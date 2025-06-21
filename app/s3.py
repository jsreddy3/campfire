import os, boto3
from botocore.client import Config

S3_BUCKET = os.environ["S3_BUCKET"]
REGION    = os.getenv("AWS_REGION", "us-west-2")

aws = boto3.client("s3", region_name=REGION, config=Config(signature_version="s3v4"))

def presign_upload(dream_id: str, filename: str, expires: int = 3600):
    key = f"dreams/{dream_id}/{filename}"
    return aws.generate_presigned_post(
        Bucket=S3_BUCKET,
        Key=key,
        ExpiresIn=expires,
        Fields={"acl": "private"},
        Conditions=[{"acl": "private"}],
    )

def presign_download(key: str, expires: int = 3600):
    return aws.generate_presigned_url(
        "get_object", Params={"Bucket": S3_BUCKET, "Key": key}, ExpiresIn=expires
    )