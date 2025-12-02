"""
Export Batch schemas for batch export functionality.

This module defines Pydantic schemas for export batch requests, responses,
and download quota management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Export Batch Schemas


class ExportBatchCreateRequest(BaseModel):
    """Request schema for creating export batch."""

    date_from: Optional[datetime] = Field(
        None, description="Filter chunks from this date"
    )
    date_to: Optional[datetime] = Field(None, description="Filter chunks to this date")
    min_duration: Optional[float] = Field(
        None, ge=0.0, description="Minimum chunk duration in seconds"
    )
    max_duration: Optional[float] = Field(
        None, ge=0.0, description="Maximum chunk duration in seconds"
    )
    force_create: bool = Field(
        True,
        description="Admin-only: Create batch even if < 200 chunks available (ignored for non-admin users)",
    )


class ExportBatchResponse(BaseModel):
    """Response schema for export batch."""

    id: int
    batch_id: str
    archive_path: str
    storage_type: str
    chunk_count: int
    file_size_bytes: Optional[int]
    chunk_ids: List[int]
    status: str
    exported: bool
    error_message: Optional[str]
    retry_count: int
    checksum: Optional[str]
    compression_level: Optional[int]
    format_version: str
    recording_id_range: Optional[Dict[str, Any]]
    language_stats: Optional[Dict[str, Any]]
    total_duration_seconds: Optional[float]
    filter_criteria: Optional[Dict[str, Any]]
    created_at: datetime
    completed_at: Optional[datetime]
    created_by_id: Optional[int]


class ExportBatchListResponse(BaseModel):
    """Response schema for export batch list."""

    batches: List[ExportBatchResponse]
    total_count: int
    page: int
    page_size: int


class ExportDownloadQuotaResponse(BaseModel):
    """Response schema for download quota."""

    downloads_today: int
    downloads_remaining: int
    daily_limit: int
    reset_time: datetime
