"""
Export Batch API endpoints for batch export management.

This module provides REST API endpoints for creating, managing, and downloading
export batches. Export batches package ready chunks into compressed archives
for efficient data distribution.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import (
    get_current_active_user,
    require_admin,
    require_sworik_developer,
)
from app.db.database import get_db
from app.models.user import User
from app.schemas.export import (
    ExportBatchCreateRequest,
    ExportBatchListResponse,
    ExportBatchResponse,
    ExportDownloadQuotaResponse,
)
from app.services.export_batch_service import ExportBatchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/export/batch", tags=["export-batch"])


def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """Extract client IP and user agent from request."""
    ip_address = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP")
        or request.client.host
        if request.client
        else None
    )
    user_agent = request.headers.get("User-Agent")
    return ip_address, user_agent


@router.post("/create", response_model=ExportBatchResponse)
async def create_export_batch(
    request_body: ExportBatchCreateRequest,
    http_request: Request,
    current_user: User = Depends(require_sworik_developer),
    db: Session = Depends(get_db),
):
    """
    Create a new export batch from ready chunks.

    This endpoint allows users to create export batches with optional filtering criteria.
    The batch will include up to 200 chunks that meet the specified criteria and have not
    been previously exported.

    **Required Permission:** sworik_developer role (or admin)

    **Business Rules:**
    - Sworik developers: Can only create batches when >= 200 chunks are available (force_create is ignored)
    - Admins: Can create batches with any chunk count by setting force_create=True

    **Request Body:**
    - date_from: Filter chunks created from this date
    - date_to: Filter chunks created to this date
    - min_duration: Minimum chunk duration in seconds
    - max_duration: Maximum chunk duration in seconds
    - force_create: Admin-only override to create batch with < 200 chunks (default: True)

    **Behavior:**
    - Queries chunks WHERE ready_for_export = TRUE
    - Excludes chunks already in completed export batches (never-before-exported guarantee)
    - Applies date range and duration filters if specified
    - Limits to 200 chunks per batch
    - Creates tar.zst archive with audio files and JSON metadata
    - Uploads to configured storage (local or R2)
    - Triggers cleanup task to delete exported chunks

    **Returns:**
    - Export batch details including batch_id, chunk_count, filter_criteria, and status

    **Error Responses:**
    - 400: Insufficient chunks available (< 200 for non-admin users)
    - 500: Export batch creation failed
    """
    ip_address, user_agent = get_client_info(http_request)

    logger.info(
        f"Export batch creation requested by user {current_user.id} (role: {current_user.role.value}) "
        f"from IP {ip_address} with filters: {request_body.dict()}"
    )

    try:
        export_service = ExportBatchService(db)

        # Enforce business rule: only admins can use force_create
        # Sworik developers must have >= 200 chunks available
        is_admin = current_user.role.value == "admin"
        force_create = request_body.force_create if is_admin else False

        if not is_admin and request_body.force_create:
            logger.warning(
                f"User {current_user.id} (role: {current_user.role.value}) attempted to use "
                "force_create but is not admin. Ignoring force_create parameter."
            )

        # Create export batch with filters
        batch = export_service.create_export_batch(
            max_chunks=200,
            user_id=current_user.id,
            date_from=request_body.date_from,
            date_to=request_body.date_to,
            min_duration=request_body.min_duration,
            max_duration=request_body.max_duration,
            force_create=force_create,
        )

        logger.info(
            f"Export batch {batch.batch_id} created successfully with "
            f"{batch.chunk_count} chunks by user {current_user.id}"
        )

        return ExportBatchResponse(
            id=batch.id,
            batch_id=batch.batch_id,
            archive_path=batch.archive_path,
            storage_type=batch.storage_type,
            chunk_count=batch.chunk_count,
            file_size_bytes=batch.file_size_bytes,
            chunk_ids=batch.chunk_ids,
            status=batch.status,
            exported=batch.exported,
            error_message=batch.error_message,
            retry_count=batch.retry_count,
            checksum=batch.checksum,
            compression_level=batch.compression_level,
            format_version=batch.format_version,
            recording_id_range=batch.recording_id_range,
            language_stats=batch.language_stats,
            total_duration_seconds=batch.total_duration_seconds,
            filter_criteria=batch.filter_criteria,
            created_at=batch.created_at,
            completed_at=batch.completed_at,
            created_by_id=batch.created_by_id,
        )

    except ValueError as e:
        # Handle insufficient chunks error
        logger.warning(
            f"Export batch creation failed for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            f"Export batch creation failed for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export batch creation failed: {str(e)}",
        )


@router.get("/{batch_id}", response_model=ExportBatchResponse)
async def get_export_batch(
    batch_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Get export batch details by batch ID.

    This endpoint allows authenticated users to retrieve details about a specific
    export batch. Users can only access batches they created or all batches if admin.

    **Required Permission:** Authenticated user

    **Returns:**
    - Export batch details including status, chunk count, and metadata
    """
    try:
        export_service = ExportBatchService(db)
        batch = export_service.get_export_batch(batch_id)

        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export batch {batch_id} not found",
            )

        # Verify user has access to this batch
        # Users can access their own batches, admins can access all
        if (
            batch.created_by_id != current_user.id
            and current_user.role.value != "admin"
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this export batch",
            )

        return ExportBatchResponse(
            id=batch.id,
            batch_id=batch.batch_id,
            archive_path=batch.archive_path,
            storage_type=batch.storage_type,
            chunk_count=batch.chunk_count,
            file_size_bytes=batch.file_size_bytes,
            chunk_ids=batch.chunk_ids,
            status=batch.status,
            exported=batch.exported,
            error_message=batch.error_message,
            retry_count=batch.retry_count,
            checksum=batch.checksum,
            compression_level=batch.compression_level,
            format_version=batch.format_version,
            recording_id_range=batch.recording_id_range,
            language_stats=batch.language_stats,
            total_duration_seconds=batch.total_duration_seconds,
            filter_criteria=batch.filter_criteria,
            created_at=batch.created_at,
            completed_at=batch.completed_at,
            created_by_id=batch.created_by_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve export batch {batch_id}: {str(e)}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve export batch: {str(e)}",
        )


