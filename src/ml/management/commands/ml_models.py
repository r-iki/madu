from django.core.management.base import BaseCommand
import os
from django.conf import settings
from ml.s3storage import S3ModelStorage
import glob

class Command(BaseCommand):
    help = 'Upload ML models to S3 storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--download',
            action='store_true',
            help='Download models from S3 instead of uploading',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List models in S3',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to upload/download (filename only)',
        )

    def handle(self, *args, **options):
        s3_storage = S3ModelStorage()
        model_dir = os.path.join(settings.BASE_DIR, 'ml', 'saved_models')
        
        # Make sure the directory exists
        os.makedirs(model_dir, exist_ok=True)
        
        # List models
        if options['list']:
            models = s3_storage.list_models()
            if models:
                self.stdout.write(self.style.SUCCESS(f"Models in S3:"))
                for model in models:
                    self.stdout.write(self.style.SUCCESS(f"- {model}"))
            else:
                self.stdout.write(self.style.WARNING("No models found in S3"))
            return
        
        # Download models
        if options['download']:
            if options['model']:
                # Download a specific model
                model_name = options['model']
                local_path = os.path.join(model_dir, model_name)
                success = s3_storage.download_model(model_name, local_path)
                if success:
                    self.stdout.write(self.style.SUCCESS(f"Downloaded {model_name}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to download {model_name}"))
            else:
                # Download all models
                models = s3_storage.list_models()
                if not models:
                    self.stdout.write(self.style.WARNING("No models found in S3"))
                    return
                
                for model_name in models:
                    if model_name:  # Skip empty names
                        local_path = os.path.join(model_dir, model_name)
                        success = s3_storage.download_model(model_name, local_path)
                        if success:
                            self.stdout.write(self.style.SUCCESS(f"Downloaded {model_name}"))
                        else:
                            self.stdout.write(self.style.ERROR(f"Failed to download {model_name}"))
            return
        
        # Upload models
        if options['model']:
            # Upload a specific model
            model_name = options['model']
            local_path = os.path.join(model_dir, model_name)
            if os.path.exists(local_path):
                success = s3_storage.upload_model(local_path, model_name)
                if success:
                    self.stdout.write(self.style.SUCCESS(f"Uploaded {model_name}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to upload {model_name}"))
            else:
                self.stdout.write(self.style.ERROR(f"File not found: {local_path}"))
        else:
            # Upload all models
            model_files = glob.glob(os.path.join(model_dir, "*.pkl"))
            
            if not model_files:
                self.stdout.write(self.style.WARNING(f"No .pkl files found in {model_dir}"))
                return
                
            for local_path in model_files:
                model_name = os.path.basename(local_path)
                success = s3_storage.upload_model(local_path, model_name)
                if success:
                    self.stdout.write(self.style.SUCCESS(f"Uploaded {model_name}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to upload {model_name}"))
