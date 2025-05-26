import boto3
import requests
from io import BytesIO
from PyPDF2 import PdfMerger, PdfReader
from typing import List, Tuple, Optional
import tempfile
import os
from datetime import datetime
from PIL import Image
import logging
import time
from botocore.config import Config
from botocore.exceptions import ClientError
from ..config import get_settings
from ..utils.logger import setup_logger


class PDFService:
    def __init__(self, is_prod: bool = False):
        self.settings = get_settings()
        self.is_prod = is_prod
        self.logger = setup_logger("pdf_service", is_prod)

        # Configure S3 client with retries and longer timeouts
        config = Config(
            retries=dict(
                max_attempts=3,
                mode='adaptive'
            ),
            connect_timeout=5,
            read_timeout=10,
            max_pool_connections=50
        )

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.settings.AWS_REGION,
            config=config
        )
        self.logger.info(
            f"Initialized PDFService for {'production' if is_prod else 'staging'} environment")

    def convert_image_to_pdf(self, image_data: BytesIO) -> Optional[BytesIO]:
        """Convert image to PDF with A4 sizing"""
        try:
            # Open image
            image = Image.open(image_data)

            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1])
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # A4 size in pixels at 300 DPI (standard print quality)
            A4_WIDTH = 2480  # 8.27 inches * 300 DPI
            A4_HEIGHT = 3508  # 11.69 inches * 300 DPI

            # Calculate aspect ratio
            img_width, img_height = image.size
            aspect_ratio = img_width / img_height

            # Calculate new dimensions while maintaining aspect ratio
            if aspect_ratio > 1:  # Landscape
                new_width = min(A4_WIDTH, img_width)
                new_height = int(new_width / aspect_ratio)
                if new_height > A4_HEIGHT:
                    new_height = A4_HEIGHT
                    new_width = int(new_height * aspect_ratio)
            else:  # Portrait
                new_height = min(A4_HEIGHT, img_height)
                new_width = int(new_height * aspect_ratio)
                if new_width > A4_WIDTH:
                    new_width = A4_WIDTH
                    new_height = int(new_width / aspect_ratio)

            # Resize image with high-quality resampling
            resized_image = image.resize(
                (new_width, new_height), Image.Resampling.LANCZOS)

            # Create a new white A4 background
            a4_image = Image.new('RGB', (A4_WIDTH, A4_HEIGHT), (255, 255, 255))

            # Calculate position to center the image
            x_offset = (A4_WIDTH - new_width) // 2
            y_offset = (A4_HEIGHT - new_height) // 2

            # Paste the resized image onto the A4 background
            a4_image.paste(resized_image, (x_offset, y_offset))

            # Save as PDF
            pdf_data = BytesIO()
            a4_image.save(pdf_data, format='PDF', resolution=300.0)
            pdf_data.seek(0)

            self.logger.info(
                f"Image converted to A4 PDF successfully (original size: {img_width}x{img_height}, new size: {new_width}x{new_height})")
            return pdf_data
        except Exception as e:
            self.logger.error(f"Error converting image to PDF: {str(e)}")
            return None

    def validate_pdf(self, pdf_data: BytesIO) -> Tuple[bool, str]:
        """Validate if the file is a valid PDF"""
        try:
            pdf_data.seek(0)
            PdfReader(pdf_data)
            return True, ""
        except Exception as e:
            return False, str(e)

    def download_and_convert_file(self, url: str) -> Optional[BytesIO]:
        """Download file and convert to PDF if necessary"""
        self.logger.info(f"Downloading file from URL: {url}")
        try:
            response = requests.get(url)
            response.raise_for_status()

            content_type = response.headers.get('content-type', '').lower()
            file_data = BytesIO(response.content)

            # Handle PDF files
            if 'application/pdf' in content_type:
                is_valid, error_msg = self.validate_pdf(file_data)
                if is_valid:
                    self.logger.info(
                        "PDF file downloaded and validated successfully")
                    return file_data
                else:
                    self.logger.warning(f"Invalid PDF file: {error_msg}")
                    return None

            # Handle image files
            elif any(img_type in content_type for img_type in ['image/jpeg', 'image/png', 'image/gif']):
                self.logger.info(f"Converting image ({content_type}) to PDF")
                pdf_data = self.convert_image_to_pdf(file_data)
                if pdf_data:
                    self.logger.info("Image converted to PDF successfully")
                    return pdf_data
                else:
                    self.logger.warning("Failed to convert image to PDF")
                    return None

            else:
                self.logger.warning(
                    f"Unsupported content type: {content_type}")
                return None

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error downloading file: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}")
            return None

    def merge_pdfs(self, pdf_files: List[BytesIO]) -> Optional[BytesIO]:
        """Merge multiple PDF files in order"""
        if not pdf_files:
            self.logger.error("No valid PDF files to merge")
            return None

        self.logger.info(f"Starting to merge {len(pdf_files)} PDF files")
        try:
            merger = PdfMerger()

            for i, pdf_file in enumerate(pdf_files, 1):
                try:
                    # Reset file pointer and validate again before merging
                    pdf_file.seek(0)
                    is_valid, error_msg = self.validate_pdf(pdf_file)
                    if not is_valid:
                        self.logger.warning(
                            f"Skipping invalid PDF file at position {i}: {error_msg}")
                        continue

                    merger.append(pdf_file)
                    self.logger.debug(f"Added PDF {i} to merger")
                except Exception as e:
                    self.logger.warning(f"Error processing PDF {i}: {str(e)}")
                    continue

            if len(merger.pages) == 0:
                self.logger.error("No valid PDFs to merge")
                return None

            output = BytesIO()
            merger.write(output)
            output.seek(0)
            self.logger.info("PDFs merged successfully")
            return output
        except Exception as e:
            self.logger.error(f"Error merging PDFs: {str(e)}")
            return None

    def upload_to_s3(self, file_data: BytesIO, bucket: str, key: str) -> Optional[str]:
        """Upload file to S3 bucket with retries and error handling"""
        self.logger.info(
            f"Uploading merged PDF to S3 bucket: {bucket}, key: {key}")

        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                # Ensure file pointer is at the beginning
                file_data.seek(0)

                # Upload with retry configuration
                self.s3_client.upload_fileobj(
                    file_data,
                    bucket,
                    key,
                    ExtraArgs={
                        'ContentType': 'application/pdf',
                        'ACL': 'private'
                    }
                )

                self.logger.info("File uploaded successfully to S3")
                return key

            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code')
                error_message = e.response.get('Error', {}).get('Message')

                if error_code == 'RequestTimeTooSkewed':
                    self.logger.warning(
                        f"Time skew detected on attempt {attempt + 1}. Retrying...")
                    # Exponential backoff
                    time.sleep(retry_delay * (attempt + 1))
                    continue

                self.logger.error(
                    f"S3 upload error (attempt {attempt + 1}/{max_retries}): {error_code} - {error_message}")
                if attempt == max_retries - 1:
                    return None

            except Exception as e:
                self.logger.error(
                    f"Unexpected error during S3 upload (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt == max_retries - 1:
                    return None

            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff

        return None

    def process_and_merge(self, urls: List[str], lead_id: str, is_prod: bool = False) -> Optional[str]:
        """Process URLs, merge PDFs, and upload to S3"""
        self.logger.info(
            f"Processing merge request for lead_id: {lead_id} with {len(urls)} PDFs")
        try:
            # Download and convert all files
            pdf_files = []
            for url in urls:
                pdf_file = self.download_and_convert_file(url)
                if pdf_file:
                    pdf_files.append(pdf_file)

            if not pdf_files:
                raise ValueError("No valid files could be processed")

            # Merge PDFs
            merged_pdf = self.merge_pdfs(pdf_files)
            if not merged_pdf:
                raise ValueError("Failed to merge PDFs")

            # Determine bucket
            bucket = self.settings.PROD_BUCKET_NAME if is_prod else self.settings.STAGING_BUCKET_NAME

            # Generate S3 key with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key = f"{lead_id}/merged_pdf/merged_document_{timestamp}.pdf"

            # Upload to S3 with retries
            result = self.upload_to_s3(merged_pdf, bucket, s3_key)
            if not result:
                raise ValueError(
                    "Failed to upload to S3 after multiple attempts")

            self.logger.info(
                f"Successfully processed merge request for lead_id: {lead_id}")
            return s3_key
        except Exception as e:
            self.logger.error(f"Error in process_and_merge: {str(e)}")
            raise ValueError(f"Failed to process and merge PDFs: {str(e)}")
