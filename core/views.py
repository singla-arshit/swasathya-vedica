import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from django.utils import timezone
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Profile, Symptom, Disease, Prediction, PredictionFeedback, Medicine, DiseaseMedicine, DietPlan
from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm, 
    PredictionForm, FeedbackForm, SymptomForm, DiseaseForm, 
    MedicineForm, DietPlanForm
)
from .predictor import predict_disease


def home(request):
    """Render the home page with featured content."""
    # Get top 5 most common symptoms
    common_symptoms = Symptom.objects.annotate(
        num_predictions=Count('predictions')
    ).filter(num_predictions__gt=0).order_by('-num_predictions')[:5]
    
    # Get top 5 most predicted diseases
    common_diseases = Disease.objects.annotate(
        num_predictions=Count('prediction__predicted_disease', distinct=True)
    ).filter(num_predictions__gt=0).order_by('-num_predictions')[:5]
    
    context = {
        'title': 'Home',
        'common_symptoms': common_symptoms,
        'common_diseases': common_diseases,
    }
    return render(request, 'home.html', context)


def about(request):
    """Render the about page."""
    context = {
        'title': 'About Us',
    }
    return render(request, 'about.html', context)


def contact(request):
    """Render the contact page."""
    context = {
        'title': 'Contact Us',
    }
    return render(request, 'contact.html', context)


def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created for {user.username}! You are now logged in.')
            return redirect('core:home')
    else:
        form = UserRegisterForm()
    
    context = {
        'title': 'Register',
        'form': form,
    }
    return render(request, 'registration/register_new.html', context)


@login_required
def profile(request):
    """Display and update user profile."""
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    # Get user's recent predictions
    recent_predictions = Prediction.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'title': 'My Profile',
        'u_form': u_form,
        'p_form': p_form,
        'recent_predictions': recent_predictions,
    }
    return render(request, 'profile.html', context)


@login_required
def change_password(request):
    """Handle password change."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'title': 'Change Password',
        'form': form,
    }
    return render(request, 'change_password.html', context)


@login_required
def predict_disease_view(request):
    """Handle disease prediction form and display results."""
    if request.method == 'POST':
        # Check if we're receiving raw symptom names from JavaScript
        if request.POST.getlist('symptoms') and not request.POST.get('symptoms_0'):
            # Get symptom names directly from POST data
            raw_symptom_names = request.POST.getlist('symptoms')
            
            # Get or create Symptom objects
            selected_symptoms = []
            symptom_names = []
            symptom_display_names = []
            
            for symptom_name in raw_symptom_names:
                # Format the symptom name for display
                display_name = ' '.join(word.capitalize() for word in symptom_name.split('_'))
                symptom_display_names.append(display_name)
                
                # Use the raw symptom name for prediction
                symptom_names.append(symptom_name)
                
                # Get or create the Symptom object
                symptom, created = Symptom.objects.get_or_create(name=display_name)
                selected_symptoms.append(symptom)
            
            # Handle empty symptom list
            if not symptom_names:
                messages.error(request, 'Please select at least one symptom')
                return redirect('predict')
                
            # Get prediction using the model
            try:
                prediction_result = predict_disease(symptom_names)
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
                return redirect('predict')
        else:
            # Process the form normally
            form = PredictionForm(request.POST)
            if not form.is_valid():
                return render(request, 'predict.html', {'form': form, 'title': 'Predict Health Condition'})
                
            # Get selected symptoms
            selected_symptoms = form.cleaned_data.get('symptoms')
            
            # Handle empty symptom list
            if not selected_symptoms:
                messages.error(request, 'Please select at least one symptom')
                return redirect('predict')
            
            # Convert symptom queryset to list of symptom names
            symptom_names = [symptom.name.lower() for symptom in selected_symptoms]
            symptom_display_names = [symptom.name for symptom in selected_symptoms]
            
            # Get prediction using the model
            try:
                prediction_result = predict_disease(symptom_names)
            except Exception as e:
                messages.error(request, f'An error occurred: {str(e)}')
                return redirect('predict')
        
        # Check for prediction errors
        if 'error' in prediction_result:
            messages.error(request, f'Prediction error: {prediction_result["error"]}')
            return redirect('predict')
        
        # Get or create disease
        disease, created = Disease.objects.get_or_create(
            name=prediction_result['disease'],
            defaults={
                'description': prediction_result.get('description', 'No description available'),
                'prevention': '\n'.join(prediction_result.get('precautions', [])),
                'severity': 'M'  # Default to Medium severity
            }
        )
        
        # Create prediction record
        prediction = Prediction.objects.create(
            user=request.user,
            predicted_disease=disease,
            confidence=0.95,  # Placeholder confidence
            notes=request.POST.get('notes', '')
        )
        
        # Add symptoms to prediction
        prediction.symptoms.set(selected_symptoms)
        
        # Prepare context for the template
        context = {
            'title': 'Prediction Result',
            'disease': prediction_result['disease'],
            'confidence': 95,  # Using placeholder confidence
            'description': prediction_result.get('description', 'No description available'),
            'symptoms': symptom_display_names,
            'prediction_id': prediction.id,
            # Recommendations
            'precautions': prediction_result.get('precautions', []),
            'medication': prediction_result.get('medication', ''),
            'workout': prediction_result.get('workout', []),
            'diet': prediction_result.get('diet', '')
        }
        
        return render(request, 'prediction_result.html', context)
    else:
        form = PredictionForm()
    
    context = {
        'title': 'Predict Health Condition',
        'form': form,
    }
    return render(request, 'predict.html', context)


@login_required
def prediction_history(request):
    """Display user's prediction history."""
    # Prefetch related data to avoid N+1 queries
    predictions_list = Prediction.objects.filter(user=request.user)\
        .select_related('predicted_disease')\
        .prefetch_related('symptoms')\
        .order_by('-created_at')
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(predictions_list, 10)  # Show 10 predictions per page
    
    try:
        predictions = paginator.page(page)
    except PageNotAnInteger:
        predictions = paginator.page(1)
    except EmptyPage:
        predictions = paginator.page(paginator.num_pages)
    
    context = {
        'title': 'Prediction History',
        'predictions': predictions,
    }
    return render(request, 'history.html', context)


