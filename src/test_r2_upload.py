import os
import django
import boto3
import sys

# Print Python version
print(f"Python version: {sys.version}")

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Now import settings
from django.conf import settings

def upload_test_file():
    print("Creating S3 client...")
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
        aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
        endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT
    )
    
    print(f"Using bucket: {settings.CLOUDFLARE_R2_BUCKET}")
    
    # Create a test file
    test_key = 'ml_models/test_file.txt'
    test_content = b'This is a test file for R2 storage!'
    
    print(f"Uploading test file to {test_key}...")
    s3.put_object(
        Bucket=settings.CLOUDFLARE_R2_BUCKET,
        Key=test_key,
        Body=test_content,
        ContentType='text/plain'
    )
    print("Upload successful!")
    
    # Verify file exists
    print("Verifying file exists...")
    try:
        head = s3.head_object(Bucket=settings.CLOUDFLARE_R2_BUCKET, Key=test_key)
        print(f"File exists! Size: {head['ContentLength']} bytes")
    except Exception as e:
        print(f"Failed to verify file: {e}")
    
    # List files in the bucket with ml_models prefix
    print("\nListing files with 'ml_models/' prefix:")
    response = s3.list_objects_v2(
        Bucket=settings.CLOUDFLARE_R2_BUCKET,
        Prefix='ml_models/'
    )
    
    if 'Contents' in response:
        print(f"Found {len(response['Contents'])} files:")
        for obj in response['Contents']:
            print(f"- {obj['Key']} ({obj['Size']} bytes)")
    else:
        print("No files found with 'ml_models/' prefix!")
        print(f"Response keys: {', '.join(response.keys())}")

if __name__ == "__main__":
    upload_test_file()
