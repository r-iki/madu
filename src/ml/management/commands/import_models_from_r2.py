from django.core.management.base import BaseCommand
from django.conf import settings
import os
import boto3
import io
import joblib
import pickle

class Command(BaseCommand):
    help = 'Import ML model files from Cloudflare R2 storage to local filesystem'

    def handle(self, *args, **options):
        # Directory where models should be stored locally
        model_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
        os.makedirs(model_dir, exist_ok=True)
        
        # Initialize R2 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
            endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
        )
        bucket_name = settings.CLOUDFLARE_R2_BUCKET
        
        # Count processed files
        success_count = 0
        error_count = 0
        
        try:
            # List all objects in the ml_models directory
            self.stdout.write("Listing models in R2 storage...")
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='ml_models/'
            )
            
            if 'Contents' not in response:
                self.stdout.write(self.style.WARNING('No models found in R2 storage.'))
                return
            
            model_files = [obj for obj in response['Contents'] if not obj['Key'].endswith('/')]
            self.stdout.write(f"Found {len(model_files)} model files in R2 storage.")
            
            # Process each model file
            for obj in model_files:
                key = obj['Key']
                filename = os.path.basename(key)
                if not filename:  # Skip directories
                    continue
                    
                local_path = os.path.join(model_dir, filename)
                
                try:
                    self.stdout.write(f"Downloading {filename} from R2 storage...")
                    
                    # Download the file
                    s3_client.download_file(bucket_name, key, local_path)
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Successfully downloaded {filename} to {local_path}"))
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f"Failed to download {filename}: {str(e)}"))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing objects in R2 storage: {str(e)}"))
            
        # Summary
        self.stdout.write("\nSummary:")
        self.stdout.write(f"Successfully downloaded {success_count} model files.")
        
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f"Failed to download {error_count} model files."))
        
        self.stdout.write(self.style.SUCCESS("Done!"))
