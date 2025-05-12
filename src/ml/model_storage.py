"""
ML model storage manager for handling both local and Cloudflare R2 storage
"""
import os
import io
import boto3
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class ModelStorageManager:
    """
    Wrapper class for handling ML model storage in both local filesystem and Cloudflare R2
    """
    def __init__(self):
        """Initialize the model storage manager"""
        # Define local model directory
        self.local_model_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
        os.makedirs(self.local_model_dir, exist_ok=True)
        
        # Initialize with default values
        self.use_r2 = False
        self.s3_client = None
        self.bucket_name = None
        
        # Check if Cloudflare R2 configuration is available
        try:
            # Check if we have the necessary settings
            if hasattr(settings, 'CLOUDFLARE_R2_BUCKET') and \
               hasattr(settings, 'CLOUDFLARE_R2_ACCESS_KEY') and \
               hasattr(settings, 'CLOUDFLARE_R2_SECRET_KEY') and \
               hasattr(settings, 'CLOUDFLARE_R2_BUCKET_ENDPOINT'):
               
                # Flag to determine if we should use R2 storage
                # Use R2 when DEBUG is False (production) or forced by environment variable
                self.use_r2 = not settings.DEBUG or os.environ.get('FORCE_R2', False)
                self.bucket_name = settings.CLOUDFLARE_R2_BUCKET
                
                if self.use_r2:
                    self._init_r2_client()
            else:
                logger.warning("Cloudflare R2 settings not found. Using local storage only.")
        except Exception as e:
            logger.error(f"Error initializing R2 storage. Using local storage only. Error: {e}")
            self.use_r2 = False
    
    def _init_r2_client(self):
        """Initialize the Cloudflare R2 client"""
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
                endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.use_r2 = False
    
    def _get_r2_key(self, filename):
        """Convert a filename to an R2 key"""
        return f'ml_models/{os.path.basename(filename)}'
    
    def file_exists(self, filename):
        """Check if a model file exists in the appropriate storage"""
        # Check local storage first
        local_path = os.path.join(self.local_model_dir, os.path.basename(filename))
        if os.path.exists(local_path):
            return True
            
        # Check R2 if enabled
        if self.use_r2 and self.s3_client:
            try:
                key = self._get_r2_key(filename)
                self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
                return True
            except Exception:
                return False
        return False
    
    def get_filepath(self, filename):
        """Get the full path to a model file (for local storage only)"""
        return os.path.join(self.local_model_dir, os.path.basename(filename))
    
    def load_file(self, filename, loader_func):
        """
        Load a model file from storage using the provided loader function
        
        Args:
            filename (str): Name of the model file
            loader_func (callable): Function to load the model (e.g., joblib.load)
            
        Returns:
            The loaded model or None if file not found
        """
        # First try local storage
        local_path = os.path.join(self.local_model_dir, os.path.basename(filename))
        if os.path.exists(local_path):
            try:
                return loader_func(local_path)
            except Exception as e:
                logger.error(f"Error loading local file {filename}: {e}")
                
        # If not found locally or error loading, try R2 if enabled
        if self.use_r2 and self.s3_client:
            try:
                # Try to load from R2
                key = self._get_r2_key(filename)
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
                file_content = response['Body'].read()
                
                # Load from bytes buffer
                buffer = io.BytesIO(file_content)
                
                # Also save locally for future use
                try:
                    with open(local_path, 'wb') as f:
                        f.write(file_content)
                except Exception as e:
                    logger.warning(f"Failed to save local copy of {filename}: {e}")
                
                return loader_func(buffer)
            
            except Exception as e:
                logger.error(f"Error loading from R2: {str(e)}")
        
        logger.warning(f"File {filename} not found in any storage")
        return None
    
    def save_file(self, model_obj, filename, saver_func):
        """
        Save a model file to storage using the provided saver function
        
        Args:
            model_obj: The model object to save
            filename (str): Name of the model file
            saver_func (callable): Function to save the model (e.g., joblib.dump)
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Always save locally first
        local_path = os.path.join(self.local_model_dir, os.path.basename(filename))
        
        try:
            # Save locally
            saver_func(model_obj, local_path)
            
            # If using R2, also upload to R2
            if self.use_r2 and self.s3_client:
                try:
                    key = self._get_r2_key(filename)
                    with open(local_path, 'rb') as file_data:
                        self.s3_client.upload_fileobj(
                            file_data,
                            self.bucket_name,
                            key,
                            ExtraArgs={'ContentType': 'application/octet-stream'}
                        )
                except Exception as e:
                    logger.error(f"Error uploading to R2: {e}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving model {filename}: {str(e)}")
            return False