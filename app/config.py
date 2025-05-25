from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    # AWS Configuration
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "us-east-1"

    # S3 Bucket Configuration
    STAGING_BUCKET_NAME: str
    PROD_BUCKET_NAME: str

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    STAGING_LOG_FILE: str = str(LOGS_DIR / "staging.log")
    PROD_LOG_FILE: str = str(LOGS_DIR / "prod.log")

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
