# ML Model Cloud Storage Documentation

## Overview

This project implements a cloud-only mode for machine learning models, where models are loaded directly from Cloudflare R2 storage without requiring local downloads. This approach is especially beneficial for deployment on platforms like Heroku with ephemeral filesystems.

## Technical Implementation

### Dependencies Required

For ML model cloud storage to work properly, the following dependencies are essential:

```
# Core ML dependencies
joblib==1.3.2
scikit-learn==1.2.2
numpy==2.2.1
pandas==2.2.3

# Cloud storage
boto3==1.36.16
botocore==1.36.16
```

These dependencies enable:
- Loading ML models with joblib/pickle
- Direct streaming from cloud storage to memory
- Interfacing with Cloudflare R2 through boto3's S3 compatibility

### How It Works

1. **Direct Model Loading**: 
   - `ModelStorageManager` uses boto3 to retrieve model files from R2
   - Models are loaded directly from memory buffers without writing to local disk
   - Uses `io.BytesIO` to provide file-like objects to joblib/pickle

2. **Environment Detection**:
   - Automatically detects Heroku environment via `DYNO` environment variable
   - Forces cloud-only mode on Heroku to prevent filesystem-related errors
   - Can be manually controlled via `ML_CLOUD_ONLY` environment variable

3. **Performance Considerations**:
   - Initial loading from cloud may be slower than local loading
   - For repeated operations, consider setting `ML_CLOUD_ONLY=false` in development

## Testing

Tests have been implemented to verify cloud-only functionality:

- `test_cloud_only_mode.py`: Tests direct loading from cloud without local caching
- `test_model_loading.py`: Tests model loading with and without local files

Run tests with:

```bash
cd src
python test_cloud_only_mode.py
```

## Troubleshooting

If experiencing issues with ML model loading:

1. Ensure Cloudflare R2 credentials are properly configured in environment variables
2. Verify models exist in R2 bucket using `verify_models.py`
3. Check application logs for specific error messages related to model loading
4. Run `test_cloud_only_mode.py` to verify cloud configuration
