from storages.backends.s3boto3 import S3Boto3Storage

class MLModelStorage(S3Boto3Storage):
    """
    Storage class for machine learning models using Cloudflare R2.
    """
    location = 'ml_models'  # Location for ML model files on R2
    file_overwrite = True   # Allow overwriting existing files
    custom_domain = None    # No custom domain for ML models