@login_required
def prediction_detail(request, pk):
    """Display details of a specific prediction."""
    prediction = get_object_or_404(Prediction, pk=pk, user=request.user)
    
    # Get recommended medicines and diet plan
    medicines = []
    diet_plan = None
    
    if prediction.predicted_disease:
        # Get recommended medicines for the predicted disease
        disease_medicines = DiseaseMedicine.objects.filter(disease=prediction.predicted_disease)
        for dm in disease_medicines:
            medicines.append({
                'name': dm.medicine.name,
                'dosage': dm.dosage or 'As prescribed by doctor',
                'duration': dm.duration or 'As needed',
                'notes': dm.notes
            })
        
        # Get diet plan if available
        try:
            diet_plan = DietPlan.objects.get(disease=prediction.predicted_disease)
        except DietPlan.DoesNotExist:
            diet_plan = None
    
    # Handle feedback submission
    feedback = None
    feedback_form = None
    
    try:
        feedback = prediction.feedback
    except PredictionFeedback.DoesNotExist:
        if request.method == 'POST':
            feedback_form = FeedbackForm(request.POST)
            if feedback_form.is_valid():
                feedback = feedback_form.save(commit=False)
                feedback.prediction = prediction
                feedback.save()
                messages.success(request, 'Thank you for your feedback!')
                return redirect('prediction_detail', pk=prediction.pk)
        else:
            feedback_form = FeedbackForm()
    
    context = {
        'title': f'Prediction #{prediction.id}',
        'prediction': prediction,
        'medicines': medicines,
        'diet_plan': diet_plan,
        'feedback': feedback,
        'feedback_form': feedback_form
    }
    return render(request, 'prediction_detail.html', context)


@login_required
def delete_prediction(request, pk):
    """Delete a prediction."""
    prediction = get_object_or_404(Prediction, pk=pk, user=request.user)
    
    if request.method == 'POST':
        prediction.delete()
        messages.success(request, 'Prediction deleted successfully.')
        return redirect('core:prediction_history')
    
    context = {
        'title': 'Delete Prediction',
        'prediction': prediction,
    }
    return render(request, 'prediction_confirm_delete.html', context)


