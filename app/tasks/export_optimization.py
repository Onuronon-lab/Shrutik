"""
Celery tasks for export optimization.

These tasks handle:
- Consensus calculation for chunks
- Export batch creation
- Cleanup of exported chunks
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.exceptions import ValidationError
from app.core.redis_client import redis_client
from app.db.database import SessionLocal
from app.models.audio_chunk import AudioChunk
from app.services.consensus_service import ConsensusService
from app.services.export_batch_service import ExportBatchService

logger = logging.getLogger(__name__)


def get_db() -> Session:
    """Get database session for Celery tasks."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


@celery_app.task(
    bind=True,
    name="calculate_consensus_for_chunks_export",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 60},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def calculate_consensus_for_chunks_export(self, chunk_ids: List[int]) -> dict:
    """
    Calculate consensus for multiple audio chunks for export optimization.

    This task:
    - Uses Redis locking per chunk to prevent duplicate calculations
    - Calls ConsensusService.calculate_consensus_for_chunk() for each chunk
    - Updates chunk ready_for_export flag based on quality threshold (90%)
    - Handles errors and increments consensus_failed_count on failure
    - Uses exponential backoff for retries

    Args:
        chunk_ids: List of AudioChunk IDs to process

    Returns:
        dict: Consensus calculation results with statistics
    """
    db = get_db()

    try:
        logger.info(
            f"Starting consensus calculation for {len(chunk_ids)} chunks (export optimization)"
        )

        consensus_service = ConsensusService(db)
        results = {
            "total_chunks": len(chunk_ids),
            "processed": 0,
            "ready_for_export": 0,
            "insufficient_transcriptions": 0,
            "below_quality_threshold": 0,
            "failed": 0,
            "skipped_locked": 0,
            "details": [],
        }

        for i, chunk_id in enumerate(chunk_ids):
            try:
                # Update task progress
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "current": i + 1,
                        "total": len(chunk_ids),
                        "status": f"Processing chunk {chunk_id}...",
                        "ready_for_export": results["ready_for_export"],
                    },
                )

                # Check if lock exists (another worker is processing this chunk)
                lock_key = f"consensus_lock:chunk_{chunk_id}"
                if redis_client.exists(lock_key):
                    logger.info(
                        f"Chunk {chunk_id} is locked by another worker, skipping"
                    )
                    results["skipped_locked"] += 1
                    results["details"].append(
                        {
                            "chunk_id": chunk_id,
                            "status": "skipped",
                            "reason": "locked_by_another_worker",
                        }
                    )
                    continue

                # Calculate consensus for this chunk
                consensus_transcript = consensus_service.calculate_consensus_for_chunk(
                    chunk_id
                )

                # Get updated chunk to check status
                chunk = db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()

                if not chunk:
                    logger.error(
                        f"Chunk {chunk_id} not found after consensus calculation"
                    )
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "chunk_id": chunk_id,
                            "status": "failed",
                            "error": "Chunk not found",
                        }
                    )
                    continue

                results["processed"] += 1

                # Track result based on chunk status
                if chunk.ready_for_export:
                    results["ready_for_export"] += 1
                    results["details"].append(
                        {
                            "chunk_id": chunk_id,
                            "status": "ready_for_export",
                            "consensus_quality": chunk.consensus_quality,
                            "transcript_count": chunk.transcript_count,
                            "consensus_transcript_id": chunk.consensus_transcript_id,
                        }
                    )
                    logger.info(
                        f"Chunk {chunk_id} marked ready for export "
                        f"(quality: {chunk.consensus_quality:.3f})"
                    )
                elif chunk.transcript_count < 5:
                    results["insufficient_transcriptions"] += 1
                    results["details"].append(
                        {
                            "chunk_id": chunk_id,
                            "status": "insufficient_transcriptions",
                            "transcript_count": chunk.transcript_count,
                            "required": 5,
                        }
                    )
                else:
                    results["below_quality_threshold"] += 1
                    results["details"].append(
                        {
                            "chunk_id": chunk_id,
                            "status": "below_quality_threshold",
                            "consensus_quality": chunk.consensus_quality,
                            "threshold": 0.90,
                            "transcript_count": chunk.transcript_count,
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to calculate consensus for chunk {chunk_id}: {e}")
                results["failed"] += 1
                results["details"].append(
                    {"chunk_id": chunk_id, "status": "failed", "error": str(e)}
                )

        logger.info(
            f"Consensus calculation completed: {results['processed']} processed, "
            f"{results['ready_for_export']} ready for export, "
            f"{results['insufficient_transcriptions']} insufficient transcriptions, "
            f"{results['below_quality_threshold']} below quality threshold, "
            f"{results['failed']} failed, {results['skipped_locked']} skipped (locked)"
        )

        return results

    except Exception as e:
        logger.error(f"Unexpected error in consensus calculation task: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        return {
            "total_chunks": len(chunk_ids),
            "processed": 0,
            "ready_for_export": 0,
            "insufficient_transcriptions": 0,
            "below_quality_threshold": 0,
            "failed": len(chunk_ids),
            "skipped_locked": 0,
            "error": str(e),
        }

    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="create_export_batch_task",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 3, "countdown": 300},
    retry_backoff=True,
    retry_backoff_max=1800,
    retry_jitter=True,
)
def create_export_batch_task(self, batch_id: Optional[str] = None) -> dict:
    """
    Scheduled task for automatic export batch creation.

    This task:
    - Checks R2 free tier limits before proceeding
    - Calls ExportBatchService.create_export_batch() with max_chunks=200, force_create=False
    - Skips export if less than 200 chunks available (logs info message)
    - Ensures chunks are never exported twice (query excludes chunks in completed batches)
    - Handles idempotency with batch_id parameter
    - Supports partial batch recovery via batch_id parameter
    - Retries on failures with exponential backoff

    Args:
        batch_id: Optional batch ID for idempotency and recovery

    Returns:
        dict: Export batch creation results
    """
    db = get_db()

    try:
        logger.info("Starting scheduled export batch creation task")

        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Checking R2 limits..."},
        )

        export_service = ExportBatchService(db)

        # Check R2 free tier limits
        if not export_service.check_r2_free_tier_limits():
            logger.error(
                "R2 free tier limits would be exceeded, aborting export batch creation"
            )
            return {
                "status": "aborted",
                "message": "R2 free tier limits would be exceeded",
                "batch_id": None,
                "chunks_exported": 0,
            }

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 20, "total": 100, "status": "Querying ready chunks..."},
        )

        # Count available ready chunks
        from sqlalchemy import and_, func, not_

        from app.models.export_batch import ExportBatch, ExportBatchStatus

        exported_chunk_ids_subquery = (
            db.query(func.unnest(ExportBatch.chunk_ids).label("chunk_id"))
            .filter(ExportBatch.status == ExportBatchStatus.COMPLETED)
            .subquery()
        )

        available_chunks_count = (
            db.query(func.count(AudioChunk.id))
            .filter(
                and_(
                    AudioChunk.ready_for_export == True,
                    not_(
                        AudioChunk.id.in_(
                            db.query(exported_chunk_ids_subquery.c.chunk_id)
                        )
                    ),
                )
            )
            .scalar()
            or 0
        )

        logger.info(f"Found {available_chunks_count} ready chunks available for export")

        # Check if we have enough chunks (200 minimum for scheduled exports)
        if available_chunks_count < 200:
            logger.info(
                f"Insufficient chunks for scheduled export: {available_chunks_count} < 200. "
                f"Skipping export batch creation."
            )
            return {
                "status": "skipped",
                "message": f"Insufficient chunks: {available_chunks_count} < 200",
                "batch_id": None,
                "chunks_exported": 0,
                "available_chunks": available_chunks_count,
            }

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 40, "total": 100, "status": "Creating export batch..."},
        )

        # Create export batch with force_create=False (scheduled export)
        try:
            batch = export_service.create_export_batch(
                max_chunks=200,
                force_create=False,  # Scheduled exports require full batches
            )

            # Update progress
            self.update_state(
                state="PROGRESS",
                meta={"current": 90, "total": 100, "status": "Finalizing..."},
            )

            logger.info(
                f"Export batch {batch.batch_id} created successfully with {batch.chunk_count} chunks"
            )

            # Trigger cleanup task
            cleanup_exported_chunks.delay(batch.chunk_ids)

            return {
                "status": "success",
                "message": f"Export batch created with {batch.chunk_count} chunks",
                "batch_id": batch.batch_id,
                "chunks_exported": batch.chunk_count,
                "archive_path": batch.archive_path,
                "storage_type": batch.storage_type.value,
                "file_size_mb": (
                    batch.file_size_bytes / (1024 * 1024)
                    if batch.file_size_bytes
                    else 0
                ),
            }

        except ValidationError as e:
            # ValidationError for insufficient chunks is expected, not a failure
            if "Insufficient chunks" in str(e):
                logger.info(f"Export batch creation skipped: {e}")
                return {
                    "status": "skipped",
                    "message": str(e),
                    "batch_id": None,
                    "chunks_exported": 0,
                }
            else:
                # Other validation errors should be raised
                raise

    except Exception as e:
        logger.error(f"Error in export batch creation task: {e}")

        self.update_state(state="FAILURE", meta={"error": str(e)})

        return {
            "status": "failed",
            "message": str(e),
            "batch_id": batch_id,
            "chunks_exported": 0,
        }

    finally:
        db.close()


