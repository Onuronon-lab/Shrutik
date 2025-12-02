from typing import List, Literal, Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class StorageConfig:
    """Configuration for export storage backend."""

    def __init__(
        self,
        storage_type: Literal["local", "r2"],
        local_export_dir: Optional[str] = None,
        r2_account_id: Optional[str] = None,
        r2_access_key_id: Optional[str] = None,
        r2_secret_access_key: Optional[str] = None,
        r2_bucket_name: Optional[str] = None,
        r2_endpoint_url: Optional[str] = None,
    ):
        self.storage_type = storage_type
        self.local_export_dir = local_export_dir
        self.r2_account_id = r2_account_id
        self.r2_access_key_id = r2_access_key_id
        self.r2_secret_access_key = r2_secret_access_key
        self.r2_bucket_name = r2_bucket_name
        self.r2_endpoint_url = r2_endpoint_url

        # Validate required fields based on storage_type
        self._validate()

    def _validate(self):
        """Validate required fields based on storage_type."""
        if self.storage_type == "local":
            if not self.local_export_dir:
                raise ValueError(
                    "local_export_dir is required when storage_type is 'local'"
                )
        elif self.storage_type == "r2":
            required_fields = {
                "r2_account_id": self.r2_account_id,
                "r2_access_key_id": self.r2_access_key_id,
                "r2_secret_access_key": self.r2_secret_access_key,
                "r2_bucket_name": self.r2_bucket_name,
                "r2_endpoint_url": self.r2_endpoint_url,
            }
            missing_fields = [
                field for field, value in required_fields.items() if not value
            ]
            if missing_fields:
                raise ValueError(
                    f"The following fields are required when storage_type is 'r2': {', '.join(missing_fields)}"
                )

    @classmethod
    def from_env(cls) -> "StorageConfig":
        """Load configuration from environment variables."""
        from app.core.config import settings

        return cls(
            storage_type=settings.EXPORT_STORAGE_TYPE,
            local_export_dir=settings.EXPORT_LOCAL_DIR,
            r2_account_id=settings.R2_ACCOUNT_ID,
            r2_access_key_id=settings.R2_ACCESS_KEY_ID,
            r2_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            r2_bucket_name=settings.R2_BUCKET_NAME,
            r2_endpoint_url=settings.R2_ENDPOINT_URL,
        )


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    APP_NAME: str = "Shrutik (শ্রুতিক)"
    DEBUG: bool = False
    VERSION: str = "1.0.0"

    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/voice_collection"

    REDIS_URL: str = "redis://localhost:6379/0"

    # Job monitoring settings
    JOB_RESULT_EXPIRES: int = 3600  # 1 hour
    JOB_MAX_RETRIES: int = 3
    JOB_RETRY_DELAY: int = 60  # 1 minute

    # Development settings
    USE_CELERY: bool = (
        True  # Set to False to disable Celery and use synchronous processing
    )

    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    ALGORITHM: str = "HS256"

    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    ALLOWED_AUDIO_FORMATS: List[str] = [".wav", ".mp3", ".m4a", ".flac", ".webm"]

    CHUNK_MIN_DURATION: float = 1.0
    CHUNK_MAX_DURATION: float = 10.0

    # Performance and caching settings
    ENABLE_CACHING: bool = True
    CACHE_DEFAULT_TTL: int = 3600  # 1 hour
    ENABLE_RATE_LIMITING: bool = True
    ENABLE_CDN: bool = False
    CDN_BASE_URL: str = ""

    # Database optimization settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600


settings = Settings()
