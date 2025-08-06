import boto3
import uuid
from botocore.exceptions import ClientError
from botocore.config import Config
from typing import Dict, Optional
from io import BytesIO
import os
from dotenv import load_dotenv
import logging
import traceback
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class S3Service:
    def __init__(self):
        # Optimize boto3 configuration for better performance
        config = Config(
            region_name=os.getenv("AWS_REGION"),
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=50,  # Increase connection pool
            connect_timeout=5,        # 5 seconds connection timeout
            read_timeout=10           # 10 seconds read timeout
        )

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            config=config
        )
        self.bucket_name = os.getenv("AWS_BUCKET_NAME")

    def presigned_url(self, extension: str, content_type: str, expires_in: int = 1800) -> Dict[str, str]:
        logger.info(f"Generating presigned URL for extension: {extension}, content_type: {content_type}")

        # Generate unique key with timestamp for better organization
        key = f"uploads/{uuid.uuid4()}.{extension}"

        try:
            # Generate presigned URL with optimized parameters
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ContentType': content_type,
                    # Add server-side encryption for security
                    'ServerSideEncryption': 'AES256'
                },
                ExpiresIn=expires_in
            )

            logger.info(f"Successfully generated presigned URL for key: {key}")
            return {'preSignedUrl': url, 'Key': key}

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"AWS S3 ClientError ({error_code}): {str(e)}")
            raise RuntimeError(f"Failed to generate presigned URL: {error_code}")
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise RuntimeError(f"Failed to generate presigned URL: {str(e)}")

    def delete_file(self, key: str):
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            raise RuntimeError(f"Failed to delete file: {e}")

    def download_file(self, key: str) -> Dict[str, Optional[bytes]]:
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            file_stream = response['Body'].read()
            content_type = response.get('ContentType')
            return {
                'buffer': file_stream,
                'contentType': content_type,
                'key': key
            }
        except ClientError as e:
            raise RuntimeError(f"Failed to download file: {e}")
    
