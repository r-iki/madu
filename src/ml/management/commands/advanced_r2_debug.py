import os
import boto3
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Advanced debug tool for R2 storage and model synchronization'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            default='all',
            choices=['list', 'test-upload', 'test-key', 'check-core', 'all'],
            help='Debug mode to run'
        )
        parser.add_argument(
            '--prefix',
            type=str,
            default=None,
            help='Specific prefix to check in R2'
        )

    def _get_r2_client(self):
        """Create an S3 client for Cloudflare R2"""
        try:
            client = boto3.client(
                's3',
                aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
                aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
                endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
            )
            return client
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create R2 client: {e}"))
            return None

    def _check_core_settings(self):
        """Check core R2 settings"""
        self.stdout.write("Checking core R2 settings:")
        self.stdout.write(f"  Bucket name: {settings.CLOUDFLARE_R2_BUCKET}")
        self.stdout.write(f"  Endpoint: {settings.CLOUDFLARE_R2_BUCKET_ENDPOINT}")
        
        # Check for empty or None values
        for name, value in [
            ('CLOUDFLARE_R2_BUCKET', settings.CLOUDFLARE_R2_BUCKET),
            ('CLOUDFLARE_R2_ACCESS_KEY', settings.CLOUDFLARE_R2_ACCESS_KEY),
            ('CLOUDFLARE_R2_SECRET_KEY', settings.CLOUDFLARE_R2_SECRET_KEY),
            ('CLOUDFLARE_R2_BUCKET_ENDPOINT', settings.CLOUDFLARE_R2_BUCKET_ENDPOINT),
        ]:
            if not value:
                self.stdout.write(self.style.ERROR(f"  {name} is empty or not set!"))

    def _list_bucket_contents(self, prefix=None):
        """List contents of the R2 bucket with optional prefix"""
        s3_client = self._get_r2_client()
        bucket_name = settings.CLOUDFLARE_R2_BUCKET
        
        if not s3_client:
            return
            
        try:
            params = {'Bucket': bucket_name}
            if prefix:
                params['Prefix'] = prefix
                
            response = s3_client.list_objects_v2(**params)
            
            self.stdout.write(f"Listing objects in bucket '{bucket_name}':")
            if prefix:
                self.stdout.write(f"  With prefix: '{prefix}'")
            
            if 'Contents' not in response:
                self.stdout.write(self.style.WARNING("  No objects found"))
                return
                
            self.stdout.write(f"  Found {len(response['Contents'])} objects:")
            for obj in response['Contents'][:20]:  # Limit to first 20
                self.stdout.write(f"  - {obj['Key']} ({obj['Size']} bytes)")
                
            if len(response['Contents']) > 20:
                self.stdout.write(f"  ... and {len(response['Contents']) - 20} more")
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing bucket contents: {e}"))

    def _test_upload(self):
        """Test uploading a small file to R2"""
        s3_client = self._get_r2_client()
        bucket_name = settings.CLOUDFLARE_R2_BUCKET
        
        if not s3_client:
            return
            
        # Create a small test file
        test_content = b"This is a test file for R2 storage."
        test_key = "ml_models/r2_test_file.txt"
        
        try:
            self.stdout.write(f"Uploading test file to '{test_key}'...")
            
            # Upload directly using put_object
            s3_client.put_object(
                Bucket=bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType='text/plain',
                ACL='private'
            )
            
            self.stdout.write(self.style.SUCCESS("  Upload successful"))
            
            # Verify the file exists
            self.stdout.write("Verifying test file exists...")
            try:
                response = s3_client.head_object(
                    Bucket=bucket_name,
                    Key=test_key
                )
                self.stdout.write(self.style.SUCCESS(f"  File exists: {response['ContentLength']} bytes"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to verify file: {e}"))
                
            # Now retrieve the object
            self.stdout.write("Retrieving test file content...")
            try:
                response = s3_client.get_object(
                    Bucket=bucket_name,
                    Key=test_key
                )
                content = response['Body'].read()
                self.stdout.write(self.style.SUCCESS(f"  Retrieved content: {content}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  Failed to retrieve file: {e}"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error in test upload: {e}"))

    def _test_key_variations(self):
        """Test with different key/prefix variations"""
        variations = [
            "ml_models",
            "ml_models/",
            "ml-models",
            "ml-models/",
            "models",
            "models/",
            "ml/models",
            "ml/models/"
        ]
        
        self.stdout.write("Testing various key prefix variations:")
        for prefix in variations:
            self._list_bucket_contents(prefix)
            self.stdout.write("-" * 40)

    def handle(self, *args, **options):
        mode = options['mode']
        prefix = options['prefix']
        
        self.stdout.write(f"Running R2 debug in mode: {mode}")
        
        if mode == 'list' or mode == 'all':
            if prefix:
                self._list_bucket_contents(prefix)
            else:
                self._list_bucket_contents()
        
        if mode == 'test-upload' or mode == 'all':
            self._test_upload()
            
        if mode == 'test-key' or mode == 'all':
            self._test_key_variations()
            
        if mode == 'check-core' or mode == 'all':
            self._check_core_settings()
            
        self.stdout.write(self.style.SUCCESS("Debug complete"))
