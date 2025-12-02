"""
Admin endpoints for consensus and R2 monitoring.

These endpoints provide administrative control over consensus calculation
and monitoring of R2 storage usage.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_admin
from app.core.export_metrics import (
    consensus_metrics_collector,
    export_metrics_collector,
    r2_metrics_collector,
)
from app.core.logging_config import get_logger
from app.db.database import get_db
from app.models.audio_chunk import AudioChunk
from app.models.export_batch import ExportBatch, ExportBatchStatus, StorageType
from app.models.export_download import ExportDownload
from app.models.user import User
from app.schemas.admin import (
    AdminConsensusCalculateRequest,
    AdminConsensusCalculateResponse,
    AdminConsensusReviewQueueItem,
    AdminConsensusReviewQueueResponse,
    AdminConsensusStatsResponse,
    AdminR2LimitsResponse,
    AdminR2UsageResponse,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/admin", tags=["admin-consensus"])


@router.post("/consensus/calculate", response_model=AdminConsensusCalculateResponse)
async def trigger_consensus_calculation(
    request: AdminConsensusCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Trigger consensus calculation for specific chunks.

    This endpoint allows admins to manually trigger consensus calculation
    for a list of chunk IDs. The calculation is performed asynchronously
    via Celery tasks.

    **Requirements**: Admin role

    **Returns**: Task IDs for tracking the consensus calculation jobs
    """
    logger.info(
        f"Admin {current_user.id} triggering consensus calculation for {len(request.chunk_ids)} chunks"
    )

    if not request.chunk_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chunk_ids list cannot be empty",
        )

    if len(request.chunk_ids) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot process more than 1000 chunks at once",
        )

    # Verify chunks exist
    existing_chunks = (
        db.query(AudioChunk.id).filter(AudioChunk.id.in_(request.chunk_ids)).all()
    )

    existing_chunk_ids = [chunk.id for chunk in existing_chunks]

    if len(existing_chunk_ids) != len(request.chunk_ids):
        missing_ids = set(request.chunk_ids) - set(existing_chunk_ids)
        logger.warning(f"Some chunk IDs not found: {missing_ids}")

    if not existing_chunk_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No valid chunks found"
        )

    # Trigger consensus calculation tasks
    from app.tasks.export_optimization import calculate_consensus_for_chunks_export

    # Split into batches of 100 for better task distribution
    batch_size = 100
    task_ids = []

    for i in range(0, len(existing_chunk_ids), batch_size):
        batch = existing_chunk_ids[i : i + batch_size]
        task = calculate_consensus_for_chunks_export.delay(batch)
        task_ids.append(task.id)
        logger.info(f"Queued consensus task {task.id} for {len(batch)} chunks")

    return AdminConsensusCalculateResponse(
        task_ids=task_ids,
        chunk_count=len(existing_chunk_ids),
        message=f"Consensus calculation queued for {len(existing_chunk_ids)} chunks in {len(task_ids)} tasks",
    )


@router.get("/consensus/stats", response_model=AdminConsensusStatsResponse)
async def get_consensus_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """
    Get consensus statistics.

    Returns comprehensive statistics about consensus calculation including:
    - Success rates
    - Average quality scores
    - Distribution of transcript counts
    - Chunks ready for export

    **Requirements**: Admin role
    """
    logger.info(f"Admin {current_user.id} requesting consensus statistics")

    # Total chunks
    total_chunks = db.query(func.count(AudioChunk.id)).scalar() or 0

    # Chunks with transcriptions (transcript_count > 0)
    chunks_with_transcriptions = (
        db.query(func.count(AudioChunk.id))
        .filter(AudioChunk.transcript_count > 0)
        .scalar()
        or 0
    )

    # Chunks ready for export
    chunks_ready_for_export = (
        db.query(func.count(AudioChunk.id))
        .filter(AudioChunk.ready_for_export == True)
        .scalar()
        or 0
    )

    # Chunks pending consensus (have transcriptions but not ready)
    chunks_pending_consensus = (
        db.query(func.count(AudioChunk.id))
        .filter(
            and_(AudioChunk.transcript_count > 0, AudioChunk.ready_for_export == False)
        )
        .scalar()
        or 0
    )

    # Chunks with failed consensus (consensus_failed_count >= 3)
    chunks_failed_consensus = (
        db.query(func.count(AudioChunk.id))
        .filter(AudioChunk.consensus_failed_count >= 3)
        .scalar()
        or 0
    )

    # Average consensus quality (for chunks with quality > 0)
    avg_consensus_quality = (
        db.query(func.avg(AudioChunk.consensus_quality))
        .filter(AudioChunk.consensus_quality > 0)
        .scalar()
        or 0.0
    )

    # Average transcript count (for chunks with transcriptions)
    avg_transcript_count = (
        db.query(func.avg(AudioChunk.transcript_count))
        .filter(AudioChunk.transcript_count > 0)
        .scalar()
        or 0.0
    )

    # Consensus success rate (ready / with_transcriptions)
    consensus_success_rate = (
        (chunks_ready_for_export / chunks_with_transcriptions * 100)
        if chunks_with_transcriptions > 0
        else 0.0
    )

    # Distribution of transcript counts
    transcript_count_distribution = (
        db.query(AudioChunk.transcript_count, func.count(AudioChunk.id).label("count"))
        .filter(AudioChunk.transcript_count > 0)
        .group_by(AudioChunk.transcript_count)
        .order_by(AudioChunk.transcript_count)
        .all()
    )

    chunks_by_transcript_count = {
        f"{row.transcript_count} transcripts": row.count
        for row in transcript_count_distribution
    }

    return AdminConsensusStatsResponse(
        total_chunks=total_chunks,
        chunks_with_transcriptions=chunks_with_transcriptions,
        chunks_ready_for_export=chunks_ready_for_export,
        chunks_pending_consensus=chunks_pending_consensus,
        chunks_failed_consensus=chunks_failed_consensus,
        average_consensus_quality=round(float(avg_consensus_quality), 3),
        average_transcript_count=round(float(avg_transcript_count), 2),
        consensus_success_rate=round(consensus_success_rate, 2),
        chunks_by_transcript_count=chunks_by_transcript_count,
    )


