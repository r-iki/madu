from django.db import models
from django.utils.timezone import now
from sensors.models import SpectralReading
import numpy as np
import os
from django.conf import settings
import pickle
import logging
from ml.model_storage import ModelStorageManager

# Try to import joblib, with a fallback
try:
    import joblib
except ImportError:
    # Create a simple fallback for joblib
    print("WARNING: joblib not found. Using pickle as fallback for model loading.")
    class JobLibFallback:
        @staticmethod
        def load(file_path):
            if hasattr(file_path, 'read'):  # It's a file-like object
                return pickle.load(file_path)
            else:  # It's a path
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
        
        @staticmethod
        def dump(obj, file_path):
            with open(file_path, 'wb') as f:
                pickle.dump(obj, f)
    
    joblib = JobLibFallback()

# Initialize model storage manager for both local and R2 storage
model_storage = ModelStorageManager()

# For backward compatibility
MODEL_DIR = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
os.makedirs(MODEL_DIR, exist_ok=True)

class MLModel(models.Model):
    """Model to store information about trained ML models"""
    MODEL_TYPES = (
        ('ANN', 'Artificial Neural Network'),
        ('RF', 'Random Forest'),
        ('SVM', 'Support Vector Machine'),
    )
    
    name = models.CharField(max_length=100)
    model_type = models.CharField(max_length=3, choices=MODEL_TYPES)
    accuracy = models.FloatField(default=0.0)
    precision = models.FloatField(default=0.0)
    recall = models.FloatField(default=0.0)
    f1_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(default=now)
    updated_at = models.DateTimeField(auto_now=True)
    parameters = models.JSONField(default=dict)
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.model_type})"
    
    class Meta:
        ordering = ['-updated_at']
        
class MLTestData(models.Model):
    """Model to store test data for ML predictions"""
    spectral_reading = models.ForeignKey(SpectralReading, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=now)
    notes = models.TextField(blank=True, null=True)
    
    # ML prediction results
    ann_prediction = models.CharField(max_length=100, blank=True, null=True)
    rf_prediction = models.CharField(max_length=100, blank=True, null=True)
    svm_prediction = models.CharField(max_length=100, blank=True, null=True)
    
    # Confidence scores (stored as JSON string)
    ann_confidence = models.JSONField(default=dict)
    rf_confidence = models.JSONField(default=dict) 
    svm_confidence = models.JSONField(default=dict)
    
    test_name = models.CharField(max_length=100, default="Test ML")
    
    def __str__(self):
        return f"ML Test {self.id}: {self.test_name}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "ML Test Data"
        verbose_name_plural = "ML Test Data"


class MLModelManager:
    """Manager class for handling ML models"""
    def __init__(self):
        self.models = {
            'ANN': None,
            'RF': None,
            'SVM': None
        }
        self.scaler = None
        self.label_encoder = None
        self.feature_names = [
            'uv_410', 'uv_435', 'uv_460', 'uv_485', 'uv_510', 'uv_535',
            'vis_560', 'vis_585', 'vis_645', 'vis_705', 'vis_900', 'vis_940',
            'nir_610', 'nir_680', 'nir_730', 'nir_760', 'nir_810', 'nir_860',
        ]
        
        # Try to load pre-trained models
        self._load_models()
    
    def _load_models(self):
        """Load all available models from either local storage or Cloudflare R2"""
        try:
            # Load scaler
            scaler_filename = 'scaler.pkl'
            self.scaler = model_storage.load_file(scaler_filename, joblib.load)
            
            # Load label encoder
            encoder_filename = 'label_encoder.pkl'
            self.label_encoder = model_storage.load_file(encoder_filename, joblib.load)
            
            # Load ML models
            for model_type in self.models:
                model_filename = f'{model_type.lower()}_model.pkl'
                model = model_storage.load_file(model_filename, joblib.load)
                if model is not None:
                    self.models[model_type] = model
        except Exception as e:
            print(f"Error loading ML models: {e}")
    
    def predict(self, spectral_data, model_type='all'):
        """Make predictions using the specified model or all models
        
        Args:
            spectral_data: Dictionary containing spectral data
            model_type: 'ANN', 'RF', 'SVM' or 'all'
            
        Returns:
            Dictionary with prediction results
        """
        if self.scaler is None:
            return {"error": "Scaler not loaded. Models may not be trained yet."}
        
        if model_type != 'all' and self.models[model_type] is None:
            return {"error": f"{model_type} model not loaded."}
        
        # Extract features
        features = np.array([[
            spectral_data.get(f, 0) for f in self.feature_names
        ]])
        
        # Scale features
        scaled_features = self.scaler.transform(features)
        
        results = {}
        
        if model_type == 'all':
            # Predict with all available models
            for m_type, model in self.models.items():
                if model is not None:
                    try:
                        # Get prediction
                        pred_class_idx = model.predict(scaled_features)[0]
                        
                        # Get probabilities
                        probas = model.predict_proba(scaled_features)[0]
                        
                        # Convert class index to label
                        if self.label_encoder:
                            pred_class = self.label_encoder.inverse_transform([pred_class_idx])[0]
                        else:
                            pred_class = str(pred_class_idx)
                        
                        # Format class probabilities
                        if self.label_encoder:
                            class_names = self.label_encoder.classes_
                            prob_dict = {str(name): float(prob) for name, prob in zip(class_names, probas)}
                        else:
                            prob_dict = {str(i): float(p) for i, p in enumerate(probas)}
                            
                        results[m_type] = {
                            'prediction': pred_class,
                            'confidence': prob_dict
                        }
                    except Exception as e:
                        results[m_type] = {'error': str(e)}
        else:
            # Predict with specific model
            model = self.models[model_type]
            if model is not None:
                try:
                    # Get prediction
                    pred_class_idx = model.predict(scaled_features)[0]
                    
                    # Get probabilities
                    probas = model.predict_proba(scaled_features)[0]
                    
                    # Convert class index to label
                    if self.label_encoder:
                        pred_class = self.label_encoder.inverse_transform([pred_class_idx])[0]
                    else:
                        pred_class = str(pred_class_idx)
                    
                    # Format class probabilities
                    if self.label_encoder:
                        class_names = self.label_encoder.classes_
                        prob_dict = {str(name): float(prob) for name, prob in zip(class_names, probas)}
                    else:
                        prob_dict = {str(i): float(p) for i, p in enumerate(probas)}
                        
                    results[model_type] = {
                        'prediction': pred_class,
                        'confidence': prob_dict
                    }
                except Exception as e:
                    results[model_type] = {'error': str(e)}
                    
        return results

# Create a singleton instance
ml_model_manager = MLModelManager()
