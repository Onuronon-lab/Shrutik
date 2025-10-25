from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Voice Data Collection Platform"
    DEBUG: bool = False
    VERSION: str = "1.0.0"
    
    # Database settings
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/voice_collection"
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # File storage settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_AUDIO_FORMATS: List[str] = [".wav", ".mp3", ".m4a", ".flac"]
    
    # Audio processing settings
    CHUNK_MIN_DURATION: float = 1.0  # seconds
    CHUNK_MAX_DURATION: float = 10.0  # seconds
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()