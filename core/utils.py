"""
Utility functions and constants for the Health Predictor application.
"""
import os
import random
import string
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def generate_random_string(length=8):
    """Generate a random string of fixed length."""
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


def send_welcome_email(user):
    """Send a welcome email to a new user."""
    subject = f'Welcome to {settings.SITE_NAME}!'
    html_message = render_to_string('emails/welcome.html', {
        'user': user,
        'site_name': settings.SITE_NAME,
        'support_email': settings.DEFAULT_FROM_EMAIL,
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_password_reset_email(user, reset_url):
    """Send a password reset email to the user."""
    subject = f'Password Reset Request - {settings.SITE_NAME}'
    html_message = render_to_string('emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
        'expiry_hours': settings.PASSWORD_RESET_TIMEOUT // 3600,  # Convert seconds to hours
    })
    plain_message = strip_tags(html_message)
    
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def get_user_activity(user_id):
    """Get user's last activity time from cache or database."""
    from .models import Profile
    
    cache_key = f'user_activity_{user_id}'
    last_activity = cache.get(cache_key)
    
    if not last_activity:
        try:
            profile = Profile.objects.get(user_id=user_id)
            last_activity = profile.last_activity
            # Cache for 5 minutes
            cache.set(cache_key, last_activity, 300)
        except Profile.DoesNotExist:
            last_activity = None
    
    return last_activity


def is_user_online(user):
    """Check if a user is currently online (active in the last 5 minutes)."""
    if not user.is_authenticated:
        return False
    
    last_activity = get_user_activity(user.id)
    if not last_activity:
        return False
    
    now = datetime.now(last_activity.tzinfo)
    return (now - last_activity) < timedelta(minutes=5)


def get_file_extension(filename):
    """Get the file extension from a filename."""
    return os.path.splitext(filename)[1].lower()


def is_image_file(filename):
    """Check if a file is an image based on its extension."""
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    return get_file_extension(filename) in image_extensions


def format_file_size(size_in_bytes):
    """Convert file size in bytes to a human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024.0:
            return f"{size_in_bytes:.1f} {unit}"
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} PB"


def get_client_ip(request):
    """Get the client's IP address from the request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_browser_info(request):
    """Get browser information from the request."""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    browsers = {
        'chrome': 'chrome' in user_agent,
        'firefox': 'firefox' in user_agent,
        'safari': 'safari' in user_agent and 'chrome' not in user_agent,
        'edge': 'edge' in user_agent,
        'opera': 'opera' in user_agent or 'opr/' in user_agent,
        'ie': 'msie' in user_agent or 'trident/' in user_agent,
    }
    
    for browser, is_this_browser in browsers.items():
        if is_this_browser:
            return browser
    
    return 'unknown'


def get_os_info(request):
    """Get operating system information from the request."""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if 'windows' in user_agent:
        return 'Windows'
    elif 'mac' in user_agent:
        return 'macOS'
    elif 'linux' in user_agent:
        return 'Linux'
    elif 'android' in user_agent:
        return 'Android'
    elif 'iphone' in user_agent or 'ipad' in user_agent or 'ipod' in user_agent:
        return 'iOS'
    
    return 'Unknown OS'


def get_device_type(request):
    """Get the type of device making the request."""
    user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
    
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return 'Mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'Tablet'
    else:
        return 'Desktop'


def get_geolocation_info(ip_address):
    """
    Get geolocation information for an IP address.
    Note: This is a placeholder. In a real application, you would use a geolocation API.
    """
    # In a real application, you would call a geolocation API here
    # For example: https://ipapi.co/{ip_address}/json/
    return {
        'ip': ip_address,
        'city': 'Unknown',
        'region': 'Unknown',
        'country': 'Unknown',
        'timezone': 'UTC',
    }


def track_user_activity(user, request=None):
    """Track user activity and update relevant information."""
    from .models import UserActivityLog
    
    if not user.is_authenticated:
        return
    
    # Update last activity in the profile
    from .models import Profile
    Profile.objects.filter(user=user).update(last_activity=timezone.now())
    
    # Log the activity if a request is provided
    if request:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        UserActivityLog.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent[:500],  # Limit length to prevent database errors
            path=request.path,
            method=request.method,
            referrer=request.META.get('HTTP_REFERER', '')[:500],
            browser=get_browser_info(request),
            os=get_os_info(request),
            device_type=get_device_type(request),
        )


def check_password_strength(password):
    """Check the strength of a password."""
    if len(password) < 8:
        return 'weak', 'Password is too short (minimum 8 characters)'
    
    if not any(char.isdigit() for char in password):
        return 'weak', 'Password must contain at least one number'
    
    if not any(char.isupper() for char in password):
        return 'medium', 'Consider adding uppercase letters for better security'
    
    if not any(char in '!@#$%^&*()-_=+[]{}|;:,.<>?/' for char in password):
        return 'medium', 'Consider adding special characters for better security'
    
    return 'strong', 'Password is strong'
