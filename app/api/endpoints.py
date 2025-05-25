from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from ..services.pdf_service import PDFService
from ..utils.logger import setup_logger

router = APIRouter()
staging_logger = setup_logger("staging_endpoints", is_prod=False)
prod_logger = setup_logger("prod_endpoints", is_prod=True)

# Initialize services as None
staging_service = None
prod_service = None


def get_staging_service():
    global staging_service
    if staging_service is None:
        staging_service = PDFService(is_prod=False)
    return staging_service


def get_prod_service():
    global prod_service
    if prod_service is None:
        prod_service = PDFService(is_prod=True)
    return prod_service


class MergeRequest(BaseModel):
    lead_id: str = Field(...,
                         description="Unique identifier for the lead", example="LEAD123")
    urls: List[str] = Field(..., description="List of presigned S3 URLs for PDFs to merge",
                            example=["https://s3.amazonaws.com/bucket/file1.pdf",
                                     "https://s3.amazonaws.com/bucket/file2.pdf"])

    class Config:
        schema_extra = {
            "example": {
                "lead_id": "LEAD123",
                "urls": [
                    "https://s3.amazonaws.com/bucket/file1.pdf",
                    "https://s3.amazonaws.com/bucket/file2.pdf"
                ]
            }
        }


@router.post("/staging/merge",
             response_model=dict,
             summary="Merge PDFs in Staging Environment",
             description="""Merge multiple PDFs from presigned S3 URLs and upload the result to the staging bucket.
    
    - Downloads PDFs from provided presigned URLs
    - Merges them in the order provided
    - Uploads the merged PDF to the staging S3 bucket
    - Returns the S3 key of the merged PDF
    """,
             tags=["PDF Operations"])
async def merge_pdfs_staging(request: MergeRequest):
    """
    Merge PDFs in staging environment:

    - **lead_id**: Unique identifier for the lead
    - **urls**: List of presigned S3 URLs for PDFs to merge

    Returns:
    - **status**: Success status
    - **s3_key**: S3 key of the merged PDF
    """
    staging_logger.info(
        f"Received staging merge request for lead_id: {request.lead_id}")
    try:
        service = get_staging_service()
        s3_key = service.process_and_merge(
            request.urls, request.lead_id, is_prod=False)
        staging_logger.info(
            f"Successfully completed staging merge for lead_id: {request.lead_id}")
        return {"status": "success", "s3_key": s3_key}
    except Exception as e:
        staging_logger.error(f"Error in staging merge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prod/merge",
             response_model=dict,
             summary="Merge PDFs in Production Environment",
             description="""Merge multiple PDFs from presigned S3 URLs and upload the result to the production bucket.
    
    - Downloads PDFs from provided presigned URLs
    - Merges them in the order provided
    - Uploads the merged PDF to the production S3 bucket
    - Returns the S3 key of the merged PDF
    """,
             tags=["PDF Operations"])
async def merge_pdfs_prod(request: MergeRequest):
    """
    Merge PDFs in production environment:

    - **lead_id**: Unique identifier for the lead
    - **urls**: List of presigned S3 URLs for PDFs to merge

    Returns:
    - **status**: Success status
    - **s3_key**: S3 key of the merged PDF
    """
    prod_logger.info(
        f"Received production merge request for lead_id: {request.lead_id}")
    try:
        service = get_prod_service()
        s3_key = service.process_and_merge(
            request.urls, request.lead_id, is_prod=True)
        prod_logger.info(
            f"Successfully completed production merge for lead_id: {request.lead_id}")
        return {"status": "success", "s3_key": s3_key}
    except Exception as e:
        prod_logger.error(f"Error in production merge: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