@login_required
def export_prediction_pdf(request, pk):
    """Export prediction details as PDF."""
    prediction = get_object_or_404(Prediction, pk=pk)
    
    # Check if the user has permission to view this prediction
    if prediction.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("You don't have permission to export this prediction.")
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    # Prepare styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create a list to hold the PDF elements
    elements = []
    
    # Add title and date
    elements.append(Paragraph("Health Prediction Report", title_style))
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Add prediction details
    elements.append(Paragraph("Prediction Details", heading_style))
    
    # Create a table for prediction details
    prediction_data = [
        ["Date:", prediction.prediction_date.strftime('%Y-%m-%d %H:%M')],
        ["Predicted Disease:", str(prediction.predicted_disease)],
        ["Confidence:", f"{prediction.confidence}%"]
    ]
    
    if hasattr(prediction, 'actual_disease') and prediction.actual_disease:
        prediction_data.append(["Actual Diagnosis:", str(prediction.actual_disease)])
    
    prediction_table = Table(prediction_data, colWidths=[2*inch, 4*inch])
    prediction_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ]))
    
    elements.append(prediction_table)
    elements.append(Spacer(1, 12))
    
    # Add symptoms
    elements.append(Paragraph("Reported Symptoms", heading_style))
    symptoms = [symptom.name for symptom in prediction.symptoms.all()]
    symptoms_text = ", ".join(symptoms)
    elements.append(Paragraph(symptoms_text, normal_style))
    elements.append(Spacer(1, 12))
    
    # Add disease description if available
    if hasattr(prediction.predicted_disease, 'description') and prediction.predicted_disease.description:
        elements.append(Paragraph("Description", heading_style))
        elements.append(Paragraph(prediction.predicted_disease.description, normal_style))
        elements.append(Spacer(1, 12))
    
    # Add prevention measures if available
    if hasattr(prediction.predicted_disease, 'prevention') and prediction.predicted_disease.prevention:
        elements.append(Paragraph("Prevention", heading_style))
        elements.append(Paragraph(prediction.predicted_disease.prevention, normal_style))
    
    # Build the PDF document
    doc.build(elements)
    
    # File response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="health_prediction_{prediction.id}.pdf"'
    
    return response


@login_required
def prediction_history_pdf(request):
    """Export prediction history as PDF."""
    predictions = Prediction.objects.filter(user=request.user).order_by('-created_at')
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                          rightMargin=72, leftMargin=72,
                          topMargin=72, bottomMargin=72)
    
    # Prepare styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    heading_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Create a list to hold the PDF elements
    elements = []
    
    # Add title and date
    elements.append(Paragraph("Health Prediction History", title_style))
    elements.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M')}", normal_style))
    elements.append(Spacer(1, 12))
    
    # Create a table for prediction history
    prediction_data = [['Date', 'Predicted Disease', 'Confidence']]  # Header row
    for prediction in predictions:
        prediction_data.append([
            prediction.created_at.strftime('%Y-%m-%d %H:%M'),
            str(prediction.predicted_disease) if prediction.predicted_disease else 'N/A',
            f"{prediction.confidence:.2f}%" if prediction.confidence is not None else 'N/A'
        ])
    
    # Create table with data
    prediction_table = Table(prediction_data, colWidths=[2*inch, 3.5*inch, 1.5*inch])
    
    # Define table style
    table_style = [
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#343a40')),  # Dark header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # White text for header
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]
    
    # Add alternating row colors
    for i in range(1, len(prediction_data)):
        if i % 2 == 0:
            table_style.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa')))
    
    prediction_table.setStyle(TableStyle(table_style))
    
    elements.append(prediction_table)
    
    # Build the PDF document
    doc.build(elements)
    
    # File response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="health_prediction_history.pdf"'
    
    return response


@login_required
def autocomplete_symptoms(request):
    """Provide autocomplete suggestions for symptoms."""
    query = request.GET.get('term', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)
        
    symptoms = Symptom.objects.filter(name__icontains=query)[:10]
    results = [symptom.name for symptom in symptoms]
    return JsonResponse(results, safe=False)


