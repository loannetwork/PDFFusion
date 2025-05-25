from fastapi import FastAPI
from .api.endpoints import router

app = FastAPI(
    title="PDF Merger Service",
    description="""
    A microservice for merging PDFs from S3 presigned URLs.
    
    ## Features
    * Merge multiple PDFs from S3 presigned URLs
    * Separate endpoints for staging and production environments
    * Automatic S3 upload of merged PDFs
    * Robust error handling
    
    ## Authentication
    This service requires AWS credentials configured in the environment.
    
    ## Environment Setup
    Required environment variables:
    * AWS_ACCESS_KEY_ID
    * AWS_SECRET_ACCESS_KEY
    * AWS_REGION
    * STAGING_BUCKET_NAME
    * PROD_BUCKET_NAME
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

app.include_router(router, prefix="/api/v1")


@app.get("/health",
         tags=["Health"],
         summary="Health Check Endpoint",
         description="Check if the service is running properly",
         response_description="Returns the health status of the service")
async def health_check():
    return {"status": "healthy"}
