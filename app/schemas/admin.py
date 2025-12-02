from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.quality_review import ReviewDecision
from app.models.user import UserRole


class UserStatsResponse(BaseModel):
    user_id: int
    name: str
    email: str
    role: UserRole
    recordings_count: int
    transcriptions_count: int
    quality_reviews_count: int
    avg_transcription_quality: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PlatformStatsResponse(BaseModel):
    total_users: int
    total_contributors: int
    total_admins: int
    total_sworik_developers: int
    total_recordings: int
    total_chunks: int
    total_transcriptions: int
    total_validated_transcriptions: int
    total_quality_reviews: int
    avg_recording_duration: Optional[float] = None
    avg_transcription_quality: Optional[float] = None
    recordings_by_status: Dict[str, int]
    transcriptions_by_validation_status: Dict[str, int]


class UserManagementResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    recordings_count: int
    transcriptions_count: int
    quality_reviews_count: int
    created_at: datetime
    last_activity: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoleUpdateRequest(BaseModel):
    role: UserRole


class QualityReviewItemResponse(BaseModel):
    id: int
    transcription_id: int
    chunk_id: int
    transcription_text: str
    contributor_name: str
    contributor_id: int
    decision: ReviewDecision
    rating: Optional[float] = None
    comment: Optional[str] = None
    reviewer_name: Optional[str] = None
    created_at: datetime
    chunk_file_path: str

    model_config = {"from_attributes": True}


class FlaggedTranscriptionResponse(BaseModel):
    transcription_id: int
    chunk_id: int
    text: str
    contributor_name: str
    contributor_id: int
    quality_score: float
    confidence_score: float
    chunk_file_path: str
    created_at: datetime
    review_count: int

    model_config = {"from_attributes": True}


class SystemHealthResponse(BaseModel):
    database_status: str
    total_storage_used: Optional[float] = None  # in GB
    active_users_last_24h: int
    active_users_last_7d: int
    processing_queue_size: int
    failed_recordings_count: int
    avg_response_time: Optional[float] = None  # in ms
    uptime: Optional[str] = None


class UsageAnalyticsResponse(BaseModel):
    daily_recordings: List[Dict[str, Any]]  # [{date: str, count: int}, ...]
    daily_transcriptions: List[Dict[str, Any]]
    user_activity_by_role: Dict[str, int]
    popular_script_durations: Dict[str, int]
    transcription_quality_trend: List[Dict[str, Any]]
    top_contributors: List[
        Dict[str, Any]
    ]  # [{user_id: int, name: str, contribution_count: int}, ...]


class QualityReviewUpdateRequest(BaseModel):
    decision: ReviewDecision
    rating: Optional[float] = None
    comment: Optional[str] = None


# Admin Consensus API Schemas
class AdminConsensusCalculateRequest(BaseModel):
    """Request to trigger consensus calculation for specific chunks."""

    chunk_ids: List[int]

    model_config = {"json_schema_extra": {"example": {"chunk_ids": [1, 2, 3, 4, 5]}}}


class AdminConsensusCalculateResponse(BaseModel):
    """Response for consensus calculation trigger."""

    message: str
    chunks_processed: int
    chunks_validated: int
    chunks_flagged: int


class AdminConsensusReviewQueueItem(BaseModel):
    """Item in the consensus review queue."""

    chunk_id: int
    recording_id: int
    transcript_count: int
    consensus_quality: Optional[float] = None
    flagged_reasons: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminConsensusReviewQueueResponse(BaseModel):
    """Response for consensus review queue."""

    items: List[AdminConsensusReviewQueueItem]
    total_count: int
    page: int
    page_size: int


class AdminConsensusStatsResponse(BaseModel):
    """Statistics about consensus system."""

    total_chunks: int
    chunks_with_consensus: int
    chunks_validated: int
    chunks_pending_review: int
    chunks_ready_for_export: int
    avg_consensus_quality: Optional[float] = None
    avg_transcripts_per_chunk: Optional[float] = None


class AdminR2UsageResponse(BaseModel):
    """R2 storage usage statistics."""

    class_a_operations: int
    class_b_operations: int
    storage_used_gb: float
    class_a_limit: int
    class_b_limit: int
    storage_limit_gb: float
    class_a_usage_pct: float
    class_b_usage_pct: float
    storage_usage_pct: float


class AdminR2LimitsResponse(BaseModel):
    """R2 free tier limits check."""

    within_limits: bool
    warnings: List[str]
    usage: AdminR2UsageResponse
