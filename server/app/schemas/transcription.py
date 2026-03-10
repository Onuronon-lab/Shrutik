from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class TranscriptionBase(BaseModel):
    """Base transcription schema with common fields."""

    text: str = Field(
        ..., min_length=1, max_length=5000, description="Transcribed text"
    )
    language_id: int = Field(..., gt=0, description="Language ID")
    quality: Optional[float] = Field(
        None, ge=0, le=1, description="Quality score (0-1)"
    )
    confidence: Optional[float] = Field(
        None, ge=0, le=1, description="Confidence score (0-1)"
    )
    meta_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate transcription text."""
        if not v.strip():
            raise ValueError("Transcription text cannot be empty")
        return v.strip()


class TranscriptionCreate(TranscriptionBase):
    """Schema for creating a new transcription."""

    chunk_id: int = Field(..., gt=0, description="Audio chunk ID being transcribed")


class TranscriptionUpdate(BaseModel):
    """Schema for updating an existing transcription."""

    text: Optional[str] = Field(None, min_length=1, max_length=5000)
    quality: Optional[float] = Field(None, ge=0, le=1)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    is_consensus: Optional[bool] = None
    is_validated: Optional[bool] = None
    meta_data: Optional[Dict[str, Any]] = None

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
        """Validate transcription text if provided."""
        if v is not None and not v.strip():
            raise ValueError("Transcription text cannot be empty")
        return v.strip() if v else v


class TranscriptionResponse(TranscriptionBase):
    """Schema for transcription response."""

    id: int
    chunk_id: int
    user_id: int
    is_consensus: bool
    is_validated: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AudioChunkForTranscription(BaseModel):
    """Schema for audio chunk data needed for transcription."""

    id: int
    recording_id: int
    chunk_index: int
    file_path: str
    start_time: float
    end_time: float
    duration: float
    sentence_hint: Optional[str] = None
    transcription_count: int = Field(0, description="Number of existing transcriptions")

    model_config = {"from_attributes": True}


class TranscriptionTaskRequest(BaseModel):
    """Schema for requesting transcription tasks."""

    quantity: int = Field(
        ..., ge=1, le=20, description="Number of chunks to transcribe (1-20)"
    )
    language_id: Optional[int] = Field(None, gt=0, description="Filter by language ID")
    skip_chunk_ids: Optional[List[int]] = Field(
        default_factory=list, description="Chunk IDs to skip"
    )

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        """Validate quantity is within allowed range."""
        allowed_quantities = [2, 5, 10, 15, 20]
        if v not in allowed_quantities:
            raise ValueError(
                f'Quantity must be one of: {", ".join(map(str, allowed_quantities))}'
            )
        return v


class TranscriptionTaskResponse(BaseModel):
    """Schema for transcription task response."""

    chunks: List[AudioChunkForTranscription]
    total_available: int
    session_id: str = Field(
        ..., description="Session ID for tracking this transcription batch"
    )


class TranscriptionSubmission(BaseModel):
    """Schema for submitting transcriptions."""

    session_id: str = Field(..., description="Session ID from transcription task")
    transcriptions: List[TranscriptionCreate]
    skipped_chunk_ids: Optional[List[int]] = Field(
        default_factory=list, description="Chunk IDs that were skipped"
    )

    @field_validator("transcriptions")
    @classmethod
    def validate_transcriptions(cls, v):
        """Validate transcriptions list."""
        if not v:
            raise ValueError("At least one transcription must be provided")
        return v


class TranscriptionSubmissionResponse(BaseModel):
    """Schema for transcription submission response."""

    submitted_count: int
    skipped_count: int
    transcriptions: List[TranscriptionResponse]
    message: str


class TranscriptionListResponse(BaseModel):
    """Schema for paginated transcription list response."""

    transcriptions: List[TranscriptionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class TranscriptionStatistics(BaseModel):
    """Schema for transcription statistics."""

    total_transcriptions: int
    by_user: List[Dict[str, Any]]
    by_language: List[Dict[str, Any]]
    consensus_rate: float
    validation_rate: float
    average_quality_score: float
    chunks_with_transcriptions: int
    chunks_needing_transcription: int


class ChunkSkipRequest(BaseModel):
    """Schema for skipping a difficult chunk."""

    chunk_id: int = Field(..., gt=0, description="Audio chunk ID to skip")
    reason: Optional[str] = Field(
        None, max_length=500, description="Optional reason for skipping"
    )


class ChunkSkipResponse(BaseModel):
    """Schema for chunk skip response."""

    chunk_id: int
    skipped_by_user: int
    reason: Optional[str]
    skip_count: int = Field(
        ..., description="Total number of times this chunk has been skipped"
    )
    created_at: datetime
