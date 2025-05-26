from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Home and static pages
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        extra_context={'title': 'Login'},
        next_page='core:home'
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='core:home'), name='logout'),
    
    # Password Reset
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
             success_url='/password-reset/done/'
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/password-reset/complete/'
         ), 
         name='password_reset_confirm'),
    path('password-reset/complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # User profile
    path('profile/', views.profile, name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    # Predictions
    path('predict/', views.predict_disease_view, name='predict'),
    path('history/', views.prediction_history, name='prediction_history'),
    path('history/export-pdf/', views.prediction_history_pdf, name='export_prediction_history_pdf'),
    path('history/<int:pk>/', views.prediction_detail, name='prediction_detail'),
    path('history/<int:pk>/export-pdf/', views.export_prediction_pdf, name='export_prediction_pdf'),
    path('history/<int:pk>/delete/', views.delete_prediction, name='delete_prediction'),
    path('api/symptoms/autocomplete/', views.autocomplete_symptoms, name='autocomplete_symptoms'),
    
    # Feedback
    path('api/predictions/<int:pk>/feedback/', views.save_prediction_feedback, name='save_prediction_feedback'),
    
    # Admin management (staff only)
    path('admin/symptoms/', views.manage_symptoms, name='manage_symptoms'),
    path('admin/diseases/', views.manage_diseases, name='manage_diseases'),
    path('admin/medicines/', views.manage_medicines, name='manage_medicines'),
    path('admin/diet-plans/', views.manage_diet_plans, name='manage_diet_plans'),
    
    # API Endpoints
    path('api/diseases/<int:disease_id>/', views.api_get_disease_details, name='api_disease_details'),
    path('api/diseases/search/', views.api_search_diseases, name='api_search_diseases'),
]