@router.get("/consensus/review-queue", response_model=AdminConsensusReviewQueueResponse)
async def get_consensus_review_queue(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get chunks requiring manual review.

    Returns chunks with consensus_failed_count >= 3, indicating repeated
    failures in automatic consensus calculation. These chunks need manual
    review to determine the correct consensus transcript.

    **Requirements**: Admin role

    **Pagination**: Use page and page_size query parameters
    """
    logger.info(
        f"Admin {current_user.id} requesting consensus review queue (page {page})"
    )

    # Query chunks with consensus_failed_count >= 3
    query = (
        db.query(AudioChunk)
        .filter(AudioChunk.consensus_failed_count >= 3)
        .order_by(AudioChunk.consensus_failed_count.desc(), AudioChunk.created_at.asc())
    )

    # Get total count
    total_count = query.count()

    # Apply pagination
    skip = (page - 1) * page_size
    chunks = query.offset(skip).limit(page_size).all()

    # Convert to response items
    items = [
        AdminConsensusReviewQueueItem(
            chunk_id=chunk.id,
            recording_id=chunk.recording_id,
            transcript_count=chunk.transcript_count,
            consensus_failed_count=chunk.consensus_failed_count,
            consensus_quality=chunk.consensus_quality,
            ready_for_export=chunk.ready_for_export,
            created_at=chunk.created_at,
            file_path=chunk.file_path,
        )
        for chunk in chunks
    ]

    return AdminConsensusReviewQueueResponse(
        items=items, total_count=total_count, page=page, page_size=page_size
    )


@router.get("/r2/usage", response_model=AdminR2UsageResponse)
async def get_r2_usage_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """
    Get current R2 usage statistics.

    Returns detailed information about R2 storage usage including:
    - Class A operations (uploads) this month
    - Class B operations (downloads) this month
    - Total storage used
    - Remaining quota for each metric

    **Requirements**: Admin role
    """
    logger.info(f"Admin {current_user.id} requesting R2 usage statistics")

    # Get current month boundaries
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Calculate month end (first day of next month)
    if now.month == 12:
        month_end = now.replace(
            year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
    else:
        month_end = now.replace(
            month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

    # Count Class A operations (uploads) this month
    class_a_count = (
        db.query(func.count(ExportBatch.id))
        .filter(
            and_(
                ExportBatch.storage_type == StorageType.R2,
                ExportBatch.status == ExportBatchStatus.COMPLETED,
                ExportBatch.created_at >= month_start,
            )
        )
        .scalar()
        or 0
    )

    # Count Class B operations (downloads) this month
    class_b_count = (
        db.query(func.count(ExportDownload.id))
        .filter(ExportDownload.downloaded_at >= month_start)
        .scalar()
        or 0
    )

    # Calculate total storage used (sum of all completed R2 batch file sizes)
    total_storage_bytes = (
        db.query(func.sum(ExportBatch.file_size_bytes))
        .filter(
            and_(
                ExportBatch.storage_type == StorageType.R2,
                ExportBatch.status == ExportBatchStatus.COMPLETED,
            )
        )
        .scalar()
        or 0
    )

    storage_used_gb = total_storage_bytes / (1024**3)

    # Get limits from settings
    class_a_limit = settings.R2_FREE_TIER_CLASS_A_MONTHLY
    class_b_limit = settings.R2_FREE_TIER_CLASS_B_MONTHLY
    storage_limit_gb = settings.R2_FREE_TIER_STORAGE_GB

    # Calculate usage percentages
    class_a_usage_pct = (
        (class_a_count / class_a_limit * 100) if class_a_limit > 0 else 0.0
    )
    class_b_usage_pct = (
        (class_b_count / class_b_limit * 100) if class_b_limit > 0 else 0.0
    )
    storage_usage_pct = (
        (storage_used_gb / storage_limit_gb * 100) if storage_limit_gb > 0 else 0.0
    )

    return AdminR2UsageResponse(
        class_a_operations_this_month=class_a_count,
        class_a_operations_limit=class_a_limit,
        class_a_usage_percentage=round(class_a_usage_pct, 2),
        class_b_operations_this_month=class_b_count,
        class_b_operations_limit=class_b_limit,
        class_b_usage_percentage=round(class_b_usage_pct, 2),
        storage_used_gb=round(storage_used_gb, 2),
        storage_limit_gb=storage_limit_gb,
        storage_usage_percentage=round(storage_usage_pct, 2),
        month_start=month_start,
        month_end=month_end,
    )


@router.get("/r2/limits", response_model=AdminR2LimitsResponse)
async def get_r2_limits(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """
    Get R2 free tier limits and current usage.

    Returns free tier limits and calculates remaining quota for each metric.
    Also indicates if any limits are being approached (>80% usage).

    **Requirements**: Admin role
    """
    logger.info(f"Admin {current_user.id} requesting R2 limits")

    # Get current month boundaries
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Count Class A operations (uploads) this month
    class_a_count = (
        db.query(func.count(ExportBatch.id))
        .filter(
            and_(
                ExportBatch.storage_type == StorageType.R2,
                ExportBatch.status == ExportBatchStatus.COMPLETED,
                ExportBatch.created_at >= month_start,
            )
        )
        .scalar()
        or 0
    )

    # Count Class B operations (downloads) this month
    class_b_count = (
        db.query(func.count(ExportDownload.id))
        .filter(ExportDownload.downloaded_at >= month_start)
        .scalar()
        or 0
    )

    # Calculate total storage used
    total_storage_bytes = (
        db.query(func.sum(ExportBatch.file_size_bytes))
        .filter(
            and_(
                ExportBatch.storage_type == StorageType.R2,
                ExportBatch.status == ExportBatchStatus.COMPLETED,
            )
        )
        .scalar()
        or 0
    )

    storage_used_gb = total_storage_bytes / (1024**3)

    # Get limits from settings
    class_a_limit = settings.R2_FREE_TIER_CLASS_A_MONTHLY
    class_b_limit = settings.R2_FREE_TIER_CLASS_B_MONTHLY
    storage_limit_gb = settings.R2_FREE_TIER_STORAGE_GB

    # Calculate remaining quota
    class_a_remaining = max(0, class_a_limit - class_a_count)
    class_b_remaining = max(0, class_b_limit - class_b_count)
    storage_remaining_gb = max(0.0, storage_limit_gb - storage_used_gb)

    # Check if approaching limits (>80%)
    class_a_usage_pct = (
        (class_a_count / class_a_limit * 100) if class_a_limit > 0 else 0.0
    )
    class_b_usage_pct = (
        (class_b_count / class_b_limit * 100) if class_b_limit > 0 else 0.0
    )
    storage_usage_pct = (
        (storage_used_gb / storage_limit_gb * 100) if storage_limit_gb > 0 else 0.0
    )

    approaching_limits = False
    limit_warnings = []

    if class_a_usage_pct > 80:
        approaching_limits = True
        limit_warnings.append(
            f"Class A operations at {class_a_usage_pct:.1f}% of limit"
        )

    if class_b_usage_pct > 80:
        approaching_limits = True
        limit_warnings.append(
            f"Class B operations at {class_b_usage_pct:.1f}% of limit"
        )

    if storage_usage_pct > 80:
        approaching_limits = True
        limit_warnings.append(f"Storage at {storage_usage_pct:.1f}% of limit")

    return AdminR2LimitsResponse(
        free_tier_enabled=settings.R2_ENABLE_FREE_TIER_GUARD,
        class_a_limit=class_a_limit,
        class_b_limit=class_b_limit,
        storage_limit_gb=storage_limit_gb,
        class_a_remaining=class_a_remaining,
        class_b_remaining=class_b_remaining,
        storage_remaining_gb=round(storage_remaining_gb, 2),
        approaching_limits=approaching_limits,
        limit_warnings=limit_warnings,
    )


@router.get("/metrics/export")
async def get_export_metrics(current_user: User = Depends(require_admin)):
    """
    Get export operation metrics.

    Returns comprehensive metrics about export batch creation, failures,
    and overall export performance.

    **Requirements**: Admin role
    """
    logger.info(f"Admin {current_user.id} requesting export metrics")

    metrics = export_metrics_collector.get_export_metrics()

    return {
        "total_batches_created": metrics.total_batches_created,
        "total_batches_failed": metrics.total_batches_failed,
        "total_chunks_exported": metrics.total_chunks_exported,
        "total_batches_today": metrics.total_batches_today,
        "total_batches_this_week": metrics.total_batches_this_week,
        "total_batches_this_month": metrics.total_batches_this_month,
        "average_batch_size": metrics.average_batch_size,
        "average_batch_creation_time": metrics.average_batch_creation_time,
        "last_batch_created_at": metrics.last_batch_created_at,
        "last_batch_failed_at": metrics.last_batch_failed_at,
        "success_rate": round(
            (
                (
                    metrics.total_batches_created
                    / (metrics.total_batches_created + metrics.total_batches_failed)
                    * 100
                )
                if (metrics.total_batches_created + metrics.total_batches_failed) > 0
                else 0.0
            ),
            2,
        ),
    }


@router.get("/metrics/consensus")
async def get_consensus_metrics(current_user: User = Depends(require_admin)):
    """
    Get consensus calculation metrics.

    Returns comprehensive metrics about consensus calculations, success rates,
    and quality scores.

    **Requirements**: Admin role
    """
    logger.info(f"Admin {current_user.id} requesting consensus metrics")

    metrics = consensus_metrics_collector.get_consensus_metrics()

    return {
        "total_calculations": metrics.total_calculations,
        "total_calculations_today": metrics.total_calculations_today,
        "total_calculations_this_hour": metrics.total_calculations_this_hour,
        "total_failed": metrics.total_failed,
        "total_ready_for_export": metrics.total_ready_for_export,
        "success_rate": metrics.success_rate,
        "average_quality_score": metrics.average_quality_score,
        "average_calculation_time": metrics.average_calculation_time,
        "chunks_in_review_queue": metrics.chunks_in_review_queue,
    }


@router.get("/metrics/r2")
async def get_r2_metrics(current_user: User = Depends(require_admin)):
    """
    Get R2 usage metrics.

    Returns comprehensive metrics about R2 operations and storage usage,
    including usage percentages against free tier limits.

    **Requirements**: Admin role
    """
    logger.info(f"Admin {current_user.id} requesting R2 metrics")

    metrics = r2_metrics_collector.get_r2_metrics()

    return {
        "class_a_operations_today": metrics.class_a_operations_today,
        "class_a_operations_this_month": metrics.class_a_operations_this_month,
        "class_b_operations_today": metrics.class_b_operations_today,
        "class_b_operations_this_month": metrics.class_b_operations_this_month,
        "storage_used_gb": metrics.storage_used_gb,
        "class_a_limit": metrics.class_a_limit,
        "class_b_limit": metrics.class_b_limit,
        "storage_limit_gb": metrics.storage_limit_gb,
        "class_a_usage_percent": metrics.class_a_usage_percent,
        "class_b_usage_percent": metrics.class_b_usage_percent,
        "storage_usage_percent": metrics.storage_usage_percent,
        "approaching_limits": (
            metrics.class_a_usage_percent > 80
            or metrics.class_b_usage_percent > 80
            or metrics.storage_usage_percent > 80
        ),
    }


@router.get("/alerts")
async def get_export_alerts(
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of alerts to return"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get recent export-related alerts.

    Returns alerts for export batch failures, R2 usage, consensus failures,
    and export backlog issues.

    **Requirements**: Admin role
    """
    logger.info(f"Admin {current_user.id} requesting export alerts")

    from app.core.export_alerts import ExportAlerting

    alerting = ExportAlerting(db)
    recent_alerts = alerting.get_recent_alerts(limit=limit)

    return {"alerts": recent_alerts, "count": len(recent_alerts)}


@router.post("/alerts/check")
async def check_export_alerts(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """
    Manually trigger alert checking.

    Checks all alert conditions and returns any active alerts.
    This is useful for testing alert rules or getting immediate feedback.

    **Requirements**: Admin role
    """
    logger.info(f"Admin {current_user.id} manually triggering alert check")

    from app.core.export_alerts import ExportAlerting

    alerting = ExportAlerting(db)
    active_alerts = alerting.check_all_alerts()

    return {
        "alerts": [
            {
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "component": alert.component,
                "timestamp": alert.timestamp.isoformat(),
                "metrics": alert.metrics,
                "action_required": alert.action_required,
            }
            for alert in active_alerts
        ],
        "count": len(active_alerts),
    }
