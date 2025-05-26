"""
Disease Prediction Model

This module provides functionality to predict diseases based on symptoms using the user's trained ML model.
"""
import os
import joblib
import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict, Any
from django.conf import settings
from ..models import Disease, Symptom

# Paths
MODEL_PATH = os.path.join(settings.BASE_DIR, 'Model', 'model.pkl')
SYMPTOM_CSV = os.path.join(settings.BASE_DIR, 'Data', 'symptoms_df.csv')
DESC_CSV = os.path.join(settings.BASE_DIR, 'Data', 'description.csv')
PRECAUTIONS_CSV = os.path.join(settings.BASE_DIR, 'Data', 'precautions_df.csv')
WORKOUT_CSV = os.path.join(settings.BASE_DIR, 'Data', 'workout_df.csv')
DIETS_CSV = os.path.join(settings.BASE_DIR, 'Data', 'diets.csv')
MEDICATION_CSV = os.path.join(settings.BASE_DIR, 'Data', 'medications.csv')

# Load model and data
MODEL = joblib.load(MODEL_PATH)
symptom_data = pd.read_csv(SYMPTOM_CSV)
desc_data = pd.read_csv(DESC_CSV)
precautions_data = pd.read_csv(PRECAUTIONS_CSV)
workout_data = pd.read_csv(WORKOUT_CSV)
diets_data = pd.read_csv(DIETS_CSV)
medication_data = pd.read_csv(MEDICATION_CSV)

# Build symptoms_dict and diseases_list from notebook
symptoms_dict = {symptom: idx for idx, symptom in enumerate(symptom_data.columns[1:])}
# Assume the model classes_ are in the same order as diseases_list in notebook
if hasattr(MODEL, 'classes_'):
    diseases_list = {idx: disease for idx, disease in enumerate(MODEL.classes_)}
else:
    # fallback: use notebook mapping or raise error
    diseases_list = {}


def predict_disease(symptom_names: List[str]) -> Tuple[str, float]:
    """
    Predict the most likely disease based on the given symptoms.
    Returns (disease_name, confidence)
    """
    input_vector = [0] * len(symptoms_dict)
    for symptom in symptom_names:
        idx = symptoms_dict.get(symptom)
        if idx is not None:
            input_vector[idx] = 1
    prediction = MODEL.predict([input_vector])[0]
    # If model outputs index, map to name; if outputs string, use directly
    disease_name = diseases_list[prediction] if prediction in diseases_list else str(prediction)
    # Confidence: use predict_proba if available
    if hasattr(MODEL, 'predict_proba'):
        proba = MODEL.predict_proba([input_vector])[0]
        confidence = max(proba)
    else:
        confidence = 1.0  # fallback
    return disease_name, confidence


def get_recommendations(disease_name: str):
    """
    Return (description, medication, workout, diet, precautions) for the given disease_name
    """
    desc = desc_data[desc_data["Disease"] == disease_name]["Description"].values
    desc = desc[0] if len(desc) else "No description available"
    meds = medication_data[medication_data['Disease'] == disease_name]['Medication'].values
    med = meds[0] if len(meds) else "No medication available"
    work = workout_data[workout_data['disease'] == disease_name]['workout'].values
    diet = diets_data[diets_data['Disease'] == disease_name]['Diet'].values
    diet = diet[0] if len(diet) else "No diet available"
    prec = precautions_data[precautions_data['Disease'] == disease_name].values
    precautions = prec[0][2:] if len(prec) else []
    return desc, med, work, diet, precautions

