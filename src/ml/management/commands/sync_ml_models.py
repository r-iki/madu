import os
import glob
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage
from botocore.exceptions import ClientError
import joblib
import pickle
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sync ML models with Cloudflare R2 storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--direction',
            type=str,
            default='upload',
            choices=['upload', 'download', 'list'],
            help='Direction of sync: upload, download, or list'
        )

    def _get_r2_client(self):
        # Set up the S3 client for Cloudflare R2
        return boto3.client(
            's3',
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
            endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
        )

    def _get_local_models(self):
        # Get the list of local model files
        model_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
        os.makedirs(model_dir, exist_ok=True)
        return glob.glob(os.path.join(model_dir, '*.pkl'))    def _upload_models(self):
        """Upload local models to Cloudflare R2"""
        s3_client = self._get_r2_client()
        bucket_name = settings.CLOUDFLARE_R2_BUCKET
        model_files = self._get_local_models()

        if not model_files:
            self.stdout.write(self.style.WARNING('No .pkl files found in the saved_models directory.'))
            return

        for model_path in model_files:
            filename = os.path.basename(model_path)
            s3_key = f'ml_models/{filename}'
            
            try:
                # Upload the file
                self.stdout.write(f'Uploading {filename} to R2 storage as {s3_key}...')
                with open(model_path, 'rb') as file_data:
                    s3_client.upload_fileobj(
                        file_data,
                        bucket_name,
                        s3_key,
                        ExtraArgs={'ACL': 'private', 'ContentType': 'application/octet-stream'}
                    )
                
                # Verify the upload by checking if the file now exists
                try:
                    head = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
                    self.stdout.write(self.style.SUCCESS(
                        f'Successfully uploaded {filename} ({head["ContentLength"]} bytes)'
                    ))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'Upload appeared to succeed but verification failed: {str(e)}'
                    ))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Failed to upload {filename}: {str(e)}'))

    def _download_models(self):
        """Download models from Cloudflare R2 to local storage"""
        s3_client = self._get_r2_client()
        bucket_name = settings.CLOUDFLARE_R2_BUCKET
        model_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
        os.makedirs(model_dir, exist_ok=True)
        
        try:
            # List all objects in the ml_models directory
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='ml_models/'
            )
            
            if 'Contents' not in response:
                self.stdout.write(self.style.WARNING('No models found in R2 storage.'))
                return
                
            for obj in response['Contents']:
                key = obj['Key']
                filename = os.path.basename(key)
                if filename:  # Skip directories
                    local_path = os.path.join(model_dir, filename)
                    self.stdout.write(f'Downloading {filename} from R2 storage...')
                    
                    try:
                        s3_client.download_file(bucket_name, key, local_path)
                        self.stdout.write(self.style.SUCCESS(f'Successfully downloaded {filename}'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'Failed to download {filename}: {str(e)}'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error listing objects in R2 storage: {str(e)}'))    def _list_models(self):
        """List models available in Cloudflare R2"""
        s3_client = self._get_r2_client()
        bucket_name = settings.CLOUDFLARE_R2_BUCKET
        
        try:
            # Debug info
            self.stdout.write(f"Using bucket: {bucket_name}")
            self.stdout.write(f"Endpoint URL: {settings.CLOUDFLARE_R2_BUCKET_ENDPOINT}")
            
            # First, try listing without a prefix to check if the bucket is accessible
            self.stdout.write("Checking bucket access...")
            try:
                list_response = s3_client.list_objects_v2(
                    Bucket=bucket_name,
                    MaxKeys=5
                )
                if 'Contents' in list_response:
                    self.stdout.write(f"Bucket is accessible. Contains {len(list_response['Contents'])} objects.")
                else:
                    self.stdout.write("Bucket appears to be empty.")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to access bucket: {str(e)}"))
            
            # List all objects in the ml_models directory
            self.stdout.write("Listing ML models...")
            response = s3_client.list_objects_v2(
                Bucket=bucket_name,
                Prefix='ml_models/'
            )
            
            # Debug the response
            self.stdout.write(f"Response keys: {', '.join(response.keys())}")
            
            if 'Contents' not in response:
                self.stdout.write(self.style.WARNING('No models found in R2 storage with prefix "ml_models/".'))
                return
                
            self.stdout.write(self.style.SUCCESS(f'Found {len(response["Contents"])} models in R2 storage:'))
            for obj in response['Contents']:
                key = obj['Key']
                size = obj['Size']
                last_modified = obj['LastModified']
                self.stdout.write(f'  - {key} ({size} bytes, last modified: {last_modified})')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error listing objects in R2 storage: {str(e)}'))

    def handle(self, *args, **options):
        direction = options['direction']
        
        if direction == 'upload':
            self.stdout.write('Uploading ML models to Cloudflare R2...')
            self._upload_models()
        elif direction == 'download':
            self.stdout.write('Downloading ML models from Cloudflare R2...')
            self._download_models()
        elif direction == 'list':
            self.stdout.write('Listing ML models in Cloudflare R2...')
            self._list_models()
        
        self.stdout.write(self.style.SUCCESS('Done!'))
