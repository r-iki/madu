#!/usr/bin/env python
"""
Test script to verify ML model loading directly from cloud storage
without downloading to local storage first.
"""
import os
import sys
import django
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Force cloud-only mode for ML models
os.environ['ML_CLOUD_ONLY'] = 'true'

django.setup()

from django.conf import settings
from ml.model_storage import ModelStorageManager
from ml.models import MLModelManager

def test_cloud_only_mode():
    """Test ML model loading directly from cloud storage without local download"""
    print("=" * 80)
    print("CLOUD-ONLY MODE TEST: Testing direct loading of ML models from cloud storage")
    print("=" * 80)
    
    # Initialize the ML model storage manager
    model_storage = ModelStorageManager()
    
    # Verify cloud-only mode is enabled
    if not hasattr(model_storage, 'cloud_only') or not model_storage.cloud_only:
        print("❌ Cloud-only mode is not enabled")
        return False
    
    print("✅ Cloud-only mode is enabled")
    
    # Make sure R2 settings are available
    if not model_storage.use_r2 or not model_storage.s3_client:
        print("❌ Cloud storage settings not configured correctly")
        return False
    
    print(f"✅ Cloud storage settings configured correctly - using bucket: {model_storage.bucket_name}")
    
    # Try loading a model directly from cloud
    print("\nTesting model loading directly from cloud...")
    
    # Initialize MLModelManager which will use our storage
    try:
        ml_model = MLModelManager()
        
        # Check if scaler model was loaded
        if ml_model.scaler is None:
            print("❌ Scaler not loaded from cloud!")
            return False
        print("✅ Scaler successfully loaded from cloud")
        
        # Check label encoder
        if ml_model.label_encoder is None:
            print("❌ Label encoder not loaded from cloud!")
            return False
        print("✅ Label encoder successfully loaded from cloud")
        
        # Check prediction models
        loaded_models = []
        failed_models = []
        
        for model_type, model in ml_model.models.items():
            if model is not None:
                loaded_models.append(model_type)
                print(f"✅ {model_type} model loaded successfully from cloud")
            else:
                failed_models.append(model_type)
                print(f"❌ {model_type} model not loaded from cloud")
        
        if failed_models:
            print(f"❌ Failed to load {len(failed_models)} models from cloud: {', '.join(failed_models)}")
            return False
            
        print("\nAll models were successfully loaded directly from cloud storage without local files!")
        return True
        
    except Exception as e:
        print(f"❌ Error during model loading: {e}")
        return False

if __name__ == "__main__":
    result = test_cloud_only_mode()
    print("=" * 80)
    if result:
        print("✅ TEST RESULT: SUCCESS - ML models can be loaded directly from cloud storage")
    else:
        print("❌ TEST RESULT: FAILURE - There are issues with cloud-only model loading")
    print("=" * 80)
    sys.exit(0 if result else 1)
