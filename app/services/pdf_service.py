import boto3
import requests
from io import BytesIO
from PyPDF2 import PdfMerger
from typing import List
import tempfile
import os
from datetime import datetime
from ..config import get_settings
from ..utils.logger import setup_logger


class PDFService:
    def __init__(self, is_prod: bool = False):
        self.settings = get_settings()
        self.is_prod = is_prod
        self.logger = setup_logger("pdf_service", is_prod)
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.settings.AWS_REGION
        )
        self.logger.info(
            f"Initialized PDFService for {'production' if is_prod else 'staging'} environment")

    def download_from_presigned_url(self, url: str) -> BytesIO:
        """Download file from presigned URL"""
        self.logger.info(f"Downloading file from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.logger.info("File downloaded successfully")
            return BytesIO(response.content)
        except Exception as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            raise

    def merge_pdfs(self, pdf_files: List[BytesIO]) -> BytesIO:
        """Merge multiple PDF files in order"""
        self.logger.info(f"Starting to merge {len(pdf_files)} PDF files")
        try:
            merger = PdfMerger()

            for i, pdf_file in enumerate(pdf_files, 1):
                merger.append(pdf_file)
                self.logger.debug(f"Added PDF {i} to merger")

            output = BytesIO()
            merger.write(output)
            output.seek(0)
            self.logger.info("PDFs merged successfully")
            return output
        except Exception as e:
            self.logger.error(f"Error merging PDFs: {str(e)}")
            raise

    def upload_to_s3(self, file_data: BytesIO, bucket: str, key: str) -> str:
        """Upload file to S3 bucket"""
        self.logger.info(
            f"Uploading merged PDF to S3 bucket: {bucket}, key: {key}")
        try:
            self.s3_client.upload_fileobj(
                file_data,
                bucket,
                key,
                ExtraArgs={'ContentType': 'application/pdf'}
            )
            self.logger.info("File uploaded successfully to S3")
            return key
        except Exception as e:
            self.logger.error(f"Error uploading to S3: {str(e)}")
            raise

    def process_and_merge(self, urls: List[str], lead_id: str, is_prod: bool = False) -> str:
        """Process URLs, merge PDFs, and upload to S3"""
        self.logger.info(
            f"Processing merge request for lead_id: {lead_id} with {len(urls)} PDFs")
        try:
            # Download all PDFs
            pdf_files = [self.download_from_presigned_url(url) for url in urls]

            # Merge PDFs
            merged_pdf = self.merge_pdfs(pdf_files)

            # Determine bucket
            bucket = self.settings.PROD_BUCKET_NAME if is_prod else self.settings.STAGING_BUCKET_NAME

            # Generate S3 key with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"{lead_id}/merged_pdf/merged_document_{timestamp}.pdf"

            # Upload to S3
            self.upload_to_s3(merged_pdf, bucket, s3_key)

            self.logger.info(
                f"Successfully processed merge request for lead_id: {lead_id}")
            return s3_key
        except Exception as e:
            self.logger.error(f"Error in process_and_merge: {str(e)}")
            raise
