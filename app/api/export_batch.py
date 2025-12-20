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
    require_admin_or_sworik,
)
from app.core.exceptions import ValidationError
from app.db.database import get_db
from app.models.export_batch import ExportBatch, ExportBatchStatus
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
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db),
):
    """
    Create a new export batch from ready chunks.

    This endpoint allows users to create export batches with optional filtering criteria.
    The batch will include up to 200 chunks that meet the specified criteria and have not
    been previously exported.

    **Required Permission:** sworik_developer role (or admin)

    **Business Rules:**
    - Sworik developers: Minimum 50 chunks required (configurable via EXPORT_MIN_CHUNKS_SWORIK_DEVELOPER)
    - Admins: Minimum 10 chunks required (configurable via EXPORT_MIN_CHUNKS_ADMIN)
    - force_create: Admin-only override to create batch with any chunk count

    **Request Body:**
    - date_from: Filter chunks created from this date
    - date_to: Filter chunks created to this date
    - min_duration: Minimum chunk duration in seconds
    - max_duration: Maximum chunk duration in seconds
    - force_create: Admin-only override to create batch with any available chunk count

    **Enhanced Error Responses:**
    - 400: Structured error with context and actionable suggestions
    - 500: System error with user-friendly message

    **Returns:**
    - Export batch details including batch_id, chunk_count, filter_criteria, and status
    """
    ip_address, user_agent = get_client_info(http_request)

    logger.info(
        f"Export batch creation requested by user {current_user.id} (role: {current_user.role.value}) "
        f"from IP {ip_address} with filters: {request_body.dict()}"
    )

    try:
        export_service = ExportBatchService(db)

        # Pass user role to service layer for role-based logic
        batch = export_service.create_export_batch(
            max_chunks=200,
            user_id=current_user.id,
            user_role=current_user.role,  # Pass user role
            date_from=request_body.date_from,
            date_to=request_body.date_to,
            min_duration=request_body.min_duration,
            max_duration=request_body.max_duration,
            force_create=request_body.force_create,
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

    except ValidationError as e:
        # Handle insufficient chunks error with structured response
        error_message = str(e)
        logger.warning(
            f"Export batch creation failed for user {current_user.id}: {error_message}"
        )

        # Parse error details from service layer
        # The service layer includes structured error information in the exception message
        if "Insufficient chunks for batch creation" in error_message:
            # Extract details from error message or query current state
            try:
                # Get current chunk count for better error context
                from sqlalchemy import func

                from app.models.audio_chunk import AudioChunk

                # Get completed batch chunk IDs (same logic as service)
                completed_batches = (
                    db.query(ExportBatch.chunk_ids)
                    .filter(ExportBatch.status == ExportBatchStatus.COMPLETED)
                    .all()
                )

                exported_chunk_ids = set()
                for batch in completed_batches:
                    if batch.chunk_ids:
                        exported_chunk_ids.update(batch.chunk_ids)

                # Count available chunks with same filters as service
                query = db.query(func.count(AudioChunk.id)).filter(
                    AudioChunk.ready_for_export == True
                )

                if exported_chunk_ids:
                    query = query.filter(~AudioChunk.id.in_(exported_chunk_ids))

                if request_body.date_from:
                    query = query.filter(
                        AudioChunk.created_at >= request_body.date_from
                    )
                if request_body.date_to:
                    query = query.filter(AudioChunk.created_at <= request_body.date_to)
                if request_body.min_duration is not None:
                    query = query.filter(
                        AudioChunk.duration >= request_body.min_duration
                    )
                if request_body.max_duration is not None:
                    query = query.filter(
                        AudioChunk.duration <= request_body.max_duration
                    )

                available_chunks = query.scalar() or 0
                required_chunks = settings.get_min_chunks_for_role(
                    current_user.role.value
                )

                # Generate role-specific suggestions
                suggestions = []
                if current_user.role.value == "sworik_developer":
                    suggestions.extend(
                        [
                            "Wait for more chunks to be processed (check back in a few hours)",
                            "Contact an admin who can create batches with as few as 10 chunks",
                            "Try adjusting your date range or duration filters to find more chunks",
                        ]
                    )
                elif current_user.role.value == "admin":
                    suggestions.extend(
                        [
                            "Wait for more chunks to be processed",
                            "Try adjusting your date range or duration filters",
                            "Use force_create=true to create a batch with any available chunk count",
                        ]
                    )

                # Create structured error response
                error_details = {
                    "error": "Insufficient chunks for batch creation",
                    "details": {
                        "available_chunks": available_chunks,
                        "required_chunks": required_chunks,
                        "user_role": current_user.role.value,
                        "suggestions": suggestions,
                    },
                }

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=error_details
                )

            except Exception as parse_error:
                logger.error(
                    f"Error parsing insufficient chunks details: {parse_error}"
                )
                # Fallback to simple error message
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "Insufficient chunks for batch creation",
                        "details": {
                            "user_role": current_user.role.value,
                            "suggestions": [
                                "Wait for more chunks to be processed",
                                "Contact an admin if you need urgent access",
                                "Try adjusting your filters to find more chunks",
                            ],
                        },
                    },
                )
        else:
            # Other validation errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": error_message,
                    "details": {
                        "user_role": current_user.role.value,
                        "suggestions": [
                            "Check your request parameters",
                            "Contact support if the issue persists",
                        ],
                    },
                },
            )

    except Exception as e:
        logger.error(
            f"Export batch creation failed for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Export batch creation failed",
                "details": {
                    "suggestions": [
                        "Try again in a few minutes",
                        "Contact support if the issue persists",
                    ]
                },
            },
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
    Downloads are subject to role-based daily limits and rate limiting.
    All downloads are logged for audit purposes.

    **Required Permission:** Authenticated user

    **Role-based Rate Limits:**
    - Sworik developers: 5 downloads per day (configurable via EXPORT_DAILY_DOWNLOAD_LIMIT_SWORIK_DEVELOPER)
    - Admins: Unlimited downloads (configurable via EXPORT_DAILY_DOWNLOAD_LIMIT_ADMIN)

    **Enhanced Error Responses:**
    - 429: Quota exceeded with detailed information and reset time
    - 404: Batch not found or not ready for download
    - 500: System error with user-friendly message

    **Returns:**
    - For local storage: File download response
    - For R2 storage: JSON with download URL and expiry
    """
    ip_address, user_agent = get_client_info(http_request)

    logger.info(
        f"Download requested for batch {batch_id} by user {current_user.id} ({current_user.role.value}) "
        f"from IP {ip_address}"
    )

    try:
        export_service = ExportBatchService(db)

        # Download the batch with role-based quota checking
        result = export_service.download_export_batch(
            batch_id=batch_id,
            user_id=current_user.id,
            user_role=current_user.role,  # Pass user role
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

    except ValidationError as e:
        error_message = str(e)
        logger.warning(
            f"Download failed for batch {batch_id} by user {current_user.id}: {error_message}"
        )

        # Handle specific error types with structured responses
        if "Daily download limit exceeded" in error_message:
            # Parse quota information from error message or get current state
            try:
                # Get current quota information
                can_download, reset_time, downloads_today, daily_limit = (
                    export_service.check_download_limit(
                        current_user.id, current_user.role
                    )
                )

                # Calculate hours until reset
                now = datetime.now(timezone.utc)
                hours_until_reset = 0
                if reset_time:
                    hours_until_reset = max(
                        0, int((reset_time - now).total_seconds() / 3600)
                    )

                # Generate role-specific suggestions
                suggestions = []
                if current_user.role.value == "sworik_developer":
                    suggestions.extend(
                        [
                            f"Wait until midnight UTC when your quota resets (in {hours_until_reset} hours)",
                            "Contact an admin if you need urgent access to more downloads",
                        ]
                    )
                elif current_user.role.value == "admin":
                    suggestions.extend(
                        ["This should not happen for admin users - contact support"]
                    )

                error_details = {
                    "error": "Daily download limit exceeded",
                    "details": {
                        "downloads_today": downloads_today,
                        "daily_limit": daily_limit,
                        "reset_time": reset_time.isoformat() if reset_time else None,
                        "hours_until_reset": hours_until_reset,
                        "user_role": current_user.role.value,
                        "suggestions": suggestions,
                    },
                }

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=error_details
                )

            except Exception as parse_error:
                logger.error(f"Error parsing quota exceeded details: {parse_error}")
                # Fallback error response
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Daily download limit exceeded",
                        "details": {
                            "user_role": current_user.role.value,
                            "suggestions": [
                                "Wait until midnight UTC when your quota resets",
                                "Contact an admin if you need urgent access",
                            ],
                        },
                    },
                )

        elif "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": f"Export batch {batch_id} not found",
                    "details": {
                        "suggestions": [
                            "Check the batch ID is correct",
                            "Verify the batch exists in your batch list",
                            "Contact support if you believe this is an error",
                        ]
                    },
                },
            )

        elif "not ready for download" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": f"Export batch {batch_id} is not ready for download",
                    "details": {
                        "suggestions": [
                            "Wait for the batch to complete processing",
                            "Check the batch status in your batch list",
                            "Contact support if the batch appears stuck",
                        ]
                    },
                },
            )
        else:
            # Other validation errors
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": error_message,
                    "details": {
                        "suggestions": [
                            "Check your request parameters",
                            "Contact support if the issue persists",
                        ]
                    },
                },
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
            detail={
                "error": "Download failed due to system error",
                "details": {
                    "suggestions": [
                        "Try again in a few minutes",
                        "Contact support if the issue persists",
                    ]
                },
            },
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
    Get user's remaining download quota for today based on their role.

    This endpoint allows authenticated users to check their remaining download
    quota for the current day. The quota resets daily at midnight UTC.

    **Required Permission:** Authenticated user

    **Role-based Quotas:**
    - Sworik developers: Configurable limit (default: 5 per day)
    - Admins: Unlimited downloads (daily_limit = -1)

    **Returns:**
    - downloads_today: Number of downloads used today
    - downloads_remaining: Number of downloads remaining today (-1 for unlimited)
    - daily_limit: Total daily download limit (-1 for unlimited)
    - reset_time: When the quota resets (midnight UTC), null for unlimited
    """
    try:
        export_service = ExportBatchService(db)

        # Get role-based quota information
        can_download, reset_time, downloads_today, daily_limit = (
            export_service.check_download_limit(current_user.id, current_user.role)
        )

        # Calculate downloads remaining
        if daily_limit == -1:
            # Unlimited downloads for admins
            downloads_remaining = -1
        else:
            downloads_remaining = max(0, daily_limit - downloads_today)

        logger.info(
            f"Quota check for user {current_user.id} ({current_user.role.value}): "
            f"{downloads_today}/{daily_limit} used, {downloads_remaining} remaining"
        )

        return ExportDownloadQuotaResponse(
            downloads_today=downloads_today,
            downloads_remaining=downloads_remaining,
            daily_limit=daily_limit,
            reset_time=reset_time,  # None for unlimited quota
            user_role=current_user.role.value,
            is_unlimited=(daily_limit == -1),
        )

    except Exception as e:
        logger.error(
            f"Failed to get download quota for user {current_user.id}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to get download quota",
                "details": {
                    "suggestions": [
                        "Try again in a few minutes",
                        "Contact support if the issue persists",
                    ]
                },
            },
        )
