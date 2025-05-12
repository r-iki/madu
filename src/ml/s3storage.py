from storages.backends.s3boto3 import S3Boto3Storage
import os
import boto3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class MLModelStorage(S3Boto3Storage):
    """
    Storage class for machine learning models using Cloudflare R2.
    """
    location = 'ml_models'  # Location for ML model files on R2
    file_overwrite = True   # Allow overwriting existing files
    custom_domain = None    # No custom domain for ML models


class S3ModelStorage:
    """Storage manager for ML models in Cloudflare R2 S3 storage"""
    
    def __init__(self):
        """Initialize the S3 model storage with Cloudflare R2 settings"""
        self.bucket_name = settings.CLOUDFLARE_R2_BUCKET
        self.base_key = 'ml_models'
        self.s3_client = self._get_s3_client()
        
    def _get_s3_client(self):
        """Create and return an S3 client for Cloudflare R2"""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
                endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
            )
        except Exception as e:
            logger.error(f"Failed to create S3 client: {e}")
            return None
            
    def list_models(self):
        """List all models in the S3 bucket"""
        try:
            if not self.s3_client:
                return []
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=f'{self.base_key}/'
            )
            
            if 'Contents' not in response:
                return []
                
            # Extract just the filenames, not the full paths
            models = []
            for obj in response['Contents']:
                key = obj['Key']
                filename = os.path.basename(key)
                if filename:  # Skip directories with empty basenames
                    models.append(filename)
            
            return models
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
            
    def upload_model(self, local_path, model_name):
        """
        Upload a model file to S3
        
        Args:
            local_path (str): Path to the local model file
            model_name (str): Name to use for the model in S3
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.s3_client:
                return False
                
            s3_key = f'{self.base_key}/{model_name}'
            
            with open(local_path, 'rb') as file_data:
                self.s3_client.upload_fileobj(
                    file_data,
                    self.bucket_name,
                    s3_key,
                    ExtraArgs={'ContentType': 'application/octet-stream'}
                )
                
            # Verify upload
            try:
                self.s3_client.head_object(
                    Bucket=self.bucket_name,
                    Key=s3_key
                )
                return True
            except Exception as e:
                logger.error(f"Upload verification failed for {model_name}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading model {model_name}: {e}")
            return False
            
    def download_model(self, model_name, local_path):
        """
        Download a model file from S3
        
        Args:
            model_name (str): Name of the model in S3
            local_path (str): Path where to save the model locally
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.s3_client:
                return False
                
            # Ensure the directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            s3_key = f'{self.base_key}/{model_name}'
            
            self.s3_client.download_file(
                self.bucket_name,
                s3_key,
                local_path
            )
            
            return os.path.exists(local_path)
            
        except Exception as e:
            logger.error(f"Error downloading model {model_name}: {e}")
            return False
