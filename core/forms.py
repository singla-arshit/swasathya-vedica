from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Profile, Symptom, Disease, PredictionFeedback, Medicine, DietPlan


class UserRegisterForm(UserCreationForm):
    """Form for user registration with additional fields."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class UserUpdateForm(UserChangeForm):
    """Form for updating user information."""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the password field
        self.fields.pop('password', None)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating profile information."""
    class Meta:
        model = Profile
        fields = ['image', 'bio', 'date_of_birth', 'gender', 'blood_group', 
                 'phone_number', 'address', 'city', 'country', 'postal_code']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'image':
                field.widget.attrs.update({'class': 'form-control'})


class PredictionForm(forms.Form):
    """Form for disease prediction."""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    symptoms = forms.ModelMultipleChoiceField(
        queryset=Symptom.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2-multiple',
            'data-placeholder': 'Select symptoms...',
            'multiple': 'multiple',
        }),
        help_text='Select all symptoms you are experiencing.'
    )
    
    age = forms.IntegerField(
        min_value=0,
        max_value=120,
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your age (optional)'
        }),
        help_text='Your age can help improve prediction accuracy.'
    )
    
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        help_text='Your gender (optional) can help improve prediction accuracy.'
    )
    
    medical_history = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any relevant medical history, allergies, or additional information...'
        }),
        help_text='Optional: Any additional information that might help with the prediction.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit symptom choices to active symptoms if needed
        # self.fields['symptoms'].queryset = Symptom.objects.filter(is_active=True)

        
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'symptoms':
                field.widget.attrs.update({'class': 'form-control'})


class FeedbackForm(forms.ModelForm):
    """Form for providing feedback on predictions."""
    RATING_CHOICES = [
        (5, 'Very Accurate'),
        (4, 'Somewhat Accurate'),
        (3, 'Neutral'),
        (2, 'Somewhat Inaccurate'),
        (1, 'Very Inaccurate'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'form-check-input',
        }),
        required=True,
        help_text='How accurate was the prediction?'
    )
    
    comments = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Any additional comments about the prediction...'
        })
    )
    
    actual_diagnosis = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'If known, what was the actual diagnosis?'
        })
    )
    
    class Meta:
        model = PredictionFeedback
        fields = ['rating', 'comments', 'actual_diagnosis']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'rating':
                field.widget.attrs.update({'class': 'form-control'})


class SymptomForm(forms.ModelForm):
    """Form for adding/editing symptoms (admin only)."""
    class Meta:
        model = Symptom
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class DiseaseForm(forms.ModelForm):
    """Form for adding/editing diseases (admin only)."""
    symptoms = forms.ModelMultipleChoiceField(
        queryset=Symptom.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control select2-multiple',
            'multiple': 'multiple',
        }),
        required=False
    )
    
    class Meta:
        model = Disease
        fields = ['name', 'description', 'symptoms', 'severity', 'prevention']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'prevention': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            if field_name != 'symptoms':
                field.widget.attrs.update({'class': 'form-control'})
        
        # Set initial symptoms if editing
        if self.instance.pk:
            self.fields['symptoms'].initial = self.instance.symptoms.all()
    
    def save(self, commit=True):
        disease = super().save(commit=False)
        if commit:
            disease.save()
            self.save_m2m()
        return disease


class MedicineForm(forms.ModelForm):
    """Form for adding/editing medicines (admin only)."""
    class Meta:
        model = Medicine
        fields = ['name', 'description', 'dosage', 'side_effects']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'side_effects': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class DietPlanForm(forms.ModelForm):
    """Form for adding/editing diet plans (admin only)."""
    class Meta:
        model = DietPlan
        fields = ['disease', 'description', 'recommended_foods', 'foods_to_avoid']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'recommended_foods': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'foods_to_avoid': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
