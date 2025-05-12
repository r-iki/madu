import os
import django
import boto3

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Now import settings
from django.conf import settings

def main():
    # Print settings
    print(f"Bucket: {settings.CLOUDFLARE_R2_BUCKET}")
    print(f"Endpoint: {settings.CLOUDFLARE_R2_BUCKET_ENDPOINT}")
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.CLOUDFLARE_R2_ACCESS_KEY,
        aws_secret_access_key=settings.CLOUDFLARE_R2_SECRET_KEY,
        endpoint_url=settings.CLOUDFLARE_R2_BUCKET_ENDPOINT,
    )
    
    # List all objects in the bucket
    print("\nListing all objects in the bucket:")
    response = s3_client.list_objects_v2(Bucket=settings.CLOUDFLARE_R2_BUCKET)
    print(f"Response contains 'Contents': {'Contents' in response}")
    
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f"  - {obj['Key']}")
    else:
        print("No objects found in the bucket")
    
    # Try with ml_models/ prefix
    print("\nListing objects with 'ml_models/' prefix:")
    response = s3_client.list_objects_v2(
        Bucket=settings.CLOUDFLARE_R2_BUCKET,
        Prefix='ml_models/'
    )
    print(f"Response contains 'Contents': {'Contents' in response}")
    
    if 'Contents' in response:
        for obj in response['Contents']:
            print(f"  - {obj['Key']}")
    else:
        print("No objects found with 'ml_models/' prefix")

if __name__ == "__main__":
    main()
