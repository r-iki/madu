#!/usr/bin/env python
"""
Test script to verify ML model loading from both local and R2 storage.
This simulates a production environment where files might not exist locally
but need to be fetched from R2.
"""
import os
import sys
import django
import shutil
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.conf import settings
from ml.model_storage import ModelStorageManager
from ml.models import MLModelManager

def backup_local_models():
    """Backup local model files to simulate Heroku's ephemeral filesystem"""
    model_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
    backup_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models_backup')
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    
    # Move all model files to backup
    logger.info(f"Backing up models from {model_dir} to {backup_dir}")
    model_files = [f for f in os.listdir(model_dir) if f.endswith('.pkl')]
    
    if not model_files:
        logger.warning("No model files found to backup!")
        return False
    
    for file in model_files:
        src = os.path.join(model_dir, file)
        dst = os.path.join(backup_dir, file)
        shutil.move(src, dst)
        logger.info(f"Moved {file} to backup")
    
    return True

def restore_local_models():
    """Restore backed up model files"""
    model_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
    backup_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models_backup')
    
    # Check if backup directory exists
    if not os.path.exists(backup_dir):
        logger.warning("No backup directory found!")
        return False
    
    # Move all files back
    logger.info(f"Restoring models from {backup_dir} to {model_dir}")
    model_files = [f for f in os.listdir(backup_dir) if f.endswith('.pkl')]
    
    for file in model_files:
        src = os.path.join(backup_dir, file)
        dst = os.path.join(model_dir, file)
        shutil.move(src, dst)
        logger.info(f"Restored {file}")
    
    # Remove backup directory
    os.rmdir(backup_dir)
    
    return True

def test_model_loading():
    """Test ML model loading from both local and R2 storage"""
    # First verify models exist locally or in R2
    logger.info("Checking initial model availability...")
    storage_manager = ModelStorageManager()
    required_models = ['scaler.pkl', 'label_encoder.pkl', 'rf_model.pkl', 'svm_model.pkl', 'ann_model.pkl']
    
    for model in required_models:
        if storage_manager.file_exists(model):
            logger.info(f"✓ Model {model} is available (local or R2)")
        else:
            logger.error(f"✗ Model {model} not found in any storage!")
            return False
    
    # Backup local models to simulate Heroku's ephemeral filesystem
    backed_up = backup_local_models()
    if not backed_up:
        logger.error("Failed to backup models. Test aborted.")
        return False
    
    try:
        # Now try to load models, which should fetch from R2
        logger.info("\nTesting model loading when local files don't exist:")
        model_manager = MLModelManager()
        
        # Check scaler
        if model_manager.scaler is None:
            logger.error("❌ Test FAILED: Scaler not loaded from R2!")
            return False
        else:
            logger.info("✓ Scaler successfully loaded from R2")
        
        # Check label encoder
        if model_manager.label_encoder is None:
            logger.error("❌ Test FAILED: Label encoder not loaded from R2!")
            return False
        else:
            logger.info("✓ Label encoder successfully loaded from R2")
        
        # Check models
        loaded_models = []
        failed_models = []
        
        for model_type, model in model_manager.models.items():
            if model is not None:
                loaded_models.append(model_type)
            else:
                failed_models.append(model_type)
        
        if loaded_models:
            logger.info(f"✓ Successfully loaded {len(loaded_models)} models from R2: {', '.join(loaded_models)}")
        
        if failed_models:
            logger.error(f"❌ Failed to load {len(failed_models)} models from R2: {', '.join(failed_models)}")
            return False
        
        # Test a prediction to see if it works
        logger.info("\nTesting prediction with loaded models:")
        test_spectral_data = {
            'uv_410': 0.5, 'uv_435': 0.6, 'uv_460': 0.7, 'uv_485': 0.8, 'uv_510': 0.9, 'uv_535': 1.0,
            'vis_560': 1.1, 'vis_585': 1.2, 'vis_645': 1.3, 'vis_705': 1.4, 'vis_900': 1.5, 'vis_940': 1.6,
            'nir_610': 1.7, 'nir_680': 1.8, 'nir_730': 1.9, 'nir_760': 2.0, 'nir_810': 2.1, 'nir_860': 2.2,
        }
        
        result = model_manager.predict(test_spectral_data)
        if "error" in result:
            logger.error(f"❌ Prediction test FAILED: {result['error']}")
            return False
        else:
            logger.info("✓ Prediction successful with loaded models")
        
        logger.info("\n✅ All tests PASSED! The model loading system is working correctly!")
        return True
        
    finally:
        # Restore the models regardless of test outcome
        restore_local_models()
        logger.info("Restored original local model files")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("HEROKU SIMULATION TEST: Testing ML model loading from R2 when local files are missing")
    print("="*80 + "\n")
    
    success = test_model_loading()
    
    print("\n" + "="*80)
    if success:
        print("✅ TEST RESULT: SUCCESS - The system can properly load models from R2")
        print("The 'Scaler not loaded' error has been resolved.")
    else:
        print("❌ TEST RESULT: FAILURE - There are still issues with model loading from R2")
    print("="*80 + "\n")
    
    sys.exit(0 if success else 1)
