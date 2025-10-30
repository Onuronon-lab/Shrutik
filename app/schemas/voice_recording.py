from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from app.models.voice_recording import RecordingStatus


class VoiceRecordingBase(BaseModel):
    """Base voice recording schema with common fields."""
    script_id: int = Field(..., gt=0, description="ID of the script being recorded")
    language_id: int = Field(..., gt=0, description="Language ID")
    duration: float = Field(..., gt=0, description="Recording duration in seconds")
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v):
        """Validate recording duration."""
        if v <= 0:
            raise ValueError('Duration must be positive')
        if v > 1800:  # 30 minutes max
            raise ValueError('Duration cannot exceed 30 minutes')
        return v


class VoiceRecordingCreate(VoiceRecordingBase):
    """Schema for creating a new voice recording."""
    pass


class VoiceRecordingUpdate(BaseModel):
    """Schema for updating an existing voice recording."""
    status: Optional[RecordingStatus] = None
    duration: Optional[float] = Field(None, gt=0)
    meta_data: Optional[Dict[str, Any]] = None

    @field_validator('duration')
    @classmethod
    def validate_duration(cls, v):
        """Validate recording duration if provided."""
        if v is not None:
            if v <= 0:
                raise ValueError('Duration must be positive')
            if v > 1800:  # 30 minutes max
                raise ValueError('Duration cannot exceed 30 minutes')
        return v


class VoiceRecordingResponse(VoiceRecordingBase):
    """Schema for voice recording response."""
    id: int
    user_id: int
    file_path: str
    status: RecordingStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VoiceRecordingListResponse(BaseModel):
    """Schema for paginated voice recording list response."""
    recordings: list[VoiceRecordingResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class RecordingSessionCreate(BaseModel):
    """Schema for creating a recording session."""
    script_id: int = Field(..., gt=0, description="ID of the script to record")
    language_id: Optional[int] = Field(None, gt=0, description="Language ID (optional, defaults to script language)")


class RecordingSessionResponse(BaseModel):
    """Schema for recording session response."""
    session_id: str = Field(..., description="Unique session identifier")
    script_id: int
    script_text: str
    language_id: int
    expected_duration_category: str
    created_at: datetime
    expires_at: datetime


class RecordingUploadRequest(BaseModel):
    """Schema for recording upload request."""
    session_id: str = Field(..., description="Recording session identifier")
    duration: float = Field(..., gt=0, description="Actual recording duration in seconds")
    audio_format: str = Field(..., description="Audio file format (e.g., 'wav', 'mp3')")
    sample_rate: Optional[int] = Field(None, gt=0, description="Audio sample rate in Hz")
    channels: Optional[int] = Field(None, gt=0, le=2, description="Number of audio channels")
    bit_depth: Optional[int] = Field(None, gt=0, description="Audio bit depth")
    file_size: int = Field(..., gt=0, description="File size in bytes")

    @field_validator('audio_format')
    @classmethod
    def validate_audio_format(cls, v):
        """Validate audio format."""
        allowed_formats = ['wav', 'mp3', 'm4a', 'flac', 'webm']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Audio format must be one of: {", ".join(allowed_formats)}')
        return v.lower()

    @field_validator('file_size')
    @classmethod
    def validate_file_size(cls, v):
        """Validate file size."""
        max_size = 100 * 1024 * 1024  # 100MB
        if v > max_size:
            raise ValueError(f'File size cannot exceed {max_size // (1024 * 1024)}MB')
        return v


class RecordingProgressResponse(BaseModel):
    """Schema for recording progress response."""
    recording_id: int
    status: RecordingStatus
    progress_percentage: float = Field(..., ge=0, le=100)
    message: str
    estimated_completion: Optional[datetime] = None


class RecordingStatistics(BaseModel):
    """Schema for recording statistics."""
    total_recordings: int
    by_status: Dict[str, int]
    by_duration_category: Dict[str, int]
    by_language: list[Dict[str, Any]]
    total_duration_hours: float
    average_duration_minutes: float