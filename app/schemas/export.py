"""
Export schemas for data export functionality.

This module defines Pydantic schemas for export requests, responses,
and audit logging related to data export operations.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    JSONL = "jsonl"  # JSON Lines format
    PARQUET = "parquet"


class QualityThreshold(BaseModel):
    """Quality filtering thresholds."""
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum confidence score")
    min_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Minimum quality score")
    consensus_only: bool = Field(False, description="Only include consensus transcriptions")
    validated_only: bool = Field(False, description="Only include validated transcriptions")


class DatasetExportRequest(BaseModel):
    """Request schema for dataset export."""
    format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    quality_filters: Optional[QualityThreshold] = Field(None, description="Quality filtering criteria")
    language_ids: Optional[List[int]] = Field(None, description="Filter by language IDs")
    user_ids: Optional[List[int]] = Field(None, description="Filter by contributor user IDs")
    date_from: Optional[datetime] = Field(None, description="Filter recordings from this date")
    date_to: Optional[datetime] = Field(None, description="Filter recordings to this date")
    include_metadata: bool = Field(True, description="Include detailed metadata")
    include_audio_paths: bool = Field(True, description="Include audio file paths")
    max_records: Optional[int] = Field(None, gt=0, description="Maximum number of records to export")


class MetadataExportRequest(BaseModel):
    """Request schema for metadata export."""
    format: ExportFormat = Field(ExportFormat.JSON, description="Export format")
    include_statistics: bool = Field(True, description="Include platform statistics")
    include_user_stats: bool = Field(False, description="Include per-user statistics")
    include_quality_metrics: bool = Field(True, description="Include quality metrics")


class ExportedDataItem(BaseModel):
    """Schema for individual exported data item."""
    chunk_id: int
    recording_id: int
    audio_file_path: str
    chunk_file_path: str
    transcription_text: str
    transcription_id: int
    contributor_id: int
    language_id: int
    language_name: str
    quality_score: float
    confidence_score: float
    is_consensus: bool
    is_validated: bool
    recording_duration: float
    chunk_duration: float
    chunk_start_time: float
    chunk_end_time: float
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ExportStatistics(BaseModel):
    """Export statistics and metadata."""
    total_recordings: int
    total_chunks: int
    total_transcriptions: int
    consensus_transcriptions: int
    validated_transcriptions: int
    unique_contributors: int
    languages: List[Dict[str, Any]]
    quality_distribution: Dict[str, int]
    export_timestamp: datetime
    filters_applied: Dict[str, Any]


class DatasetExportResponse(BaseModel):
    """Response schema for dataset export."""
    export_id: str
    data: List[ExportedDataItem]
    statistics: ExportStatistics
    format: ExportFormat
    total_records: int
    export_timestamp: datetime


class MetadataExportResponse(BaseModel):
    """Response schema for metadata export."""
    export_id: str
    statistics: ExportStatistics
    platform_metrics: Dict[str, Any]
    user_statistics: Optional[List[Dict[str, Any]]] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    format: ExportFormat
    export_timestamp: datetime


class ExportAuditLog(BaseModel):
    """Audit log entry for export operations."""
    id: int
    export_id: str
    user_id: int
    user_email: str
    export_type: Literal["dataset", "metadata"]
    format: ExportFormat
    filters_applied: Dict[str, Any]
    records_exported: int
    file_size_bytes: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime


class ExportAuditLogResponse(BaseModel):
    """Response schema for export audit logs."""
    logs: List[ExportAuditLog]
    total_count: int
    page: int
    page_size: int


class ExportHistoryRequest(BaseModel):
    """Request schema for export history."""
    user_id: Optional[int] = Field(None, description="Filter by user ID")
    export_type: Optional[Literal["dataset", "metadata"]] = Field(None, description="Filter by export type")
    date_from: Optional[datetime] = Field(None, description="Filter from this date")
    date_to: Optional[datetime] = Field(None, description="Filter to this date")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=1000, description="Page size")