#!/usr/bin/env python
"""
Test script to verify ML model loading directly from R2 storage in Heroku mode.
This simulates the Heroku production environment where the app loads
models directly from R2 without trying local storage first.
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
from ml.models import MLModelManager, model_storage

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

def test_heroku_mode():
    """Test ML model loading directly from R2 storage in Heroku mode"""
    # Forcibly enable R2 for testing by checking Django settings
    if not hasattr(settings, 'CLOUDFLARE_R2_BUCKET') or not settings.CLOUDFLARE_R2_BUCKET:
        # Try setting environment variables for testing
        logger.info("Setting up test R2 environment variables")
        os.environ['CLOUDFLARE_R2_BUCKET'] = os.environ.get('CLOUDFLARE_R2_BUCKET', 'test-bucket')
        os.environ['CLOUDFLARE_R2_ACCESS_KEY'] = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY', 'test-key')
        os.environ['CLOUDFLARE_R2_SECRET_KEY'] = os.environ.get('CLOUDFLARE_R2_SECRET_KEY', 'test-secret')
        os.environ['CLOUDFLARE_R2_BUCKET_ENDPOINT'] = os.environ.get('CLOUDFLARE_R2_BUCKET_ENDPOINT', 'https://test.com')
        
        # Set these directly on settings too
        settings.CLOUDFLARE_R2_BUCKET = os.environ.get('CLOUDFLARE_R2_BUCKET')
        settings.CLOUDFLARE_R2_ACCESS_KEY = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY')
        settings.CLOUDFLARE_R2_SECRET_KEY = os.environ.get('CLOUDFLARE_R2_SECRET_KEY')
        settings.CLOUDFLARE_R2_BUCKET_ENDPOINT = os.environ.get('CLOUDFLARE_R2_BUCKET_ENDPOINT')
    
    # Verify R2 settings are available
    logger.info(f"R2 bucket: {settings.CLOUDFLARE_R2_BUCKET}")
    logger.info(f"R2 endpoint: {settings.CLOUDFLARE_R2_BUCKET_ENDPOINT}")
    
    # Backup local models to simulate Heroku's ephemeral filesystem
    backed_up = backup_local_models()
    if not backed_up:
        logger.error("Failed to backup models. Test aborted.")
        return False
    
    # Set Heroku environment variables to simulate Heroku
    os.environ['DYNO'] = 'test-dyno-1'
    os.environ['FORCE_R2'] = 'true'
    
    try:
        # Reset model_storage instance to use new environment variables
        model_storage.__init__()
        
        # Verify model storage is set to prefer R2
        if not hasattr(model_storage, 'prefer_r2') or not model_storage.prefer_r2:
            logger.error("Model storage is not configured to prefer R2 storage on Heroku.")
            return False
        
        logger.info("Model storage correctly set to prefer R2 storage in Heroku mode.")
        
        # Now initialize MLModelManager, which will load models directly from R2
        logger.info("Loading models directly from R2 storage...")
        model_manager = MLModelManager()
        
        # Check if scaler model was loaded
        if model_manager.scaler is None:
            logger.error("❌ Scaler not loaded from R2!")
            return False
        logger.info("✓ Scaler successfully loaded from R2")
        
        # Check label encoder
        if model_manager.label_encoder is None:
            logger.error("❌ Label encoder not loaded from R2!")
            return False
        logger.info("✓ Label encoder successfully loaded from R2")
        
        # Check prediction models
        loaded_models = []
        failed_models = []
        
        for model_type, model in model_manager.models.items():
            if model is not None:
                loaded_models.append(model_type)
                logger.info(f"✓ {model_type} model loaded successfully from R2")
            else:
                failed_models.append(model_type)
                logger.error(f"❌ {model_type} model not loaded from R2")
        
        if failed_models:
            logger.error(f"Failed to load {len(failed_models)} models from R2: {', '.join(failed_models)}")
            return False
        
        # Test prediction
        logger.info("\nTesting prediction with models loaded from R2...")
        test_spectral_data = {
            'uv_410': 0.5, 'uv_435': 0.6, 'uv_460': 0.7, 'uv_485': 0.8, 'uv_510': 0.9, 'uv_535': 1.0,
            'vis_560': 1.1, 'vis_585': 1.2, 'vis_645': 1.3, 'vis_705': 1.4, 'vis_900': 1.5, 'vis_940': 1.6,
            'nir_610': 1.7, 'nir_680': 1.8, 'nir_730': 1.9, 'nir_760': 2.0, 'nir_810': 2.1, 'nir_860': 2.2,
        }
        
        result = model_manager.predict(test_spectral_data)
        if "error" in result:
            logger.error(f"❌ Prediction test failed: {result['error']}")
            return False
            
        logger.info("✓ Prediction successful with models loaded from R2")
        logger.info("✅ Heroku mode test PASSED: Models can be loaded directly from R2 storage!")
        
        return True
        
    finally:
        # Clean up
        restore_local_models()
        logger.info("Restored original local model files")
        
        # Remove environment variables
        if 'DYNO' in os.environ:
            del os.environ['DYNO']
        if 'FORCE_R2' in os.environ:
            del os.environ['FORCE_R2']

if __name__ == "__main__":
    print("\n" + "="*80)
    print("HEROKU MODE TEST: Testing direct loading of ML models from Cloudflare R2")
    print("="*80 + "\n")
    
    success = test_heroku_mode()
    
    print("\n" + "="*80)
    if success:
        print("✅ TEST RESULT: SUCCESS - The system can load models directly from R2")
        print("Heroku deployments will now work correctly with ML models stored in R2.")
    else:
        print("❌ TEST RESULT: FAILURE - There are issues with direct R2 model loading")
        print("The 'Scaler not loaded' error may still occur in Heroku deployment.")
    print("="*80 + "\n")
    
    sys.exit(0 if success else 1)
