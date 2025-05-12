import os
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
import shutil
import joblib
import pickle
import glob
from ml.model_storage import ModelStorageManager

class Command(BaseCommand):
    help = 'Export ML model files from saved_models to Cloudflare R2 storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force upload even if file exists in R2'
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verify uploads with R2 head_object check'
        )

    def _get_r2_client(self):
        # Create R2 client
        return boto3.client(
            's3',
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
            endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
        )

    def handle(self, *args, **options):
        # Initialize model storage manager
        model_storage = ModelStorageManager()
        
        # Directory where models are stored locally
        model_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
        
        if not os.path.exists(model_dir):
            self.stdout.write(self.style.ERROR(f"Directory {model_dir} does not exist!"))
            return
            
        # Initialize S3 client for direct operations if needed
        s3_client = self._get_r2_client()
        bucket_name = settings.CLOUDFLARE_R2_BUCKET
            
        # Count processed files
        success_count = 0
        error_count = 0
        
        # Get all .pkl files in the directory
        model_files = [f for f in os.listdir(model_dir) if f.endswith('.pkl')]
        
        if not model_files:
            self.stdout.write(self.style.WARNING("No .pkl model files found."))
            return
            
        self.stdout.write(f"Found {len(model_files)} .pkl files.")
        
        # Try to import joblib for model loading
        try:
            import joblib
            loader = joblib.load
            saver = joblib.dump
        except ImportError:
            self.stdout.write(self.style.WARNING("joblib not found, falling back to pickle."))
            loader = lambda f: pickle.load(open(f, 'rb'))
            saver = lambda obj, f: pickle.dump(obj, open(f, 'wb'))
              # Process each model file
        for filename in model_files:
            file_path = os.path.join(model_dir, filename)
            r2_key = f'ml_models/{filename}'
            
            # Check if the file already exists in R2
            if not options['force']:
                try:
                    s3_client.head_object(Bucket=bucket_name, Key=r2_key)
                    self.stdout.write(f"Model {filename} already exists in R2. Use --force to overwrite.")
                    continue
                except Exception:
                    # File doesn't exist, proceed with upload
                    pass
            
            try:                # Direct upload with boto3 (more reliable)
                self.stdout.write(f"Uploading {filename} to R2 storage...")
                with open(file_path, 'rb') as file_data:
                    s3_client.upload_fileobj(
                        file_data, 
                        bucket_name, 
                        r2_key,
                        ExtraArgs={
                            'ContentType': 'application/octet-stream',
                        }
                    )
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully uploaded {filename} to R2 storage."))# Verify the upload if requested
                if options['verify']:
                    try:
                        head = s3_client.head_object(Bucket=bucket_name, Key=r2_key)
                        self.stdout.write(self.style.SUCCESS(
                            f"Verification successful: {filename} ({head['ContentLength']} bytes)"
                        ))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(
                            f"Upload seemed successful but verification failed: {str(e)}"
                        ))
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f"Error processing {filename}: {str(e)}"))
                
        # List the models in R2 to confirm
        self.stdout.write("\nChecking models in R2:")
        try:
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='ml_models/'
            )
            
            if 'Contents' in response:
                r2_models = [os.path.basename(obj['Key']) for obj in response['Contents']]
                self.stdout.write(self.style.SUCCESS(f"Found {len(response['Contents'])} models in R2:"))
                for obj in response['Contents']:
                    self.stdout.write(f"  - {obj['Key']} ({obj['Size']} bytes)")
            else:
                self.stdout.write(self.style.WARNING("No models found in R2 storage."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing models in R2: {str(e)}"))
        
        # Summary
        self.stdout.write("\nSummary:")
        self.stdout.write(f"Successfully uploaded {success_count} model files.")
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Failed to upload {error_count} model files."))
        
        self.stdout.write(self.style.SUCCESS("Done!"))
