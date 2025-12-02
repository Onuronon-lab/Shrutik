"""
Export Batch Service

This service manages the creation, storage, and download of export batches.
It handles:
- Querying ready chunks with filtering
- Generating tar.zst archives
- Uploading to local or R2 storage
- Enforcing download limits
- Cleanup of exported data
"""

import hashlib
import json
import logging
import os
import tarfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, not_
from sqlalchemy.orm import Session

from app.core.config import StorageConfig, settings
from app.core.exceptions import ValidationError
from app.core.export_metrics import export_metrics_collector, r2_metrics_collector
from app.models.audio_chunk import AudioChunk
from app.models.export_batch import ExportBatch, ExportBatchStatus, StorageType
from app.models.export_download import ExportDownload
from app.models.transcription import Transcription

logger = logging.getLogger(__name__)


class ExportBatchService:
    """Service for batch export operations."""

    def __init__(self, db: Session, storage_config: Optional[StorageConfig] = None):
        self.db = db
        self.storage_config = storage_config or StorageConfig.from_env()

    def check_r2_free_tier_limits(self) -> bool:
        """
        Check if creating a new export batch would exceed R2 free tier limits.

        Returns True if safe to proceed, False if limits would be exceeded.

        Checks:
        - Class A operations this month (uploads)
        - Total storage used
        - Logs warning if approaching limits (>80%)
        """
        if not settings.R2_ENABLE_FREE_TIER_GUARD:
            logger.info("R2 free tier guard is disabled, skipping limit check")
            return True

        if self.storage_config.storage_type != "r2":
            logger.debug("Storage type is not R2, skipping free tier check")
            return True

        try:
            # Get current month's export batches
            now = datetime.now(timezone.utc)
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Count Class A operations (uploads) this month
            class_a_count = (
                self.db.query(func.count(ExportBatch.id))
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
                self.db.query(func.count(ExportDownload.id))
                .filter(ExportDownload.downloaded_at >= month_start)
                .scalar()
                or 0
            )

            # Calculate total storage used (sum of all completed batch file sizes)
            total_storage_bytes = (
                self.db.query(func.sum(ExportBatch.file_size_bytes))
                .filter(
                    and_(
                        ExportBatch.storage_type == StorageType.R2,
                        ExportBatch.status == ExportBatchStatus.COMPLETED,
                    )
                )
                .scalar()
                or 0
            )

            total_storage_gb = total_storage_bytes / (1024**3)

            # Check limits
            class_a_limit = settings.R2_FREE_TIER_CLASS_A_MONTHLY
            class_b_limit = settings.R2_FREE_TIER_CLASS_B_MONTHLY
            storage_limit_gb = settings.R2_FREE_TIER_STORAGE_GB

            class_a_usage_pct = (class_a_count / class_a_limit) * 100
            class_b_usage_pct = (class_b_count / class_b_limit) * 100
            storage_usage_pct = (total_storage_gb / storage_limit_gb) * 100

            logger.info(
                f"R2 usage: Class A: {class_a_count}/{class_a_limit} ({class_a_usage_pct:.1f}%), "
                f"Class B: {class_b_count}/{class_b_limit} ({class_b_usage_pct:.1f}%), "
                f"Storage: {total_storage_gb:.2f}/{storage_limit_gb} GB ({storage_usage_pct:.1f}%)"
            )

            # Check if any limit would be exceeded
            if class_a_count >= class_a_limit:
                logger.error(
                    f"R2 Class A operation limit exceeded: {class_a_count}/{class_a_limit}"
                )
                return False

            if total_storage_gb >= storage_limit_gb:
                logger.error(
                    f"R2 storage limit exceeded: {total_storage_gb:.2f}/{storage_limit_gb} GB"
                )
                return False

            # Warn if approaching limits (>80%)
            if class_a_usage_pct > 80:
                logger.warning(
                    f"R2 Class A operations approaching limit: {class_a_usage_pct:.1f}%"
                )

            if storage_usage_pct > 80:
                logger.warning(
                    f"R2 storage approaching limit: {storage_usage_pct:.1f}%"
                )

            return True

        except Exception as e:
            logger.error(f"Error checking R2 free tier limits: {e}")
            # Fail safe: allow operation if check fails
            return True

    def create_export_batch(
        self,
        max_chunks: int = 200,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_duration: Optional[float] = None,
        max_duration: Optional[float] = None,
        force_create: bool = False,
    ) -> ExportBatch:
        """
        Create export batch from ready chunks with optional filtering.

        Steps:
        1. Check R2 free tier limits (if enabled)
        2. Query chunks WHERE ready_for_export = TRUE
           - Exclude chunks already in completed export batches
           - Apply date range filter if specified (created_at)
           - Apply duration filter if specified
           - LIMIT max_chunks (default 200)
        3. If force_create is False and chunk count < max_chunks, raise error
           (scheduled exports require full batches for consistency)
        4. If force_create is True (admin request), proceed with any chunk count
        5. Filter out oversized chunks (> EXPORT_MAX_CHUNK_SIZE_MB)
        6. Generate tar.zst with audio files and JSON metadata
        7. Upload to configured storage (local or R2)
        8. Create ExportBatch record with filter_criteria
        9. Trigger cleanup task
        10. Log skipped chunks for admin review
        """
        logger.info(
            f"Creating export batch with max_chunks={max_chunks}, force_create={force_create}",
            extra={
                "operation_type": "export_batch_creation",
                "max_chunks": max_chunks,
                "force_create": force_create,
                "user_id": user_id,
                "date_from": date_from.isoformat() if date_from else None,
                "date_to": date_to.isoformat() if date_to else None,
                "min_duration": min_duration,
                "max_duration": max_duration,
            },
        )

        # Step 1: Check R2 free tier limits
        if not self.check_r2_free_tier_limits():
            raise ValidationError(
                "R2 free tier limits would be exceeded. Cannot create export batch."
            )

        # Step 2: Query ready chunks with filters
        # Get chunk IDs that are already in completed export batches
        exported_chunk_ids_subquery = (
            self.db.query(func.unnest(ExportBatch.chunk_ids).label("chunk_id"))
            .filter(ExportBatch.status == ExportBatchStatus.COMPLETED)
            .subquery()
        )

        # Build query for ready chunks
        query = self.db.query(AudioChunk).filter(
            and_(
                AudioChunk.ready_for_export == True,
                not_(
                    AudioChunk.id.in_(
                        self.db.query(exported_chunk_ids_subquery.c.chunk_id)
                    )
                ),
            )
        )

        # Apply date range filter
        if date_from:
            query = query.filter(AudioChunk.created_at >= date_from)
        if date_to:
            query = query.filter(AudioChunk.created_at <= date_to)

        # Apply duration filter
        if min_duration is not None:
            query = query.filter(AudioChunk.duration >= min_duration)
        if max_duration is not None:
            query = query.filter(AudioChunk.duration <= max_duration)

        # Limit results
        query = query.limit(max_chunks)

        chunks = query.all()

        logger.info(
            f"Found {len(chunks)} ready chunks matching criteria",
            extra={
                "operation_type": "export_batch_creation",
                "chunk_count": len(chunks),
                "batch_id": batch_id,
            },
        )

        # Step 3 & 4: Check chunk count vs force_create
        if not force_create and len(chunks) < max_chunks:
            raise ValidationError(
                f"Insufficient chunks for scheduled export: {len(chunks)} < {max_chunks}. "
                f"Use force_create=True to create batch with fewer chunks."
            )

        if len(chunks) == 0:
            raise ValidationError("No chunks available for export")

        # Step 5: Filter out oversized chunks
        max_chunk_size_bytes = settings.EXPORT_MAX_CHUNK_SIZE_MB * 1024 * 1024
        valid_chunks = []
        skipped_chunks = []

        for chunk in chunks:
            if os.path.exists(chunk.file_path):
                file_size = os.path.getsize(chunk.file_path)
                if file_size <= max_chunk_size_bytes:
                    valid_chunks.append(chunk)
                else:
                    skipped_chunks.append(
                        {
                            "chunk_id": chunk.id,
                            "reason": "oversized",
                            "size_mb": file_size / (1024 * 1024),
                        }
                    )
            else:
                skipped_chunks.append(
                    {
                        "chunk_id": chunk.id,
                        "reason": "missing_file",
                        "file_path": chunk.file_path,
                    }
                )

        if skipped_chunks:
            logger.warning(f"Skipped {len(skipped_chunks)} chunks: {skipped_chunks}")

        if len(valid_chunks) == 0:
            raise ValidationError("No valid chunks available after filtering")

        # Generate batch ID
        batch_id = str(uuid.uuid4())

        # Create batch record (pending status)
        filter_criteria = {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
            "min_duration": min_duration,
            "max_duration": max_duration,
            "max_chunks": max_chunks,
            "force_create": force_create,
        }

        batch = ExportBatch(
            batch_id=batch_id,
            archive_path="",  # Will be set after upload
            storage_type=(
                StorageType.LOCAL
                if self.storage_config.storage_type == "local"
                else StorageType.R2
            ),
            chunk_count=len(valid_chunks),
            chunk_ids=[chunk.id for chunk in valid_chunks],
            status=ExportBatchStatus.PENDING,
            filter_criteria=filter_criteria,
            created_by_id=user_id,
            compression_level=settings.EXPORT_COMPRESSION_LEVEL,
        )

        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)

        try:
            # Update status to processing
            batch.status = ExportBatchStatus.PROCESSING
            self.db.commit()

            # Step 6: Generate tar.zst archive
            archive_path, file_size = self.generate_export_archive(
                valid_chunks, batch_id
            )

            # Step 7: Upload to storage
            storage_path = self.upload_to_storage(archive_path, batch_id)

            # Update batch record
            batch.archive_path = storage_path
            batch.file_size_bytes = file_size
            batch.status = ExportBatchStatus.COMPLETED
            batch.exported = True
            batch.completed_at = datetime.now(timezone.utc)

            # Calculate metadata
            recording_ids = [chunk.recording_id for chunk in valid_chunks]
            batch.recording_id_range = {
                "min": min(recording_ids),
                "max": max(recording_ids),
            }
            batch.total_duration_seconds = sum(chunk.duration for chunk in valid_chunks)

            # Calculate checksum
            batch.checksum = self._calculate_file_checksum(archive_path)

            self.db.commit()
            self.db.refresh(batch)

            logger.info(
                f"Export batch {batch_id} created successfully with {len(valid_chunks)} chunks",
                extra={
                    "operation_type": "export_batch_creation",
                    "batch_id": batch_id,
                    "chunk_count": len(valid_chunks),
                    "user_id": user_id,
                    "storage_type": self.storage_config.storage_type,
                    "file_size_bytes": batch.file_size_bytes,
                    "status": "completed",
                },
            )

            # Record metrics
            export_metrics_collector.record_export_batch_created(
                batch_id=batch_id, chunk_count=len(valid_chunks), user_id=user_id
            )
            export_metrics_collector.reset_consecutive_failures()

            # Step 9: Cleanup will be triggered by Celery task (not done here)
            # The cleanup task should be called separately after batch creation

            return batch

        except Exception as e:
            logger.error(
                f"Error creating export batch {batch_id}: {e}",
                extra={
                    "operation_type": "export_batch_creation",
                    "batch_id": batch_id,
                    "user_id": user_id,
                    "error": str(e),
                    "status": "failed",
                },
                exc_info=True,
            )
            batch.status = ExportBatchStatus.FAILED
            batch.error_message = str(e)
            batch.retry_count += 1
            self.db.commit()

            # Record failure metrics
            export_metrics_collector.record_export_batch_failed(
                batch_id=batch_id, error_message=str(e), user_id=user_id
            )

            raise

    def generate_export_archive(
        self, chunks: List[AudioChunk], batch_id: str
    ) -> Tuple[str, int]:
        """
        Generate tar.zst archive with chunk audio and metadata.

        Uses Zstandard compression for optimal size/speed balance.
        Returns (archive_path, file_size_bytes)
        """
        import zstandard as zstd

        logger.info(
            f"Generating tar.zst archive for batch {batch_id} with {len(chunks)} chunks"
        )

        # Create temporary directory for archive
        temp_dir = Path(settings.EXPORT_LOCAL_DIR) / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        archive_filename = f"export_batch_{batch_id}.tar.zst"
        archive_path = str(temp_dir / archive_filename)

        # Determine compression level based on average chunk duration
        avg_duration = sum(chunk.duration for chunk in chunks) / len(chunks)
        if avg_duration < 3.0:
            compression_level = 5  # Small chunks: better compression
        elif avg_duration > 7.0:
            compression_level = 1  # Large chunks: faster
        else:
            compression_level = settings.EXPORT_COMPRESSION_LEVEL  # Default: balanced

        logger.info(
            f"Using compression level {compression_level} (avg duration: {avg_duration:.1f}s)"
        )

        try:
            # Create tar archive with zstandard compression
            with open(archive_path, "wb") as f:
                # Create zstandard compressor
                cctx = zstd.ZstdCompressor(level=compression_level)

                with cctx.stream_writer(f) as compressor:
                    # Create tar file writing to compressed stream
                    with tarfile.open(fileobj=compressor, mode="w|") as tar:
                        # Add chunks directory
                        for chunk in chunks:
                            # Add audio file
                            if os.path.exists(chunk.file_path):
                                audio_filename = f"chunk_{chunk.id:06d}.webm"
                                tar.add(
                                    chunk.file_path, arcname=f"chunks/{audio_filename}"
                                )

                                # Create and add JSON metadata
                                metadata = {
                                    "chunk_id": chunk.id,
                                    "audio_file": audio_filename,
                                    "transcript": (
                                        chunk.consensus_transcript.text
                                        if chunk.consensus_transcript
                                        else ""
                                    ),
                                    "metadata": {
                                        "recording_id": chunk.recording_id,
                                        "chunk_index": chunk.chunk_index,
                                        "duration": chunk.duration,
                                        "start_time": chunk.start_time,
                                        "end_time": chunk.end_time,
                                        "language": (
                                            chunk.meta_data.get("language")
                                            if chunk.meta_data
                                            else None
                                        ),
                                        "transcript_count": chunk.transcript_count,
                                        "consensus_quality": chunk.consensus_quality,
                                        "created_at": (
                                            chunk.created_at.isoformat()
                                            if chunk.created_at
                                            else None
                                        ),
                                    },
                                }

                                # Write metadata to temp file and add to tar
                                json_filename = f"chunk_{chunk.id:06d}.json"
                                json_temp_path = temp_dir / json_filename
                                with open(
                                    json_temp_path, "w", encoding="utf-8"
                                ) as json_file:
                                    json.dump(
                                        metadata,
                                        json_file,
                                        indent=2,
                                        ensure_ascii=False,
                                    )

                                tar.add(
                                    str(json_temp_path),
                                    arcname=f"chunks/{json_filename}",
                                )
                                json_temp_path.unlink()  # Clean up temp JSON file
                            else:
                                logger.warning(
                                    f"Audio file not found for chunk {chunk.id}: {chunk.file_path}"
                                )

                        # Create and add manifest.json
                        manifest = {
                            "batch_id": batch_id,
                            "export_timestamp": datetime.now(timezone.utc).isoformat(),
                            "chunk_count": len(chunks),
                            "total_duration_seconds": sum(
                                chunk.duration for chunk in chunks
                            ),
                            "languages": list(
                                set(
                                    chunk.meta_data.get("language")
                                    for chunk in chunks
                                    if chunk.meta_data
                                    and chunk.meta_data.get("language")
                                )
                            ),
                            "format_version": "1.0",
                            "compression": "zstd",
                            "compression_level": compression_level,
                            "audio_format": "webm",
                        }

                        manifest_temp_path = temp_dir / "manifest.json"
                        with open(
                            manifest_temp_path, "w", encoding="utf-8"
                        ) as manifest_file:
                            json.dump(
                                manifest, manifest_file, indent=2, ensure_ascii=False
                            )

                        tar.add(str(manifest_temp_path), arcname="manifest.json")
                        manifest_temp_path.unlink()

                        # Create and add README.txt
                        readme_content = f"""Shrutik Export Batch {batch_id}
=====================================

This archive contains voice recording chunks and their consensus transcriptions.

Contents:
- chunks/: Audio files (.webm) and metadata (.json) for each chunk
- manifest.json: Batch metadata and statistics
- README.txt: This file

Format Version: 1.0
Export Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
Chunk Count: {len(chunks)}
Total Duration: {sum(chunk.duration for chunk in chunks):.1f} seconds

To extract:
  tar -I zstd -xf {archive_filename}

For more information, visit: https://github.com/yourusername/shrutik
"""

                        readme_temp_path = temp_dir / "README.txt"
                        with open(
                            readme_temp_path, "w", encoding="utf-8"
                        ) as readme_file:
                            readme_file.write(readme_content)

                        tar.add(str(readme_temp_path), arcname="README.txt")
                        readme_temp_path.unlink()

            # Get file size
            file_size = os.path.getsize(archive_path)

            logger.info(
                f"Archive created: {archive_path} ({file_size / (1024*1024):.2f} MB)"
            )

            return archive_path, file_size

        except Exception as e:
            logger.error(f"Error generating archive for batch {batch_id}: {e}")
            # Clean up partial archive
            if os.path.exists(archive_path):
                os.remove(archive_path)
            raise

    def upload_to_storage(self, archive_path: str, batch_id: str) -> str:
        """
        Upload archive to configured storage backend.

        Returns storage path (local or R2 URL)
        """
        if self.storage_config.storage_type == "local":
            return self._upload_to_local_storage(archive_path, batch_id)
        elif self.storage_config.storage_type == "r2":
            return self._upload_to_r2_storage(archive_path, batch_id)
        else:
            raise ValueError(
                f"Unknown storage type: {self.storage_config.storage_type}"
            )

    def _upload_to_local_storage(self, archive_path: str, batch_id: str) -> str:
        """Upload archive to local storage."""
        logger.info(f"Uploading batch {batch_id} to local storage")

        # Ensure export directory exists
        export_dir = Path(self.storage_config.local_export_dir)
        export_dir.mkdir(parents=True, exist_ok=True)

        # Move archive to export directory
        archive_filename = os.path.basename(archive_path)
        final_path = export_dir / archive_filename

        # Move file
        os.rename(archive_path, str(final_path))

        # Set proper permissions (600 - owner read/write only)
        os.chmod(str(final_path), 0o600)

        logger.info(f"Archive uploaded to local storage: {final_path}")

        return str(final_path)

    def _upload_to_r2_storage(self, archive_path: str, batch_id: str) -> str:
        """Upload archive to Cloudflare R2 storage."""
        import time

        import boto3
        from botocore.exceptions import ClientError

        logger.info(
            f"Uploading batch {batch_id} to R2 storage",
            extra={
                "operation_type": "r2_upload",
                "r2_operation_class": "Class A",
                "batch_id": batch_id,
                "storage_type": "r2",
            },
        )

        # Create S3 client for R2
        s3_client = boto3.client(
            "s3",
            endpoint_url=self.storage_config.r2_endpoint_url,
            aws_access_key_id=self.storage_config.r2_access_key_id,
            aws_secret_access_key=self.storage_config.r2_secret_access_key,
            region_name="auto",  # R2 uses 'auto' region
        )

        bucket_name = self.storage_config.r2_bucket_name
        archive_filename = os.path.basename(archive_path)
        object_key = f"exports/{archive_filename}"

        # Upload with retry logic (max 3 attempts)
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Upload attempt {attempt}/{max_retries}")

                # Upload file
                with open(archive_path, "rb") as f:
                    s3_client.upload_fileobj(
                        f,
                        bucket_name,
                        object_key,
                        ExtraArgs={
                            "ServerSideEncryption": "AES256",
                            "ContentType": "application/x-tar",
                        },
                    )

                logger.info(
                    f"Successfully uploaded to R2: {object_key}",
                    extra={
                        "operation_type": "r2_upload",
                        "r2_operation_class": "Class A",
                        "batch_id": batch_id,
                        "r2_object_key": object_key,
                        "storage_type": "r2",
                        "attempt": attempt,
                        "status": "success",
                    },
                )

                # Record R2 metrics
                r2_metrics_collector.record_r2_operation("Class A", "upload")

                # Clean up local temp file
                os.remove(archive_path)

                # Return R2 URL
                r2_url = (
                    f"{self.storage_config.r2_endpoint_url}/{bucket_name}/{object_key}"
                )
                return r2_url

            except ClientError as e:
                logger.error(
                    f"R2 upload attempt {attempt} failed: {e}",
                    extra={
                        "operation_type": "r2_upload",
                        "r2_operation_class": "Class A",
                        "batch_id": batch_id,
                        "r2_object_key": object_key,
                        "storage_type": "r2",
                        "attempt": attempt,
                        "max_retries": max_retries,
                        "error": str(e),
                        "status": "retry" if attempt < max_retries else "failed",
                    },
                )

                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"All {max_retries} upload attempts failed")
                    raise

            except Exception as e:
                logger.error(f"Unexpected error during R2 upload: {e}")
                raise

    def cleanup_exported_chunks(self, chunk_ids: List[int]) -> None:
        """
        Delete exported chunks, transcriptions, and audio files.

        Bulk operations in single transaction.
        """
        logger.info(
            f"Cleaning up {len(chunk_ids)} exported chunks",
            extra={
                "operation_type": "cleanup",
                "chunk_count": len(chunk_ids),
                "chunk_ids": (
                    chunk_ids[:10] if len(chunk_ids) > 10 else chunk_ids
                ),  # Log first 10 for brevity
            },
        )

        try:
            # Get chunks to delete (need file paths before deletion)
            chunks = (
                self.db.query(AudioChunk).filter(AudioChunk.id.in_(chunk_ids)).all()
            )

            file_paths = [chunk.file_path for chunk in chunks if chunk.file_path]

            # Delete transcriptions first (referential integrity)
            deleted_transcriptions = (
                self.db.query(Transcription)
                .filter(Transcription.chunk_id.in_(chunk_ids))
                .delete(synchronize_session=False)
            )

            logger.info(
                f"Deleted {deleted_transcriptions} transcriptions",
                extra={
                    "operation_type": "cleanup",
                    "cleanup_stage": "transcriptions",
                    "deleted_count": deleted_transcriptions,
                    "chunk_count": len(chunk_ids),
                },
            )

            # Delete chunks
            deleted_chunks = (
                self.db.query(AudioChunk)
                .filter(AudioChunk.id.in_(chunk_ids))
                .delete(synchronize_session=False)
            )

            logger.info(
                f"Deleted {deleted_chunks} chunks from database",
                extra={
                    "operation_type": "cleanup",
                    "cleanup_stage": "chunks",
                    "deleted_count": deleted_chunks,
                    "chunk_count": len(chunk_ids),
                },
            )

            # Commit database changes
            self.db.commit()

            # Delete audio files from disk
            deleted_files = 0
            failed_files = []

            for file_path in file_paths:
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_files += 1
                    else:
                        logger.warning(f"Audio file not found: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete audio file {file_path}: {e}")
                    failed_files.append(file_path)

            logger.info(
                f"Deleted {deleted_files} audio files from disk",
                extra={
                    "operation_type": "cleanup",
                    "cleanup_stage": "audio_files",
                    "deleted_count": deleted_files,
                    "failed_count": len(failed_files),
                    "chunk_count": len(chunk_ids),
                },
            )

            if failed_files:
                logger.warning(
                    f"Failed to delete {len(failed_files)} audio files: {failed_files}"
                )

        except Exception as e:
            logger.error(
                f"Error during cleanup: {e}",
                extra={
                    "operation_type": "cleanup",
                    "chunk_count": len(chunk_ids),
                    "chunk_ids": chunk_ids[:10] if len(chunk_ids) > 10 else chunk_ids,
                    "error": str(e),
                    "status": "failed",
                },
                exc_info=True,
            )
            self.db.rollback()
            raise

    def get_export_batch(self, batch_id: str) -> Optional[ExportBatch]:
        """Get export batch by ID."""
        return (
            self.db.query(ExportBatch).filter(ExportBatch.batch_id == batch_id).first()
        )

    def list_export_batches(
        self,
        user_id: Optional[int] = None,
        status_filter: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ExportBatch], int]:
        """
        List export batches with pagination and filtering.

        Returns (batches, total_count)
        """
        query = self.db.query(ExportBatch).order_by(ExportBatch.created_at.desc())

        # Filter by user if specified (non-admin users see only their batches)
        if user_id:
            query = query.filter(ExportBatch.created_by_id == user_id)

        # Filter by status
        if status_filter:
            try:
                status_enum = ExportBatchStatus(status_filter)
                query = query.filter(ExportBatch.status == status_enum)
            except ValueError:
                logger.warning(f"Invalid status filter: {status_filter}")

        # Filter by date range
        if date_from:
            query = query.filter(ExportBatch.created_at >= date_from)
        if date_to:
            query = query.filter(ExportBatch.created_at <= date_to)

        # Get total count before pagination
        total_count = query.count()

        # Apply pagination
        batches = query.offset(skip).limit(limit).all()

        return batches, total_count

    def download_export_batch(
        self,
        batch_id: str,
        user_id: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ):
        """
        Get download path for export batch with rate limiting.

        Steps:
        1. Check user's daily download count (max 2 per day)
        2. If limit exceeded, raise error with reset time
        3. Record download in export_downloads table
        4. Return (file_path, mime_type) for local or dict with download_url for R2
        """
        logger.info(
            f"Processing download request for batch {batch_id} by user {user_id}",
            extra={
                "operation_type": "export_download",
                "r2_operation_class": (
                    "Class B" if self.storage_config.storage_type == "r2" else None
                ),
                "batch_id": batch_id,
                "user_id": user_id,
                "storage_type": self.storage_config.storage_type,
            },
        )

        # Get batch
        batch = self.get_export_batch(batch_id)
        if not batch:
            raise ValidationError(f"Export batch {batch_id} not found")

        if batch.status != ExportBatchStatus.COMPLETED:
            raise ValidationError(
                f"Export batch {batch_id} is not ready for download (status: {batch.status.value})"
            )

        # Check download limit
        can_download, reset_time = self.check_download_limit(user_id)
        if not can_download:
            raise ValidationError(
                f"Daily download limit exceeded. Limit resets at {reset_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

        # Record download
        download_record = ExportDownload(
            batch_id=batch_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(download_record)
        self.db.commit()

        logger.info(
            f"Download recorded for batch {batch_id} by user {user_id}",
            extra={
                "operation_type": "export_download",
                "r2_operation_class": (
                    "Class B" if self.storage_config.storage_type == "r2" else None
                ),
                "batch_id": batch_id,
                "user_id": user_id,
                "storage_type": self.storage_config.storage_type,
                "status": "success",
            },
        )

        # Record R2 metrics for downloads
        if self.storage_config.storage_type == "r2":
            r2_metrics_collector.record_r2_operation("Class B", "download")

        # Return file path and mime type
        mime_type = "application/x-tar"

        if batch.storage_type == StorageType.LOCAL:
            return batch.archive_path, mime_type
        elif batch.storage_type == StorageType.R2:
            # Generate signed URL for R2 download
            signed_url = self._generate_r2_signed_url(
                batch.archive_path, expires_in=3600
            )
            return {"download_url": signed_url, "expires_in": 3600}
        else:
            raise ValidationError(f"Unknown storage type: {batch.storage_type}")

    def _generate_r2_signed_url(self, r2_url: str, expires_in: int = 3600) -> str:
        """Generate temporary signed URL for R2 download."""
        import boto3

        # Create S3 client for R2
        s3_client = boto3.client(
            "s3",
            endpoint_url=self.storage_config.r2_endpoint_url,
            aws_access_key_id=self.storage_config.r2_access_key_id,
            aws_secret_access_key=self.storage_config.r2_secret_access_key,
            region_name="auto",
        )

        # Extract bucket and key from R2 URL
        # Format: https://account_id.r2.cloudflarestorage.com/bucket_name/exports/filename
        bucket_name = self.storage_config.r2_bucket_name
        object_key = r2_url.split(f"/{bucket_name}/")[1]

        # Generate presigned URL
        signed_url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expires_in,
        )

        logger.info(f"Generated signed URL for {object_key} (expires in {expires_in}s)")

        return signed_url

    def retry_export_batch(self, batch_id: str) -> ExportBatch:
        """
        Retry a failed export batch.

        Args:
            batch_id: The batch ID to retry

        Returns:
            Updated export batch with status set to pending
        """
        logger.info(f"Retrying export batch {batch_id}")

        # Get the batch
        batch = self.get_export_batch(batch_id)
        if not batch:
            raise ValidationError(f"Export batch {batch_id} not found")

        # Update batch status and increment retry count
        batch.status = ExportBatchStatus.PENDING
        batch.retry_count += 1
        batch.error_message = None

        self.db.commit()
        self.db.refresh(batch)

        logger.info(
            f"Export batch {batch_id} marked for retry (attempt {batch.retry_count})"
        )

        # Trigger the export task
        from app.tasks.export_optimization import create_export_batch_task

        create_export_batch_task.delay(batch_id=batch_id)

        return batch

    def check_download_limit(self, user_id: int) -> Tuple[bool, Optional[datetime]]:
        """
        Check if user has exceeded daily download limit.

        Returns (can_download, reset_time)
        """
        download_count = self.get_user_download_count_today(user_id)
        limit = settings.EXPORT_DAILY_DOWNLOAD_LIMIT

        can_download = download_count < limit

        # Calculate reset time (midnight UTC)
        now = datetime.now(timezone.utc)
        reset_time = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        logger.info(f"User {user_id} download count today: {download_count}/{limit}")

        return can_download, reset_time

    def get_user_download_count_today(self, user_id: int) -> int:
        """
        Get number of downloads by user today (UTC).
        """
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        count = (
            self.db.query(func.count(ExportDownload.id))
            .filter(
                and_(
                    ExportDownload.user_id == user_id,
                    ExportDownload.downloaded_at >= today_start,
                )
            )
            .scalar()
            or 0
        )

        return count

    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file."""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read file in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()

    def cleanup_old_local_archives(self, days_old: int = 90) -> int:
        """
        Clean up old archives from local storage.

        Args:
            days_old: Delete archives older than this many days

        Returns:
            Number of archives deleted
        """
        if self.storage_config.storage_type != "local":
            logger.info("Storage type is not local, skipping local archive cleanup")
            return 0

        logger.info(f"Cleaning up local archives older than {days_old} days")

        export_dir = Path(self.storage_config.local_export_dir)
        if not export_dir.exists():
            logger.warning(f"Export directory does not exist: {export_dir}")
            return 0

        cutoff_time = datetime.now(timezone.utc) - timedelta(days=days_old)
        deleted_count = 0

        # Find all .tar.zst files
        for archive_file in export_dir.glob("export_batch_*.tar.zst"):
            try:
                # Get file modification time
                file_mtime = datetime.fromtimestamp(
                    archive_file.stat().st_mtime, tz=timezone.utc
                )

                if file_mtime < cutoff_time:
                    # Delete file
                    archive_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old archive: {archive_file.name}")
            except Exception as e:
                logger.error(f"Error deleting archive {archive_file}: {e}")

        logger.info(f"Cleaned up {deleted_count} old archives")
        return deleted_count
