
from minio import Minio

client = Minio(
"play.min.io",
    access_key="Q3AM3UQ867SPQQA43P2F",
    secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
)

MINIO_BUCKET = "test-kwnlokne-bucket"

def upload_image_to_minio(image, image_name):
    found = client.bucket_exists(MINIO_BUCKET)
    if not found:
        client.make_bucket(MINIO_BUCKET)
        
    client.fput_object(
        MINIO_BUCKET,
        image_name,
        image,
    )

    url = client.presigned_get_object(MINIO_BUCKET, image_name)
    return url
    