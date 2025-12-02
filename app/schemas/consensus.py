"""
Pydantic schemas for consensus and quality validation.

These schemas define the data structures for consensus evaluation,
validation status, and manual review processes.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.quality_review import ReviewDecision


class ConsensusEvaluationRequest(BaseModel):
    """Request model for consensus evaluation."""

    chunk_id: int = Field(..., description="ID of the chunk to evaluate")
    force_recalculation: bool = Field(
        False, description="Force recalculation even if already evaluated"
    )


class ConsensusResult(BaseModel):
    """Result of consensus evaluation."""

    chunk_id: int
    consensus_text: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    requires_review: bool
    participant_count: int = Field(..., ge=0)
    quality_score: float = Field(..., ge=0.0, le=1.0)
    transcription_similarities: List[float]
    flagged_reasons: List[str]


class ValidationStatus(BaseModel):
    """Validation status for a chunk."""

    chunk_id: int
    is_validated: bool
    consensus_transcription_id: Optional[int] = None
    validation_confidence: float = Field(..., ge=0.0, le=1.0)
    requires_manual_review: bool
    last_updated: datetime


class TranscriptionInfo(BaseModel):
    """Information about a transcription for review."""

    id: int
    text: str
    user_id: int
    quality: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    is_consensus: bool = False
    is_validated: bool = False


class ChunkReviewInfo(BaseModel):
    """Information about a chunk requiring review."""

    chunk_id: int
    recording_id: int
    duration: float
    transcription_count: int = Field(..., ge=0)
    flagged_reasons: List[str]
    transcriptions: List[TranscriptionInfo]


class ManualReviewRequest(BaseModel):
    """Request for manual review decision."""

    decision: ReviewDecision
    selected_transcription_id: Optional[int] = Field(
        None,
        description="ID of transcription to mark as consensus (required for APPROVED decision)",
    )
    comment: Optional[str] = Field(
        None, max_length=1000, description="Optional review comment"
    )

    model_config = {"use_enum_values": True}


class ManualReviewResponse(BaseModel):
    """Response for manual review decision."""

    success: bool
    message: str
    chunk_id: int
    decision: ReviewDecision
    reviewer_id: int
    reviewed_at: datetime

    model_config = {"use_enum_values": True}


class BatchConsensusRequest(BaseModel):
    """Request for batch consensus calculation."""

    chunk_ids: List[int] = Field(..., min_length=1, max_length=1000)
    priority: str = Field("normal", pattern="^(low|normal|high)$")


class BatchConsensusResponse(BaseModel):
    """Response for batch consensus calculation."""

    task_id: str
    message: str
    chunk_count: int
    estimated_completion_time: Optional[str] = None


class ValidationStatistics(BaseModel):
    """Statistics about validation and consensus."""

    total_chunks_with_transcriptions: int = Field(..., ge=0)
    validated_chunks: int = Field(..., ge=0)
    chunks_requiring_review: int = Field(..., ge=0)
    consensus_transcriptions: int = Field(..., ge=0)
    validation_rate: float = Field(
        ..., ge=0.0, le=100.0, description="Percentage of validated chunks"
    )
    average_confidence_score: float = Field(..., ge=0.0, le=1.0)
    average_quality_score: float = Field(..., ge=0.0, le=1.0)
    quality_review_counts: Dict[str, int]


class ChunkValidationStatus(BaseModel):
    """Current validation status of a specific chunk."""

    chunk_id: int
    has_transcriptions: bool
    transcription_count: int = Field(..., ge=0)
    is_validated: bool
    has_consensus: bool
    requires_review: bool
    consensus_transcription_id: Optional[int] = None
    transcriptions: List[TranscriptionInfo]


class QualityMetrics(BaseModel):
    """Quality metrics for transcriptions."""

    similarity_scores: List[float]
    average_similarity: float = Field(..., ge=0.0, le=1.0)
    length_consistency: float = Field(..., ge=0.0, le=1.0)
    participant_diversity: int = Field(..., ge=0)
    confidence_variance: float = Field(..., ge=0.0)


class AuditTrailEntry(BaseModel):
    """Entry in the audit trail for validation decisions."""

    timestamp: datetime
    action: str
    user_id: Optional[int] = None
    chunk_id: int
    details: Dict[str, Any]
    system_generated: bool = False


class ConsensusConfiguration(BaseModel):
    """Configuration parameters for consensus calculation."""

    min_transcriptions_for_consensus: int = Field(2, ge=1, le=10)
    consensus_similarity_threshold: float = Field(0.7, ge=0.0, le=1.0)
    high_confidence_threshold: float = Field(0.8, ge=0.0, le=1.0)
    low_confidence_threshold: float = Field(0.5, ge=0.0, le=1.0)
    max_transcription_length_diff: float = Field(0.3, ge=0.0, le=1.0)


class ReviewQueueFilter(BaseModel):
    """Filters for the review queue."""

    flagged_reasons: Optional[List[str]] = None
    min_transcription_count: Optional[int] = Field(None, ge=1)
    max_transcription_count: Optional[int] = Field(None, ge=1)
    confidence_range: Optional[tuple[float, float]] = None
    recording_ids: Optional[List[int]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "flagged_reasons": [
                    "Low consensus confidence",
                    "Large transcription length differences",
                ],
                "min_transcription_count": 2,
                "max_transcription_count": 10,
                "confidence_range": [0.0, 0.5],
                "recording_ids": [1, 2, 3],
            }
        }
    }


class ConsensusTaskStatus(BaseModel):
    """Status of a consensus calculation task."""

    task_id: str
    status: str  # PENDING, PROGRESS, SUCCESS, FAILURE
    current: Optional[int] = None
    total: Optional[int] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
