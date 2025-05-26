from django.conf import settings
from .models import Symptom, Disease

def global_context(request):
    """Add global context variables to all templates."""
    context = {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_DESCRIPTION': settings.SITE_DESCRIPTION,
        'DEBUG': settings.DEBUG,
    }
    return context

def navigation_menus(request):
    """Add navigation menu items to the context."""
    menu_items = [
        {'name': 'Home', 'url': 'core:home', 'icon': 'fas fa-home'},
        {'name': 'Predict', 'url': 'core:predict', 'icon': 'fas fa-stethoscope'},
        {'name': 'History', 'url': 'core:prediction_history', 'icon': 'fas fa-history'},
        {'name': 'About', 'url': 'core:about', 'icon': 'fas fa-info-circle'},
        {'name': 'Contact', 'url': 'core:contact', 'icon': 'fas fa-envelope'},
    ]
    
    # Add admin menu items for staff users
    if request.user.is_staff:
        menu_items += [
            {'name': 'Admin', 'url': 'admin:index', 'icon': 'fas fa-cog', 'is_admin': True},
            {'name': 'Manage Symptoms', 'url': 'core:manage_symptoms', 'icon': 'fas fa-thermometer-half', 'is_admin': True},
            {'name': 'Manage Diseases', 'url': 'core:manage_diseases', 'icon': 'fas fa-disease', 'is_admin': True},
        ]
    
    # Add user menu items for authenticated users
    if request.user.is_authenticated:
        menu_items.append(
            {'name': 'Profile', 'url': 'core:profile', 'icon': 'fas fa-user'}
        )
    
    return {
        'nav_menu': menu_items,
        'current_path': request.path,
    }

def common_data(request):
    """Add common data to all templates."""
    context = {}
    
    # Only fetch these if needed (they're cached after first request)
    if 'sidebar_symptoms' not in request.session:
        request.session['sidebar_symptoms'] = list(Symptom.objects.values_list('name', flat=True)[:10])
    
    if 'sidebar_diseases' not in request.session:
        request.session['sidebar_diseases'] = list(Disease.objects.values_list('name', flat=True)[:5])
    
    context.update({
        'sidebar_symptoms': request.session.get('sidebar_symptoms', []),
        'sidebar_diseases': request.session.get('sidebar_diseases', []),
    })
    
    # Add user-specific data
    if request.user.is_authenticated:
        context.update({
            'user_notifications': [],  # You can add notification logic here
            'unread_messages': 0,      # You can add message logic here
        })
    
    return context
