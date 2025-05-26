from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import (
    Profile, Symptom, Disease, Medicine, DiseaseMedicine, 
    DietPlan, Prediction, PredictionFeedback
)


# Register your models here.


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_joined_date')
    list_select_related = ('profile', )
    
    def get_joined_date(self, instance):
        return instance.date_joined.strftime('%Y-%m-%d')
    get_joined_date.short_description = 'Joined'
    get_joined_date.admin_order_field = 'date_joined'


class SymptomAdmin(admin.ModelAdmin):
    list_display = ('name', 'description_preview', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
        return "-"
    description_preview.short_description = 'Description Preview'


class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'severity_display', 'symptoms_list', 'created_at')
    search_fields = ('name', 'description', 'prevention')
    list_filter = ('severity', 'created_at')
    filter_horizontal = ('symptoms',)
    readonly_fields = ('created_at', 'updated_at')
    
    def severity_display(self, obj):
        return dict(Disease.SEVERITY_CHOICES).get(obj.severity, '-')
    severity_display.short_description = 'Severity'
    
    def symptoms_list(self, obj):
        return ", ".join([s.name for s in obj.symptoms.all()[:3]])
    symptoms_list.short_description = 'Symptoms'


class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'dosage', 'created_at')
    search_fields = ('name', 'description', 'side_effects')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')


class DiseaseMedicineInline(admin.TabularInline):
    model = DiseaseMedicine
    extra = 1
    fields = ('medicine', 'dosage', 'duration', 'notes')


class DiseaseMedicineAdmin(admin.ModelAdmin):
    list_display = ('disease', 'medicine', 'dosage', 'duration')
    list_filter = ('disease', 'medicine')
    search_fields = ('disease__name', 'medicine__name', 'notes')


class DietPlanAdmin(admin.ModelAdmin):
    list_display = ('disease', 'created_at')
    search_fields = ('disease__name', 'description', 'recommended_foods', 'foods_to_avoid')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')


class PredictionFeedbackInline(admin.StackedInline):
    model = PredictionFeedback
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


class PredictionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'disease_display', 'confidence_display', 'created_at')
    list_filter = ('created_at', 'predicted_disease')
    search_fields = ('user__username', 'predicted_disease__name', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'confidence_display')
    inlines = [PredictionFeedbackInline]
    
    def disease_display(self, obj):
        if obj.predicted_disease:
            return obj.predicted_disease.name
        return "-"
    disease_display.short_description = 'Predicted Disease'
    
    def confidence_display(self, obj):
        return f"{obj.confidence:.1%}"
    confidence_display.short_description = 'Confidence'


class PredictionFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'prediction_link', 'rating_display', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('prediction__user__username', 'comments', 'actual_diagnosis')
    readonly_fields = ('created_at', 'updated_at', 'prediction_link')
    
    def prediction_link(self, obj):
        url = reverse('admin:core_prediction_change', args=[obj.prediction.id])
        return mark_safe(f'<a href="{url}">Prediction #{obj.prediction.id}</a>')
    prediction_link.short_description = 'Prediction'
    prediction_link.allow_tags = True
    
    def rating_display(self, obj):
        return dict(PredictionFeedback.RATING_CHOICES).get(obj.rating, '-')
    rating_display.short_description = 'Rating'


# Unregister the default User admin and register our custom UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Register other models
admin.site.register(Symptom, SymptomAdmin)
admin.site.register(Disease, DiseaseAdmin)
admin.site.register(Medicine, MedicineAdmin)
admin.site.register(DiseaseMedicine, DiseaseMedicineAdmin)
admin.site.register(DietPlan, DietPlanAdmin)
admin.site.register(Prediction, PredictionAdmin)
admin.site.register(PredictionFeedback, PredictionFeedbackAdmin)
