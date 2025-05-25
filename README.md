# PDF Merge Service

A FastAPI microservice for merging PDFs from S3 presigned URLs. The service supports both staging and production environments and can handle both PDF and image files.

## Features

- Merge multiple PDFs into a single document
- Support for both PDF and image files
- Environment-specific endpoints (staging/production)
- S3 integration for file storage
- Comprehensive logging
- Docker support
- Swagger documentation

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- AWS credentials with S3 access

## Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd pdf-merge-service
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create `.env` file with required environment variables:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
STAGING_BUCKET_NAME=your_staging_bucket
PROD_BUCKET_NAME=your_prod_bucket
```

## Running Locally

Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Endpoints

1. Staging Endpoint:

```
POST /api/v1/staging/merge
```

2. Production Endpoint:

```
POST /api/v1/prod/merge
```

Request body format:

```json
{
    "urls": ["presigned_url1", "presigned_url2", ...],
    "lead_id": "unique_lead_id"
}
```

## Docker Deployment

1. Build the Docker image:

```bash
docker build -t pdf-merge-service .
```

2. Run the container:

```bash
docker run -p 8000:8000 --env-file .env pdf-merge-service
```

## Testing

Run the test script:

```bash
python test_merge.py
```

## Project Structure

```
pdf-merge-service/
├── app/
│   ├── api/
│   │   └── endpoints.py
│   │   └── services/
│   │   └── pdf_service.py
│   │   └── utils/
│   │   └── logger.py
│   │   └── config.py
│   └── main.py
├── tests/
│   └── test_pdf_merge.py
├── .env
├── .gitignore
├── Dockerfile
├── README.md
└── requirements.txt
```

## Dependencies

- FastAPI: Web framework
- Uvicorn: ASGI server
- PyPDF2: PDF manipulation
- Boto3: AWS SDK
- Pillow: Image processing
- ReportLab: PDF generation
- Python-dotenv: Environment management
- Pydantic: Data validation

## Logging

Logs are stored in the `logs` directory with separate files for staging and production environments.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Your License]