@router.get("/list", response_model=ExportBatchListResponse)
async def list_export_batches(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    date_from: Optional[datetime] = Query(None, description="Filter from this date"),
    date_to: Optional[datetime] = Query(None, description="Filter to this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    List export batches with pagination and filtering.

    This endpoint allows authenticated users to list export batches with optional
    filtering by status and date range. Users see only their own batches unless admin.

    **Required Permission:** Authenticated user

    **Query Parameters:**
    - status: Filter by batch status (pending, processing, completed, failed)
    - date_from: Filter batches created from this date
    - date_to: Filter batches created to this date
    - page: Page number (default: 1)
    - page_size: Number of batches per page (default: 50, max: 100)

    **Returns:**
    - Paginated list of export batches with total count
    """
    try:
        export_service = ExportBatchService(db)

        # Calculate skip for pagination
        skip = (page - 1) * page_size

        batches, total_count = export_service.list_export_batches(
            user_id=current_user.id if current_user.role.value != "admin" else None,
            status_filter=status_filter,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=page_size,
        )

        batch_responses = [
            ExportBatchResponse(
                id=batch.id,
                batch_id=batch.batch_id,
                archive_path=batch.archive_path,
                storage_type=batch.storage_type,
                chunk_count=batch.chunk_count,
                file_size_bytes=batch.file_size_bytes,
                chunk_ids=batch.chunk_ids,
                status=batch.status,
                exported=batch.exported,
                error_message=batch.error_message,
                retry_count=batch.retry_count,
                checksum=batch.checksum,
                compression_level=batch.compression_level,
                format_version=batch.format_version,
                recording_id_range=batch.recording_id_range,
                language_stats=batch.language_stats,
                total_duration_seconds=batch.total_duration_seconds,
                filter_criteria=batch.filter_criteria,
                created_at=batch.created_at,
                completed_at=batch.completed_at,
                created_by_id=batch.created_by_id,
            )
            for batch in batches
        ]

        return ExportBatchListResponse(
            batches=batch_responses,
            total_count=total_count,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        logger.error(f"Failed to list export batches: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list export batches: {str(e)}",
        )


@router.get("/{batch_id}/download")
async def download_export_batch(
    batch_id: str,
    http_request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Download an export batch archive.

    This endpoint allows authenticated users to download export batch archives.
    Downloads are subject to a daily limit (2 per developer per day) and rate limiting
    (10 per minute per IP). All downloads are logged for audit purposes.

    **Required Permission:** Authenticated user

    **Rate Limits:**
    - 2 downloads per developer per day
    - 10 downloads per minute per IP

    **Behavior:**
    - Checks daily download limit (2 per developer)
    - Records download in export_downloads table
    - For R2 storage: Generates temporary signed URL (1 hour expiry)
    - For local storage: Serves file directly with proper permissions
    - Logs download attempt with user ID, IP, and user agent

    **Returns:**
    - For local storage: File download response
    - For R2 storage: Redirect to signed URL or JSON with download URL
    """
    ip_address, user_agent = get_client_info(http_request)

    logger.info(
        f"Download requested for batch {batch_id} by user {current_user.id} "
        f"from IP {ip_address}"
    )

    try:
        export_service = ExportBatchService(db)

        # Check daily download limit
        can_download, reset_time = export_service.check_download_limit(current_user.id)
        if not can_download:
            downloads_today = export_service.get_user_download_count_today(
                current_user.id
            )
            logger.warning(
                f"Download limit exceeded for user {current_user.id}. "
                f"Downloads today: {downloads_today}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Daily download limit exceeded",
                    "downloads_today": downloads_today,
                    "daily_limit": settings.EXPORT_DAILY_DOWNLOAD_LIMIT,
                    "reset_time": reset_time.isoformat() if reset_time else None,
                },
            )

        # Download the batch (records download and returns file path or URL)
        result = export_service.download_export_batch(
            batch_id=batch_id,
            user_id=current_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        logger.info(
            f"Download successful for batch {batch_id} by user {current_user.id}"
        )

        # Handle different storage types
        if isinstance(result, dict) and "download_url" in result:
            # R2 storage - return signed URL
            return {
                "download_url": result["download_url"],
                "expires_in": result.get("expires_in", 3600),
                "batch_id": batch_id,
            }
        else:
            # Local storage - serve file directly
            file_path, mime_type = result
            return FileResponse(
                path=file_path,
                media_type=mime_type,
                filename=f"export_batch_{batch_id}.tar.zst",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Download failed for batch {batch_id} by user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}",
        )


@router.post("/{batch_id}/retry", response_model=ExportBatchResponse)
async def retry_export_batch(
    batch_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Retry a failed export batch.

    This endpoint allows administrators to retry failed export batches.
    The retry uses the existing batch_id for idempotency and attempts to
    resume from the failure point.

    **Required Permission:** admin role

    **Behavior:**
    - Verifies batch exists and is in failed status
    - Increments retry_count
    - Triggers export batch creation task with existing batch_id
    - Returns updated batch details

    **Returns:**
    - Updated export batch details with new status
    """
    logger.info(f"Retry requested for batch {batch_id} by admin {current_user.id}")

    try:
        export_service = ExportBatchService(db)

        # Get the batch
        batch = export_service.get_export_batch(batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Export batch {batch_id} not found",
            )

        # Verify batch is in failed status
        if batch.status != "failed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot retry batch with status '{batch.status}'. Only failed batches can be retried.",
            )

        # Retry the batch
        updated_batch = export_service.retry_export_batch(batch_id)

        logger.info(f"Batch {batch_id} retry initiated by admin {current_user.id}")

        return ExportBatchResponse(
            id=updated_batch.id,
            batch_id=updated_batch.batch_id,
            archive_path=updated_batch.archive_path,
            storage_type=updated_batch.storage_type,
            chunk_count=updated_batch.chunk_count,
            file_size_bytes=updated_batch.file_size_bytes,
            chunk_ids=updated_batch.chunk_ids,
            status=updated_batch.status,
            exported=updated_batch.exported,
            error_message=updated_batch.error_message,
            retry_count=updated_batch.retry_count,
            checksum=updated_batch.checksum,
            compression_level=updated_batch.compression_level,
            format_version=updated_batch.format_version,
            recording_id_range=updated_batch.recording_id_range,
            language_stats=updated_batch.language_stats,
            total_duration_seconds=updated_batch.total_duration_seconds,
            filter_criteria=updated_batch.filter_criteria,
            created_at=updated_batch.created_at,
            completed_at=updated_batch.completed_at,
            created_by_id=updated_batch.created_by_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retry batch {batch_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retry export batch: {str(e)}",
        )


@router.get("/download/quota", response_model=ExportDownloadQuotaResponse)
async def get_download_quota(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    Get user's remaining download quota for today.

    This endpoint allows authenticated users to check their remaining download
    quota for the current day. The quota resets daily at midnight UTC.

    **Required Permission:** Authenticated user

    **Returns:**
    - downloads_today: Number of downloads used today
    - downloads_remaining: Number of downloads remaining today
    - daily_limit: Total daily download limit
    - reset_time: When the quota resets (midnight UTC)
    """
    try:
        export_service = ExportBatchService(db)

        downloads_today = export_service.get_user_download_count_today(current_user.id)
        daily_limit = settings.EXPORT_DAILY_DOWNLOAD_LIMIT
        downloads_remaining = max(0, daily_limit - downloads_today)

        # Calculate next reset time (midnight UTC)
        now = datetime.now(timezone.utc)
        reset_time = datetime(
            now.year, now.month, now.day, tzinfo=timezone.utc
        ).replace(hour=0, minute=0, second=0, microsecond=0)

        # If we're already past midnight, add one day
        from datetime import timedelta

        if now >= reset_time:
            reset_time += timedelta(days=1)

        return ExportDownloadQuotaResponse(
            downloads_today=downloads_today,
            downloads_remaining=downloads_remaining,
            daily_limit=daily_limit,
            reset_time=reset_time,
        )

    except Exception as e:
        logger.error(
            f"Failed to get download quota for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download quota: {str(e)}",
        )