def load_symptom_index():
    """
    Create a symptom index based on the model's feature names.
    This should match the features used during training.
    """
    global SYMPTOM_INDEX
    
    # This should match the symptoms used during training
    # You may need to adjust this based on your actual model's features
    symptoms = [
        'itching', 'skin_rash', 'nodal_skin_eruptions', 'continuous_sneezing',
        'shivering', 'chills', 'joint_pain', 'stomach_pain', 'acidity',
        'ulcers_on_tongue', 'muscle_wasting', 'vomiting', 'burning_micturition',
        'spotting_urination', 'fatigue', 'weight_gain', 'anxiety',
        'cold_hands_and_feets', 'mood_swings', 'weight_loss', 'restlessness',
        'lethargy', 'patches_in_throat', 'irregular_sugar_level', 'cough',
        'high_fever', 'sunken_eyes', 'breathlessness', 'sweating', 'dehydration',
        'indigestion', 'headache', 'yellowish_skin', 'dark_urine', 'nausea',
        'loss_of_appetite', 'pain_behind_the_eyes', 'back_pain', 'constipation',
        'abdominal_pain', 'diarrhoea', 'mild_fever', 'yellow_urine',
        'yellowing_of_eyes', 'acute_liver_failure', 'fluid_overload',
        'swelling_of_stomach', 'swelled_lymph_nodes', 'malaise',
        'blurred_and_distorted_vision', 'phlegm', 'throat_irritation',
        'redness_of_eyes', 'sinus_pressure', 'runny_nose', 'congestion',
        'chest_pain', 'weakness_in_limbs', 'fast_heart_rate',
        'pain_during_bowel_movements', 'pain_in_anal_region', 'bloody_stool',
        'irritation_in_anus', 'neck_pain', 'dizziness', 'cramps', 'bruising',
        'obesity', 'swollen_legs', 'swollen_blood_vessels', 'puffy_face_and_eyes',
        'enlarged_thyroid', 'brittle_nails', 'swollen_extremeties',
        'excessive_hunger', 'extra_marital_contacts', 'drying_and_tingling_lips',
        'slurred_speech', 'knee_pain', 'hip_joint_pain', 'muscle_weakness',
        'stiff_neck', 'swelling_joints', 'movement_stiffness', 'spinning_movements',
        'loss_of_balance', 'unsteadiness', 'weakness_of_one_body_side',
        'loss_of_smell', 'bladder_discomfort', 'foul_smell_of_urine',
        'continuous_feel_of_urine', 'passage_of_gases', 'internal_itching',
        'toxic_look_(typhos)', 'depression', 'irritability', 'muscle_pain',
        'altered_sensorium', 'red_spots_over_body', 'belly_pain',
        'abnormal_menstruation', 'dischromic _patches', 'watering_from_eyes',
        'increased_appetite', 'polyuria', 'family_history', 'mucoid_sputum',
        'rusty_sputum', 'lack_of_concentration', 'visual_disturbances',
        'receiving_blood_transfusion', 'receiving_unsterile_injections', 'coma',
        'stomach_bleeding', 'distention_of_abdomen', 'history_of_alcohol_consumption',
        'fluid_overload', 'blood_in_sputum', 'prominent_veins_on_calf',
        'palpitations', 'painful_walking', 'pus_filled_pimples', 'blackheads',
        'scurring', 'skin_peeling', 'silver_like_dusting', 'small_dents_in_nails',
        'inflammatory_nails', 'blister', 'red_sore_around_nose',
        'yellow_crust_ooze'
    ]
    
    SYMPTOM_INDEX = {symptom: idx for idx, symptom in enumerate(symptoms)}

def load_model():
    """Load the trained model."""
    global MODEL, SYMPTOM_INDEX
    
    try:
        MODEL = joblib.load(MODEL_PATH)
        # Initialize symptom index if not already done
        if SYMPTOM_INDEX is None:
            load_symptom_index()
    except Exception as e:
        print(f"Error loading model: {e}")
        MODEL = None

# Load the model when the module is imported
load_model()

def predict_disease(symptoms: List[str], age: int = None, gender: str = None, 
                   medical_history: str = '') -> Tuple[Optional[Disease], float]:
    """
    Predict the most likely disease based on the given symptoms.
    
    Args:
        symptoms: List of symptom names that the user is experiencing
        age: Age of the user (optional)
        gender: Gender of the user ('M', 'F', 'O', 'N') (optional)
        medical_history: Text containing the user's medical history (optional)
    
    Returns:
        A tuple containing:
        - The predicted Disease object (or None if no match found)
        - A confidence score between 0 and 1
    """
    if not MODEL or not SYMPTOM_INDEX:
        return _fallback_prediction(symptoms, age, gender, medical_history)
    
    if not symptoms:
        return None, 0.0
    
    try:
        # Convert symptoms to model input format (one-hot encoded)
        input_vector = np.zeros(len(SYMPTOM_INDEX))
        
        for symptom in symptoms:
            symptom_name = symptom.lower().replace(' ', '_')
            if symptom_name in SYMPTOM_INDEX:
                input_vector[SYMPTOM_INDEX[symptom_name]] = 1
        
        # Reshape for the model (1 sample, n_features)
        input_vector = input_vector.reshape(1, -1)
        
        # Make prediction
        predicted_class = MODEL.predict(input_vector)[0]
        confidence = max(MODEL.predict_proba(input_vector)[0])
        
        # Get the disease object from the database
        try:
            # Try to match the predicted class with a disease in the database
            # This assumes the class names in the model match disease names in the database
            disease = Disease.objects.get(
                Q(name__iexact=predicted_class) |
                Q(name__icontains=predicted_class) |
                Q(description__icontains=predicted_class)
            )
            return disease, float(confidence)
        except (Disease.DoesNotExist, Disease.MultipleObjectsReturned):
            # Fall back to the first matching disease if exact match not found
            return _fallback_prediction(symptoms, age, gender, medical_history)
            
    except Exception as e:
        print(f"Error in predict_disease: {e}")
        return _fallback_prediction(symptoms, age, gender, medical_history)

