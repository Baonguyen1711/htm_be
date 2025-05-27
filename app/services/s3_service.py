import boto3
import uuid
from fastapi import UploadFile
from botocore.exceptions import ClientError
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
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION")
        )
        self.bucket_name = os.getenv("AWS_BUCKET_NAME")

    def presigned_url(self, extension: str, content_type: str, expires_in: int = 1800) -> Dict[str, str]:
        logger.info(f"extension {extension}")
        logger.info(f"content_type {content_type}")
        key = f"{uuid.uuid4()}.{extension}"
        try:
            logger.info("Attempting to create reference to Firebase")
            url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key,
                    'ContentType': content_type
                },
                ExpiresIn=expires_in
            )
            logger.info(f"url {url}")
            return {'preSignedUrl': url, 'Key': key}
        except Exception as e:
            logger.error(f"Error creating Firebase reference: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise 

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
    
