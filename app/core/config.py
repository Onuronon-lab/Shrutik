from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
import os


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)
    
    APP_NAME: str = "Voice Data Collection Platform"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/voice_collection"
    
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Job monitoring settings
    JOB_RESULT_EXPIRES: int = 3600  # 1 hour
    JOB_MAX_RETRIES: int = 3
    JOB_RETRY_DELAY: int = 60  # 1 minute
    
    # Development settings
    USE_CELERY: bool = True  # Set to False to disable Celery and use synchronous processing
    
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024
    ALLOWED_AUDIO_FORMATS: List[str] = [".wav", ".mp3", ".m4a", ".flac", ".webm"]
    
    CHUNK_MIN_DURATION: float = 1.0
    CHUNK_MAX_DURATION: float = 10.0


settings = Settings()