def _fallback_prediction(symptoms: List[str], age: int = None, 
                        gender: str = None, medical_history: str = '') -> Tuple[Optional[Disease], float]:
    """
    Fallback prediction method if the ML model fails or is not available.
    Uses a simple rule-based approach.
    """
    if not symptoms:
        return None, 0.0
    
    # Get all diseases that have at least one of the given symptoms
    diseases = Disease.objects.filter(symptoms__name__in=symptoms).distinct()
    
    if not diseases.exists():
        return None, 0.0
    
    best_disease = None
    best_score = 0.0
    
    for disease in diseases:
        # Get all symptoms for this disease
        disease_symptoms = set(symptom.name.lower() for symptom in disease.symptoms.all())
        user_symptoms = set(s.lower() for s in symptoms)
        
        # Calculate score based on symptom overlap
        common_symptoms = disease_symptoms.intersection(user_symptoms)
        score = len(common_symptoms) / len(disease_symptoms) if disease_symptoms else 0
        
        # Apply some adjustments based on age and gender if available
        if age is not None:
            # Example: Some diseases are more common in certain age groups
            if disease.name.lower() in ['chickenpox', 'measles'] and age < 18:
                score *= 1.2
            elif disease.name.lower() in ['hypertension', 'diabetes type 2'] and age > 40:
                score *= 1.2
        
        if gender is not None:
            # Example: Some diseases are more common in certain genders
            if gender.upper() == 'F' and disease.name.lower() in ['migraine', 'urinary tract infection']:
                score *= 1.1
            elif gender.upper() == 'M' and disease.name.lower() in ['gout', 'prostate cancer']:
                score *= 1.1
        
        # Update best match
        if score > best_score:
            best_score = score
            best_disease = disease
    
    # Cap confidence for fallback predictions
    confidence = min(0.9, best_score * 0.8)  # Reduce confidence for fallback
    return best_disease, confidence


def get_common_diseases(limit: int = 5) -> list:
    """
    Get a list of the most commonly predicted diseases.
    
    Args:
        limit: Maximum number of diseases to return
        
    Returns:
        List of dictionaries containing disease information
    """
    diseases = Disease.objects.annotate(
        prediction_count=Count('predictions')
    ).order_by('-prediction_count')[:limit]
    
    return [
        {
            'id': disease.id,
            'name': disease.name,
            'prediction_count': disease.prediction_count,
            'severity': disease.get_severity_display(),
        }
        for disease in diseases
    ]


def get_common_symptoms(limit: int = 10) -> list:
    """
    Get a list of the most commonly reported symptoms.
    
    Args:
        limit: Maximum number of symptoms to return
        
    Returns:
        List of dictionaries containing symptom information
    """
    symptoms = Symptom.objects.annotate(
        prediction_count=Count('predictions')
    ).order_by('-prediction_count')[:limit]
    
    return [
        {
            'id': symptom.id,
            'name': symptom.name,
            'prediction_count': symptom.prediction_count,
            'description': symptom.description,
        }
        for symptom in symptoms
    ]


def get_disease_statistics() -> dict:
    """
    Get statistics about diseases and predictions.
    
    Returns:
        Dictionary containing various statistics
    """
    from ..models import Disease, Prediction, PredictionFeedback
    
    stats = {
        'total_diseases': Disease.objects.count(),
        'total_symptoms': Symptom.objects.count(),
        'total_predictions': Prediction.objects.count(),
        'diseases_by_severity': {},
        'prediction_accuracy': {}
    }
    
    # Count diseases by severity
    for severity_code, severity_name in Disease.SEVERITY_CHOICES:
        count = Disease.objects.filter(severity=severity_code).count()
        stats['diseases_by_severity'][severity_name] = count
    
    # Calculate prediction accuracy based on feedback
    feedback_stats = PredictionFeedback.objects.aggregate(
        total=Count('id'),
        positive=Count('id', filter=Q(rating__gte=4)),
        neutral=Count('id', filter=Q(rating=3)),
        negative=Count('id', filter=Q(rating__lte=2))
    )
    
    total_feedback = feedback_stats.get('total', 0)
    if total_feedback > 0:
        stats['prediction_accuracy'] = {
            'positive': feedback_stats['positive'] / total_feedback * 100,
            'neutral': feedback_stats['neutral'] / total_feedback * 100,
            'negative': feedback_stats['negative'] / total_feedback * 100,
            'total': total_feedback
        }
    
    return stats
