import boto3
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Debug Cloudflare R2 connection issues'

    def handle(self, *args, **options):
        # Display settings
        self.stdout.write(f"Bucket name: {settings.CLOUDFLARE_R2_BUCKET}")
        self.stdout.write(f"Endpoint URL: {settings.CLOUDFLARE_R2_BUCKET_ENDPOINT}")
        self.stdout.write(f"Access key ID: {settings.CLOUDFLARE_R2_ACCESS_KEY[:5]}...")
        
        # Set up S3 client
        self.stdout.write("Setting up S3 client...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
            aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
            endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
        )
        
        # List buckets
        try:
            self.stdout.write("Listing buckets...")
            response = s3_client.list_buckets()
            buckets = [bucket['Name'] for bucket in response['Buckets']]
            self.stdout.write(f"Available buckets: {', '.join(buckets)}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing buckets: {str(e)}"))
        
        # List all objects in the bucket
        try:
            self.stdout.write(f"Listing all objects in bucket: {settings.CLOUDFLARE_R2_BUCKET}")
            response = s3_client.list_objects_v2(
                Bucket=settings.CLOUDFLARE_R2_BUCKET
            )
            if 'Contents' in response:
                self.stdout.write(f"Found {len(response['Contents'])} objects")
                for obj in response['Contents']:
                    self.stdout.write(f"- {obj['Key']} ({obj['Size']} bytes)")
            else:
                self.stdout.write("No objects found in bucket")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing objects: {str(e)}"))
        
        # Try listing with the ml_models prefix
        try:
            self.stdout.write("Trying to list objects with 'ml_models/' prefix...")
            response = s3_client.list_objects_v2(
                Bucket=settings.CLOUDFLARE_R2_BUCKET,
                Prefix='ml_models/'
            )
            if 'Contents' in response:
                self.stdout.write(f"Found {len(response['Contents'])} objects with prefix 'ml_models/'")
                for obj in response['Contents']:
                    self.stdout.write(f"- {obj['Key']} ({obj['Size']} bytes)")
            else:
                self.stdout.write("No objects found with prefix 'ml_models/'")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error listing with prefix: {str(e)}"))
