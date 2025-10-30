"""
Export API endpoints for secure data export functionality.

This module provides REST API endpoints for exporting validated datasets
and metadata, restricted to users with sworik_developer role permissions.
All export activities are logged for audit purposes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.dependencies import require_export_permission
from app.models.user import User
from app.services.export_service import ExportService
from app.schemas.export import (
    DatasetExportRequest, MetadataExportRequest,
    DatasetExportResponse, MetadataExportResponse,
    ExportHistoryRequest, ExportAuditLogResponse
)

router = APIRouter(prefix="/api/export", tags=["export"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request."""
    # Get IP address (considering proxy headers)
    ip_address = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
        request.headers.get("X-Real-IP") or
        request.client.host if request.client else None
    )
    
    # Get user agent
    user_agent = request.headers.get("User-Agent")
    
    return ip_address, user_agent


@router.post("/dataset", response_model=DatasetExportResponse)
async def export_dataset(
    request: DatasetExportRequest,
    http_request: Request,
    current_user: User = Depends(require_export_permission),
    db: Session = Depends(get_db)
):
    """
    Export validated dataset with filtering and format options.
    
    This endpoint allows Sworik developers to export validated voice-transcript
    pairs with various filtering options and format choices. All export activities
    are logged for audit purposes.
    
    **Required Permission:** export_data (sworik_developer role)
    
    **Supported Formats:**
    - JSON: Standard JSON format
    - CSV: Comma-separated values
    - JSONL: JSON Lines format (one JSON object per line)
    - Parquet: Columnar storage format
    
    **Quality Filters:**
    - min_confidence: Minimum confidence score (0.0-1.0)
    - min_quality: Minimum quality score (0.0-1.0)
    - consensus_only: Only include consensus transcriptions
    - validated_only: Only include validated transcriptions
    
    **Other Filters:**
    - language_ids: Filter by specific languages
    - user_ids: Filter by specific contributors
    - date_from/date_to: Filter by recording date range
    - max_records: Limit number of exported records
    """
    export_service = ExportService(db)
    ip_address, user_agent = get_client_info(http_request)
    
    try:
        response = export_service.export_dataset(
            request=request,
            user=current_user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dataset export failed: {str(e)}"
        )


@router.post("/metadata", response_model=MetadataExportResponse)
async def export_metadata(
    request: MetadataExportRequest,
    http_request: Request,
    current_user: User = Depends(require_export_permission),
    db: Session = Depends(get_db)
):
    """
    Export platform metadata and statistics.
    
    This endpoint allows Sworik developers to export platform metadata,
    statistics, and quality metrics for analysis and reporting purposes.
    
    **Required Permission:** export_data (sworik_developer role)
    
    **Available Metadata:**
    - Platform statistics (recordings, chunks, transcriptions counts)
    - Quality metrics (average scores, consensus rates)
    - User statistics (per-user contribution stats) - optional
    - Processing metrics (status distribution, durations)
    
    **Supported Formats:**
    - JSON: Standard JSON format
    - CSV: Comma-separated values (flattened structure)
    """
    export_service = ExportService(db)
    ip_address, user_agent = get_client_info(http_request)
    
    try:
        response = export_service.export_metadata(
            request=request,
            user=current_user,
            ip_address=ip_address,
            user_agent=user_agent
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metadata export failed: {str(e)}"
        )


@router.get("/history", response_model=ExportAuditLogResponse)
async def get_export_history(
    user_id: Optional[int] = None,
    export_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(require_export_permission),
    db: Session = Depends(get_db)
):
    """
    Get export history and audit logs.
    
    This endpoint allows Sworik developers to view the history of all
    data export operations for audit and transparency purposes.
    
    **Required Permission:** export_data (sworik_developer role)
    
    **Query Parameters:**
    - user_id: Filter by specific user ID
    - export_type: Filter by export type ('dataset' or 'metadata')
    - date_from: Filter from date (ISO format)
    - date_to: Filter to date (ISO format)
    - page: Page number for pagination
    - page_size: Number of records per page (max 1000)
    """
    from datetime import datetime
    
    export_service = ExportService(db)
    
    # Parse date strings if provided
    parsed_date_from = None
    parsed_date_to = None
    
    if date_from:
        try:
            parsed_date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_from format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
    
    if date_to:
        try:
            parsed_date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date_to format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
            )
    
    # Validate page parameters
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be >= 1"
        )
    
    if page_size < 1 or page_size > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 1000"
        )
    
    try:
        logs, total_count = export_service.get_export_history(
            user_id=user_id,
            export_type=export_type,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            page=page,
            page_size=page_size
        )
        
        return ExportAuditLogResponse(
            logs=logs,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve export history: {str(e)}"
        )


@router.get("/formats")
async def get_supported_formats(
    current_user: User = Depends(require_export_permission)
):
    """
    Get list of supported export formats.
    
    Returns information about available export formats and their
    characteristics for both dataset and metadata exports.
    
    **Required Permission:** export_data (sworik_developer role)
    """
    return {
        "dataset_formats": {
            "json": {
                "name": "JSON",
                "description": "Standard JSON format with nested structure",
                "mime_type": "application/json",
                "file_extension": ".json",
                "supports_metadata": True
            },
            "csv": {
                "name": "CSV",
                "description": "Comma-separated values with flattened structure",
                "mime_type": "text/csv",
                "file_extension": ".csv",
                "supports_metadata": False
            },
            "jsonl": {
                "name": "JSON Lines",
                "description": "One JSON object per line, suitable for streaming",
                "mime_type": "application/jsonl",
                "file_extension": ".jsonl",
                "supports_metadata": True
            },
            "parquet": {
                "name": "Parquet",
                "description": "Columnar storage format, efficient for analytics",
                "mime_type": "application/octet-stream",
                "file_extension": ".parquet",
                "supports_metadata": True
            }
        },
        "metadata_formats": {
            "json": {
                "name": "JSON",
                "description": "Standard JSON format with nested structure",
                "mime_type": "application/json",
                "file_extension": ".json"
            },
            "csv": {
                "name": "CSV",
                "description": "Comma-separated values with flattened structure",
                "mime_type": "text/csv",
                "file_extension": ".csv"
            }
        }
    }


@router.get("/stats")
async def get_export_statistics(
    current_user: User = Depends(require_export_permission),
    db: Session = Depends(get_db)
):
    """
    Get current platform statistics for export planning.
    
    Returns current platform statistics to help users understand
    the scope of data available for export before making export requests.
    
    **Required Permission:** export_data (sworik_developer role)
    """
    export_service = ExportService(db)
    
    try:
        statistics = export_service._generate_platform_statistics()
        platform_metrics = export_service._generate_platform_metrics()
        quality_metrics = export_service._generate_quality_metrics()
        
        return {
            "statistics": statistics,
            "platform_metrics": platform_metrics,
            "quality_metrics": quality_metrics,
            "last_updated": statistics.export_timestamp
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve export statistics: {str(e)}"
        )