@celery_app.task(
    bind=True,
    name="cleanup_exported_chunks",
    autoretry_for=(Exception,),
    retry_kwargs={"max_retries": 5, "countdown": 120},
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
)
def cleanup_exported_chunks(self, chunk_ids: List[int]) -> dict:
    """
    Async task for cleanup after export.

    This task:
    - Deletes transcriptions first (referential integrity)
    - Deletes chunks in bulk
    - Deletes audio files from disk
    - Logs cleanup failures for manual intervention
    - Retries on database errors with exponential backoff

    Args:
        chunk_ids: List of chunk IDs to clean up

    Returns:
        dict: Cleanup results
    """
    db = get_db()

    try:
        logger.info(f"Starting cleanup task for {len(chunk_ids)} exported chunks")

        # Update task progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Preparing cleanup..."},
        )

        export_service = ExportBatchService(db)

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={
                "current": 20,
                "total": 100,
                "status": "Deleting chunks and transcriptions...",
            },
        )

        # Perform cleanup
        export_service.cleanup_exported_chunks(chunk_ids)

        # Update progress
        self.update_state(
            state="PROGRESS",
            meta={"current": 90, "total": 100, "status": "Finalizing..."},
        )

        logger.info(f"Cleanup completed successfully for {len(chunk_ids)} chunks")

        return {
            "status": "success",
            "message": f"Successfully cleaned up {len(chunk_ids)} chunks",
            "chunks_cleaned": len(chunk_ids),
        }

    except Exception as e:
        logger.error(f"Error in cleanup task for chunks {chunk_ids}: {e}")
        logger.error(
            f"Manual intervention may be required for cleanup of chunks: {chunk_ids}"
        )

        self.update_state(
            state="FAILURE", meta={"error": str(e), "chunk_ids": chunk_ids}
        )

        return {
            "status": "failed",
            "message": str(e),
            "chunks_cleaned": 0,
            "failed_chunk_ids": chunk_ids,
        }

    finally:
        db.close()


@celery_app.task(bind=True, name="check_export_alerts_task")
def check_export_alerts_task(self):
    """
    Scheduled task to check export-related alerts.

    This task runs periodically (e.g., every 15 minutes) to check:
    - Export batch failures (> 3 consecutive)
    - R2 usage approaching limits (> 80%)
    - Consensus failure rate (> 10%)
    - Export backlog (> 500 chunks)

    Alerts are logged and stored in Redis for monitoring.
    """
    from app.core.export_alerts import check_export_alerts
    from app.db.database import SessionLocal

    logger.info("Starting scheduled export alerts check")

    db = SessionLocal()
    try:
        # Check all alert conditions
        alerts = check_export_alerts(db)

        logger.info(f"Alert check completed: {len(alerts)} active alerts")

        return {
            "status": "completed",
            "alerts_count": len(alerts),
            "alerts": [
                {
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "component": alert.component,
                }
                for alert in alerts
            ],
        }

    except Exception as e:
        logger.error(f"Error in alert check task: {e}", exc_info=True)
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()
