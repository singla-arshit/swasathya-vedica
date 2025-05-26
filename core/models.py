import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


def profile_image_upload_path(instance, filename):
    # Upload to: profiles/<username>/<random_uuid>.<extension>
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('profiles', instance.user.username, filename)


class Profile(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
        ('N', 'Prefer not to say'),
    ]
    
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('U', 'Unknown'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    image = models.ImageField(upload_to=profile_image_upload_path, default='profiles/default.png')
    bio = models.TextField(max_length=500, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(max_length=200, blank=True)
    city = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Symptom(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Disease(models.Model):
    SEVERITY_CHOICES = [
        ('L', 'Low'),
        ('M', 'Medium'),
        ('H', 'High'),
        ('C', 'Critical'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    symptoms = models.ManyToManyField(Symptom, related_name='diseases')
    severity = models.CharField(max_length=1, choices=SEVERITY_CHOICES, default='M')
    prevention = models.TextField(help_text="Preventive measures")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Medicine(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    dosage = models.CharField(max_length=100, blank=True)
    side_effects = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class DiseaseMedicine(models.Model):
    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='disease_medicines')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='medicine_diseases')
    dosage = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('disease', 'medicine')
    
    def __str__(self):
        return f"{self.medicine.name} for {self.disease.name}"


class DietPlan(models.Model):
    disease = models.OneToOneField(Disease, on_delete=models.CASCADE, related_name='diet_plan')
    description = models.TextField()
    recommended_foods = models.TextField()
    foods_to_avoid = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Diet Plan for {self.disease.name}"


class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    symptoms = models.ManyToManyField(Symptom, related_name='predictions')
    predicted_disease = models.ForeignKey(Disease, on_delete=models.SET_NULL, null=True, blank=True)
    confidence = models.FloatField(help_text="Prediction confidence score (0-1)")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username}'s prediction for {self.predicted_disease or 'unknown'}"
    
    @property
    def confidence_percentage(self):
        return f"{self.confidence * 100:.1f}%"


class PredictionFeedback(models.Model):
    RATING_CHOICES = [
        (1, 'Very Inaccurate'),
        (2, 'Somewhat Inaccurate'),
        (3, 'Neutral'),
        (4, 'Somewhat Accurate'),
        (5, 'Very Accurate'),
    ]
    
    prediction = models.OneToOneField(Prediction, on_delete=models.CASCADE, related_name='feedback')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comments = models.TextField(blank=True)
    actual_diagnosis = models.CharField(max_length=200, blank=True, help_text="Actual diagnosis from a healthcare provider")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Feedback for {self.prediction}"