@login_required
@require_http_methods(["POST"])
@csrf_exempt  # In production, use proper CSRF handling with AJAX
def save_prediction_feedback(request, pk):
    """Handle AJAX request to save prediction feedback."""
    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponseForbidden('Invalid request')
    
    prediction = get_object_or_404(Prediction, pk=pk, user=request.user)
    
    try:
        data = json.loads(request.body)
        rating = int(data.get('rating'))
        comments = data.get('comments', '')
        actual_diagnosis = data.get('actual_diagnosis', '')
        
        # Validate rating
        if not 1 <= rating <= 5:
            return JsonResponse({'error': 'Invalid rating'}, status=400)
        
        # Create or update feedback
        feedback, created = PredictionFeedback.objects.update_or_create(
            prediction=prediction,
            defaults={
                'rating': rating,
                'comments': comments,
                'actual_diagnosis': actual_diagnosis
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Feedback saved successfully',
            'feedback_id': feedback.id
        })
    except (ValueError, KeyError) as e:
        return JsonResponse({'error': str(e)}, status=400)
    except Exception as e:
        return JsonResponse({'error': 'An error occurred'}, status=500)


# Admin-only views for managing the knowledge base
@login_required
def manage_symptoms(request):
    """View and manage symptoms in the knowledge base (admin only)."""
    if not request.user.is_staff:
        return redirect('home')
    
    symptoms = Symptom.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = SymptomForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Symptom added successfully.')
            return redirect('manage_symptoms')
    else:
        form = SymptomForm()
    
    context = {
        'title': 'Manage Symptoms',
        'symptoms': symptoms,
        'form': form,
    }
    return render(request, 'admin/manage_symptoms.html', context)


@login_required
def manage_diseases(request):
    """View and manage diseases in the knowledge base (admin only)."""
    if not request.user.is_staff:
        return redirect('home')
    
    diseases = Disease.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = DiseaseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Disease added successfully.')
            return redirect('manage_diseases')
    else:
        form = DiseaseForm()
    
    context = {
        'title': 'Manage Diseases',
        'diseases': diseases,
        'form': form,
    }
    return render(request, 'admin/manage_diseases.html', context)


@login_required
def manage_medicines(request):
    """View and manage medicines in the knowledge base (admin only)."""
    if not request.user.is_staff:
        return redirect('home')
    
    medicines = Medicine.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Medicine added successfully.')
            return redirect('manage_medicines')
    else:
        form = MedicineForm()
    
    context = {
        'title': 'Manage Medicines',
        'medicines': medicines,
        'form': form,
    }
    return render(request, 'admin/manage_medicines.html', context)


@login_required
def manage_diet_plans(request):
    """View and manage diet plans in the knowledge base (admin only)."""
    if not request.user.is_staff:
        return redirect('home')
    
    diet_plans = DietPlan.objects.all().order_by('disease__name')
    
    if request.method == 'POST':
        form = DietPlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Diet plan added successfully.')
            return redirect('manage_diet_plans')
    else:
        form = DietPlanForm()
    
    context = {
        'title': 'Manage Diet Plans',
        'diet_plans': diet_plans,
        'form': form,
    }
    return render(request, 'admin/manage_diet_plans.html', context)


# API Views
@login_required
def api_get_disease_details(request, disease_id):
    """API endpoint to get disease details by ID."""
    try:
        disease = Disease.objects.get(pk=disease_id)
        data = {
            'id': disease.id,
            'name': disease.name,
            'description': disease.description,
            'severity': disease.get_severity_display(),
            'prevention': disease.prevention,
            'symptoms': [s.name for s in disease.symptoms.all()]
        }
        return JsonResponse(data)
    except Disease.DoesNotExist:
        return JsonResponse({'error': 'Disease not found'}, status=404)


@login_required
def api_search_diseases(request):
    """API endpoint to search diseases by symptoms."""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'error': 'No search query provided'}, status=400)
    
    # Search for symptoms matching the query
    symptoms = Symptom.objects.filter(name__icontains=query)
    
    # Find diseases associated with these symptoms
    diseases = Disease.objects.filter(symptoms__in=symptoms).distinct()
    
    # Prepare response data
    results = []
    for disease in diseases:
        results.append({
            'id': disease.id,
            'name': disease.name,
            'severity': disease.get_severity_display(),
            'matching_symptoms': [s.name for s in disease.symptoms.filter(name__icontains=query)]
        })
    
    return JsonResponse({'results': results})
