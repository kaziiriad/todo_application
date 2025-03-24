import os
import pulumi
from pulumi_aws import s3

def create_s3_bucket_for_assets():
    """Create an S3 bucket to store file assets."""
    bucket = s3.Bucket("file-assets-bucket",
        acl="private",
        tags={"Name": "file-assets-bucket"}
    )
    return bucket

def upload_file_to_s3(bucket, file_path, key):
    """Upload a file to S3 and return the URL."""
    bucket_object = s3.BucketObject(f"file-asset-{key}",
        bucket=bucket.id,
        source=pulumi.FileAsset(file_path),
        key=key,
        acl="private"
    )
    
    # Generate a pre-signed URL that's valid for 1 hour
    url = pulumi.Output.all(bucket.bucket, bucket_object.key).apply(
        lambda args: f"https://{args[0]}.s3.amazonaws.com/{args[1]}"
    )
    
    return url

def get_docker_compose_urls(bucket):
    """Upload Docker Compose files and return their URLs."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    frontend_compose_path = os.path.join(base_dir, 'docker-compose/frontend-compose.yml')
    backend_compose_path = os.path.join(base_dir, 'docker-compose/backend-compose.yml')
    
    frontend_url = upload_file_to_s3(bucket, frontend_compose_path, "frontend-compose.yml")
    backend_url = upload_file_to_s3(bucket, backend_compose_path, "backend-compose.yml")
    
    return frontend_url, backend_url