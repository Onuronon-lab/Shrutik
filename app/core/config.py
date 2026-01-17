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
    # model_config = ConfigDict(env_file=".env", case_sensitive=True)
    model_config = ConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

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

    # Export Storage Configuration
    EXPORT_STORAGE_TYPE: Literal["local", "r2"] = "local"
    EXPORT_LOCAL_DIR: str = "/app/exports"

    # R2 Configuration (Cloudflare R2 for production)
    R2_ACCOUNT_ID: Optional[str] = None
    R2_ACCESS_KEY_ID: Optional[str] = None
    R2_SECRET_ACCESS_KEY: Optional[str] = None
    R2_BUCKET_NAME: Optional[str] = None
    R2_ENDPOINT_URL: Optional[str] = None

    # R2 Free Tier Protection
    R2_ENABLE_FREE_TIER_GUARD: bool = True
    R2_FREE_TIER_CLASS_A_MONTHLY: int = 1000000
    R2_FREE_TIER_CLASS_B_MONTHLY: int = 10000000
    R2_FREE_TIER_STORAGE_GB: float = 10.0

    # Export Batch Configuration
    EXPORT_BATCH_SIZE: int = 200
    EXPORT_SCHEDULE_CRON: str = "0 2 * * *"
    EXPORT_MIN_CHUNKS_THRESHOLD: int = 200
    EXPORT_COMPRESSION_LEVEL: int = 3
    EXPORT_MAX_CHUNK_SIZE_MB: int = 50
    EXPORT_DAILY_DOWNLOAD_LIMIT: int = 2

    # Role-based Export Configuration
    # Minimum chunk requirements by user role
    # These values control how many chunks are required to create an export batch
    # Lower values allow more flexible batch creation for privileged users
    EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER: int = 50  # Sworik developers need fewer chunks
    EXPORT_MIN_CHUNKS_ADMIN: int = 10  # Admins have the most flexibility

    # Daily download limits by user role
    # Controls how many export batches a user can download per day (UTC)
    # Use -1 for unlimited downloads
    EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER: int = (
        5  # Generous limit for developers
    )
    EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN: int = -1  # Unlimited downloads for admins

    # mail setting

    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@shrutik.com"
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Shrutik Platform"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    def __init__(self, **kwargs):
        """Initialize settings with validation."""
        super().__init__(**kwargs)
        self._validate_role_based_config()

    def _validate_role_based_config(self):
        """Validate role-based configuration values and log warnings for invalid settings."""
        import logging
        import os

        logger = logging.getLogger(__name__)

        # Track configuration sources for debugging
        config_sources = {}

        # Validate minimum chunk requirements
        original_sworik_chunks = self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER
        if self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER < 1:
            logger.warning(
                f"EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER ({self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER}) "
                "is less than 1. Using default value of 50."
            )
            self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER = 50
            config_sources["EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER"] = (
                "default (invalid value corrected)"
            )
        else:
            env_value = os.getenv("EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER")
            config_sources["EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER"] = (
                "environment" if env_value else "default"
            )

        original_admin_chunks = self.EXPORT_MIN_CHUNKS_ADMIN
        if self.EXPORT_MIN_CHUNKS_ADMIN < 1:
            logger.warning(
                f"EXPORT_MIN_CHUNKS_ADMIN ({self.EXPORT_MIN_CHUNKS_ADMIN}) "
                "is less than 1. Using default value of 10."
            )
            self.EXPORT_MIN_CHUNKS_ADMIN = 10
            config_sources["EXPORT_MIN_CHUNKS_ADMIN"] = (
                "default (invalid value corrected)"
            )
        else:
            env_value = os.getenv("EXPORT_MIN_CHUNKS_ADMIN")
            config_sources["EXPORT_MIN_CHUNKS_ADMIN"] = (
                "environment" if env_value else "default"
            )

        # Validate download limits (allow -1 for unlimited, 0 for no downloads allowed)
        original_sworik_downloads = self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER
        if self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER < -1:
            logger.warning(
                f"EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER ({self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER}) "
                "is invalid. Must be -1 (unlimited), 0 (no downloads), or positive integer. Using default value of 5."
            )
            self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER = 5
            config_sources["EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER"] = (
                "default (invalid value corrected)"
            )
        else:
            env_value = os.getenv("EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER")
            config_sources["EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER"] = (
                "environment" if env_value else "default"
            )

        original_admin_downloads = self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN
        if self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN < -1:
            logger.warning(
                f"EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN ({self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN}) "
                "is invalid. Must be -1 (unlimited), 0 (no downloads), or positive integer. Using default value of -1."
            )
            self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN = -1
            config_sources["EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN"] = (
                "default (invalid value corrected)"
            )
        else:
            env_value = os.getenv("EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN")
            config_sources["EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN"] = (
                "environment" if env_value else "default"
            )

        # Validate logical consistency
        if self.EXPORT_MIN_CHUNKS_ADMIN > self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER:
            logger.warning(
                f"Admin minimum chunks ({self.EXPORT_MIN_CHUNKS_ADMIN}) is greater than "
                f"Sworik Developer minimum chunks ({self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER}). "
                "This may indicate a configuration error - admins typically have lower requirements."
            )

        # Log configuration source for debugging
        logger.info("Role-based export configuration loaded:")
        logger.info(
            f"  Sworik Developer min chunks: {self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER} (source: {config_sources['EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER']})"
        )
        logger.info(
            f"  Admin min chunks: {self.EXPORT_MIN_CHUNKS_ADMIN} (source: {config_sources['EXPORT_MIN_CHUNKS_ADMIN']})"
        )
        logger.info(
            f"  Sworik Developer daily downloads: {self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER} (source: {config_sources['EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER']})"
        )
        logger.info(
            f"  Admin daily downloads: {self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN} (source: {config_sources['EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN']})"
        )

        # Log any corrections made
        corrections_made = []
        if original_sworik_chunks != self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER:
            corrections_made.append(
                f"EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER: {original_sworik_chunks} -> {self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER}"
            )
        if original_admin_chunks != self.EXPORT_MIN_CHUNKS_ADMIN:
            corrections_made.append(
                f"EXPORT_MIN_CHUNKS_ADMIN: {original_admin_chunks} -> {self.EXPORT_MIN_CHUNKS_ADMIN}"
            )
        if (
            original_sworik_downloads
            != self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER
        ):
            corrections_made.append(
                f"EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER: {original_sworik_downloads} -> {self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER}"
            )
        if original_admin_downloads != self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN:
            corrections_made.append(
                f"EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN: {original_admin_downloads} -> {self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN}"
            )

        if corrections_made:
            logger.info(
                f"Configuration corrections applied: {', '.join(corrections_made)}"
            )

    def get_min_chunks_for_role(self, user_role: str) -> int:
        """Get minimum chunk requirement for a specific user role.

        Args:
            user_role: The user role (from UserRole enum)

        Returns:
            Minimum number of chunks required for the role

        Raises:
            ValueError: If the role doesn't have export permissions
        """
        if user_role == "admin":
            return self.EXPORT_MIN_CHUNKS_ADMIN
        elif user_role == "sworik_developer":
            return self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER
        else:
            raise ValueError(f"Role '{user_role}' does not have export permissions")

    def get_daily_download_limit_for_role(self, user_role: str) -> int:
        """Get daily download limit for a specific user role.

        Args:
            user_role: The user role (from UserRole enum)

        Returns:
            Daily download limit (-1 for unlimited, positive integer for limit)

        Raises:
            ValueError: If the role doesn't have export permissions or configuration is invalid
        """
        if user_role == "admin":
            limit = self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN
            # Validate admin limit configuration
            if limit < -1:
                raise ValueError(
                    f"Invalid admin download limit configuration: {limit}. Must be -1 (unlimited) or >= 0"
                )
            return limit
        elif user_role == "sworik_developer":
            limit = self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER
            # Validate sworik developer limit configuration
            if limit < -1:
                raise ValueError(
                    f"Invalid sworik_developer download limit configuration: {limit}. Must be -1 (unlimited) or >= 0"
                )
            return limit
        else:
            raise ValueError(f"Role '{user_role}' does not have export permissions")

    def validate_startup_configuration(self) -> bool:
        """Validate all configuration values at startup.

        Returns:
            True if all configuration is valid, False if any corrections were needed

        This method can be called at application startup to ensure configuration
        is valid and log any issues that were automatically corrected.
        """
        import logging
        import os

        logger = logging.getLogger(__name__)

        # Check if any environment variables are missing
        expected_env_vars = [
            "EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER",
            "EXPORT_MIN_CHUNKS_ADMIN",
            "EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER",
            "EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN",
        ]

        missing_vars = []
        for var in expected_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            logger.info(
                f"Using default values for missing environment variables: {', '.join(missing_vars)}"
            )

        # Re-run validation to check if any corrections are needed
        original_values = {
            "sworik_chunks": self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER,
            "admin_chunks": self.EXPORT_MIN_CHUNKS_ADMIN,
            "sworik_downloads": self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER,
            "admin_downloads": self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN,
        }

        # This will apply any necessary corrections
        self._validate_role_based_config()

        # Check if any values were corrected
        corrections_needed = (
            original_values["sworik_chunks"] != self.EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER
            or original_values["admin_chunks"] != self.EXPORT_MIN_CHUNKS_ADMIN
            or original_values["sworik_downloads"]
            != self.EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER
            or original_values["admin_downloads"]
            != self.EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN
        )

        if not corrections_needed and not missing_vars:
            logger.info("All role-based export configuration is valid")
            return True
        else:
            logger.warning(
                "Configuration validation completed with corrections or missing values"
            )
            return False


settings = Settings()
