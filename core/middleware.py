import time
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings


class UserActivityMiddleware:
    """
    Middleware to track user activity and update last active time.
    Also handles request timing and other common functionality.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Code to be executed for each request before the view is called
        request.start_time = time.time()
        
        # Track user activity
        if request.user.is_authenticated:
            # Update last active time in cache (update every 5 minutes)
            cache_key = f'user_activity_{request.user.id}'
            if not cache.get(cache_key):
                # Update the user's last_activity field
                from .models import Profile
                Profile.objects.filter(user=request.user).update(
                    last_activity=timezone.now()
                )
                # Cache for 5 minutes
                cache.set(cache_key, True, 300)
        
        # Process the request and get the response
        response = self.get_response(request)
        
        # Code to be executed for each request/response after the view is called
        # Calculate and add request processing time to response
        total_time = time.time() - request.start_time
        response['X-Request-Time'] = f"{total_time:.2f}s"
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response):
        """Add security-related HTTP headers to the response."""
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection in older browsers
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Prevent embedding in iframe (clickjacking protection)
        response['X-Frame-Options'] = 'DENY'
        
        # Content Security Policy
        if not settings.DEBUG:
            csp = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com https://stackpath.bootstrapcdn.com",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com",
                "img-src 'self' data: https: http:",
                "font-src 'self' https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com",
                "connect-src 'self'",
                "frame-ancestors 'none'",
            ]
            response['Content-Security-Policy'] = "; ".join(csp)


class RequestLoggingMiddleware:
    """
    Middleware to log all requests for debugging and analytics.
    In production, you might want to use a more robust solution like Django's logging framework.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log the request
        self.log_request(request)
        
        # Process the request and get the response
        response = self.get_response(request)
        
        # Log the response
        self.log_response(request, response)
        
        return response
    
    def log_request(self, request):
        """Log request details."""
        if settings.DEBUG and not request.path.startswith(settings.STATIC_URL):
            print(f"\n[REQUEST] {request.method} {request.path}")
            if request.GET:
                print(f"  GET params: {request.GET}")
            if request.POST:
                print(f"  POST data: {request.POST}")
            if request.FILES:
                print(f"  FILES: {request.FILES}")
    
    def log_response(self, request, response):
        """Log response details."""
        if settings.DEBUG and not request.path.startswith(settings.STATIC_URL):
            print(f"[RESPONSE] {request.method} {request.path} - {response.status_code}")
            if hasattr(request, 'user') and request.user.is_authenticated:
                print(f"  User: {request.user.username}")
            if hasattr(response, 'content') and len(response.content) < 1000:  # Don't log large responses
                print(f"  Content: {response.content.decode('utf-8')[:500]}...")  # Limit content length


class MaintenanceModeMiddleware:
    """
    Middleware to put the site in maintenance mode.
    Add MAINTENANCE_MODE = True to settings.py to enable.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if maintenance mode is enabled
        if getattr(settings, 'MAINTENANCE_MODE', False):
            # Allow access to admin and static files even in maintenance mode
            if not (request.path.startswith('/admin/') or 
                   request.path.startswith(settings.STATIC_URL) or
                   request.path.startswith(settings.MEDIA_URL)):
                from django.http import HttpResponse
                from django.template.loader import render_to_string
                
                # Render maintenance template
                html = render_to_string('maintenance.html')
                return HttpResponse(html, status=503, content_type='text/html')
        
        return self.get_response(request)
