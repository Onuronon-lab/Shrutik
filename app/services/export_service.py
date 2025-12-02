"""
Export service for secure data export functionality.

This service handles dataset and metadata export operations with proper
filtering, format conversion, and audit logging for Sworik developers.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.audio_chunk import AudioChunk
from app.models.export_audit import ExportAuditLog
from app.models.language import Language
from app.models.transcription import Transcription
from app.models.user import User
from app.models.voice_recording import RecordingStatus, VoiceRecording
from app.schemas.export import DatasetExportRequest, DatasetExportResponse
from app.schemas.export import ExportAuditLog as ExportAuditLogSchema
from app.schemas.export import (
    ExportedDataItem,
    ExportFormat,
    ExportStatistics,
    MetadataExportRequest,
    MetadataExportResponse,
)


class ExportService:
    """Service for handling data export operations."""

    def __init__(self, db: Session):
        self.db = db

    def export_dataset(
        self,
        request: DatasetExportRequest,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> DatasetExportResponse:
        """
        Export validated dataset with filtering and format options.

        Args:
            request: Export request parameters
            user: Requesting user (must have export permissions)
            ip_address: Client IP address for audit logging
            user_agent: Client user agent for audit logging

        Returns:
            DatasetExportResponse with exported data and metadata
        """
        export_id = str(uuid.uuid4())

        try:
            # Build query with filters
            query = self._build_dataset_query(request)

            # Execute query and get results
            results = query.all()

            # Convert to export format
            exported_items = self._convert_to_export_items(results)

            # Apply record limit if specified
            if request.max_records and len(exported_items) > request.max_records:
                exported_items = exported_items[: request.max_records]

            # Generate statistics
            statistics = self._generate_export_statistics(results, request)

            # Create response
            response = DatasetExportResponse(
                export_id=export_id,
                data=exported_items,
                statistics=statistics,
                format=request.format,
                total_records=len(exported_items),
                export_timestamp=datetime.now(timezone.utc),
            )

            # Log export activity
            self._log_export_activity(
                export_id=export_id,
                user=user,
                export_type="dataset",
                format=request.format,
                filters=request.model_dump(exclude_unset=True),
                records_exported=len(exported_items),
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return response

        except Exception as e:
            # Log failed export attempt
            self._log_export_activity(
                export_id=export_id,
                user=user,
                export_type="dataset",
                format=request.format,
                filters=request.model_dump(exclude_unset=True),
                records_exported=0,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Export failed: {str(e)}",
            )

    def export_metadata(
        self,
        request: MetadataExportRequest,
        user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> MetadataExportResponse:
        """
        Export platform metadata and statistics.

        Args:
            request: Metadata export request parameters
            user: Requesting user (must have export permissions)
            ip_address: Client IP address for audit logging
            user_agent: Client user agent for audit logging

        Returns:
            MetadataExportResponse with platform metadata
        """
        export_id = str(uuid.uuid4())

        try:
            # Generate platform statistics
            statistics = self._generate_platform_statistics()

            # Generate platform metrics
            platform_metrics = self._generate_platform_metrics()

            # Generate user statistics if requested
            user_statistics = None
            if request.include_user_stats:
                user_statistics = self._generate_user_statistics()

            # Generate quality metrics if requested
            quality_metrics = None
            if request.include_quality_metrics:
                quality_metrics = self._generate_quality_metrics()

            # Create response
            response = MetadataExportResponse(
                export_id=export_id,
                statistics=statistics,
                platform_metrics=platform_metrics,
                user_statistics=user_statistics,
                quality_metrics=quality_metrics,
                format=request.format,
                export_timestamp=datetime.now(timezone.utc),
            )

            # Log export activity
            self._log_export_activity(
                export_id=export_id,
                user=user,
                export_type="metadata",
                format=request.format,
                filters=request.model_dump(exclude_unset=True),
                records_exported=1,  # Metadata is one record
                ip_address=ip_address,
                user_agent=user_agent,
            )

            return response

        except Exception as e:
            # Log failed export attempt
            self._log_export_activity(
                export_id=export_id,
                user=user,
                export_type="metadata",
                format=request.format,
                filters=request.model_dump(exclude_unset=True),
                records_exported=0,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Metadata export failed: {str(e)}",
            )

    def get_export_history(
        self,
        user_id: Optional[int] = None,
        export_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[ExportAuditLogSchema], int]:
        """
        Get export history with filtering and pagination.

        Returns:
            Tuple of (audit logs, total count)
        """
        query = self.db.query(ExportAuditLog).join(User)

        # Apply filters
        if user_id:
            query = query.filter(ExportAuditLog.user_id == user_id)
        if export_type:
            query = query.filter(ExportAuditLog.export_type == export_type)
        if date_from:
            query = query.filter(ExportAuditLog.created_at >= date_from)
        if date_to:
            query = query.filter(ExportAuditLog.created_at <= date_to)

        # Get total count
        total_count = query.count()

        # Apply pagination and ordering
        logs = (
            query.order_by(desc(ExportAuditLog.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # Convert to schema objects
        log_schemas = []
        for log in logs:
            log_schemas.append(
                ExportAuditLogSchema(
                    id=log.id,
                    export_id=log.export_id,
                    user_id=log.user_id,
                    user_email=log.user.email,
                    export_type=log.export_type,
                    format=log.format,
                    filters_applied=log.filters_applied,
                    records_exported=log.records_exported,
                    file_size_bytes=log.file_size_bytes,
                    ip_address=log.ip_address,
                    user_agent=log.user_agent,
                    created_at=log.created_at,
                )
            )

        return log_schemas, total_count

    def _build_dataset_query(self, request: DatasetExportRequest):
        """Build SQLAlchemy query based on export request filters."""
        query = (
            self.db.query(AudioChunk, Transcription, VoiceRecording, User, Language)
            .join(Transcription, AudioChunk.id == Transcription.chunk_id)
            .join(VoiceRecording, AudioChunk.recording_id == VoiceRecording.id)
            .join(User, Transcription.user_id == User.id)
            .join(Language, Transcription.language_id == Language.id)
        )

        # Apply quality filters
        if request.quality_filters:
            qf = request.quality_filters
            if qf.min_confidence is not None:
                query = query.filter(Transcription.confidence >= qf.min_confidence)
            if qf.min_quality is not None:
                query = query.filter(Transcription.quality >= qf.min_quality)
            if qf.consensus_only:
                query = query.filter(Transcription.is_consensus.is_(True))
            if qf.validated_only:
                query = query.filter(Transcription.is_validated.is_(True))

        # Apply other filters
        if request.language_ids:
            query = query.filter(Language.id.in_(request.language_ids))
        if request.user_ids:
            query = query.filter(User.id.in_(request.user_ids))
        if request.date_from:
            query = query.filter(VoiceRecording.created_at >= request.date_from)
        if request.date_to:
            query = query.filter(VoiceRecording.created_at <= request.date_to)

        # Only include successfully processed recordings
        query = query.filter(VoiceRecording.status == RecordingStatus.CHUNKED)

        return query

    def _convert_to_export_items(self, results) -> List[ExportedDataItem]:
        """Convert query results to export data items."""
        items = []
        for chunk, transcription, recording, user, language in results:
            item = ExportedDataItem(
                chunk_id=chunk.id,
                recording_id=recording.id,
                audio_file_path=recording.file_path,
                chunk_file_path=chunk.file_path,
                transcription_text=transcription.text,
                transcription_id=transcription.id,
                contributor_id=user.id,
                language_id=language.id,
                language_name=language.name,
                quality_score=transcription.quality,
                confidence_score=transcription.confidence,
                is_consensus=transcription.is_consensus,
                is_validated=transcription.is_validated,
                recording_duration=recording.duration,
                chunk_duration=chunk.duration,
                chunk_start_time=chunk.start_time,
                chunk_end_time=chunk.end_time,
                created_at=transcription.created_at,
                metadata={
                    "recording_metadata": recording.meta_data,
                    "chunk_metadata": chunk.meta_data,
                    "transcription_metadata": transcription.meta_data,
                },
            )
            items.append(item)
        return items

    def _generate_export_statistics(
        self, results, request: DatasetExportRequest
    ) -> ExportStatistics:
        """Generate statistics for the exported dataset."""
        if not results:
            return ExportStatistics(
                total_recordings=0,
                total_chunks=0,
                total_transcriptions=0,
                consensus_transcriptions=0,
                validated_transcriptions=0,
                unique_contributors=0,
                languages=[],
                quality_distribution={},
                export_timestamp=datetime.utcnow(),
                filters_applied=request.dict(exclude_unset=True),
            )

        # Extract data from results
        recordings = set()
        chunks = set()
        transcriptions = []
        contributors = set()
        languages = {}

        for chunk, transcription, recording, user, language in results:
            recordings.add(recording.id)
            chunks.add(chunk.id)
            transcriptions.append(transcription)
            contributors.add(user.id)
            languages[language.id] = {"id": language.id, "name": language.name}

        # Calculate quality distribution
        quality_ranges = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        }
        for t in transcriptions:
            if t.quality < 0.2:
                quality_ranges["0.0-0.2"] += 1
            elif t.quality < 0.4:
                quality_ranges["0.2-0.4"] += 1
            elif t.quality < 0.6:
                quality_ranges["0.4-0.6"] += 1
            elif t.quality < 0.8:
                quality_ranges["0.6-0.8"] += 1
            else:
                quality_ranges["0.8-1.0"] += 1

        return ExportStatistics(
            total_recordings=len(recordings),
            total_chunks=len(chunks),
            total_transcriptions=len(transcriptions),
            consensus_transcriptions=sum(1 for t in transcriptions if t.is_consensus),
            validated_transcriptions=sum(1 for t in transcriptions if t.is_validated),
            unique_contributors=len(contributors),
            languages=list(languages.values()),
            quality_distribution=quality_ranges,
            export_timestamp=datetime.now(timezone.utc),
            filters_applied=request.model_dump(exclude_unset=True),
        )

    def _generate_platform_statistics(self) -> ExportStatistics:
        """Generate overall platform statistics."""
        # Get counts
        total_recordings = self.db.query(VoiceRecording).count()
        total_chunks = self.db.query(AudioChunk).count()
        total_transcriptions = self.db.query(Transcription).count()
        consensus_transcriptions = (
            self.db.query(Transcription)
            .filter(Transcription.is_consensus.is_(True))
            .count()
        )
        validated_transcriptions = (
            self.db.query(Transcription)
            .filter(Transcription.is_validated.is_(True))
            .count()
        )
        unique_contributors = self.db.query(User).count()

        # Get languages
        languages = self.db.query(Language).all()
        language_list = [{"id": lang.id, "name": lang.name} for lang in languages]

        # Get quality distribution
        quality_ranges = {
            "0.0-0.2": 0,
            "0.2-0.4": 0,
            "0.4-0.6": 0,
            "0.6-0.8": 0,
            "0.8-1.0": 0,
        }
        transcriptions = self.db.query(Transcription).all()
        for t in transcriptions:
            if t.quality < 0.2:
                quality_ranges["0.0-0.2"] += 1
            elif t.quality < 0.4:
                quality_ranges["0.2-0.4"] += 1
            elif t.quality < 0.6:
                quality_ranges["0.4-0.6"] += 1
            elif t.quality < 0.8:
                quality_ranges["0.6-0.8"] += 1
            else:
                quality_ranges["0.8-1.0"] += 1

        return ExportStatistics(
            total_recordings=total_recordings,
            total_chunks=total_chunks,
            total_transcriptions=total_transcriptions,
            consensus_transcriptions=consensus_transcriptions,
            validated_transcriptions=validated_transcriptions,
            unique_contributors=unique_contributors,
            languages=language_list,
            quality_distribution=quality_ranges,
            export_timestamp=datetime.now(timezone.utc),
            filters_applied={},
        )

    def _generate_platform_metrics(self) -> Dict[str, Any]:
        """Generate detailed platform metrics."""
        return {
            "processing_status": {
                "uploaded": self.db.query(VoiceRecording)
                .filter(VoiceRecording.status == RecordingStatus.UPLOADED)
                .count(),
                "processing": self.db.query(VoiceRecording)
                .filter(VoiceRecording.status == RecordingStatus.PROCESSING)
                .count(),
                "chunked": self.db.query(VoiceRecording)
                .filter(VoiceRecording.status == RecordingStatus.CHUNKED)
                .count(),
                "failed": self.db.query(VoiceRecording)
                .filter(VoiceRecording.status == RecordingStatus.FAILED)
                .count(),
            },
            "average_chunk_duration": self.db.query(
                func.avg(AudioChunk.duration)
            ).scalar()
            or 0.0,
            "average_recording_duration": self.db.query(
                func.avg(VoiceRecording.duration)
            ).scalar()
            or 0.0,
            "transcriptions_per_chunk": self.db.query(
                func.count(Transcription.id)
            ).scalar()
            / max(self.db.query(AudioChunk).count(), 1),
        }

    def _generate_user_statistics(self) -> List[Dict[str, Any]]:
        """Generate per-user statistics."""
        users = self.db.query(User).all()
        user_stats = []

        for user in users:
            recordings_count = (
                self.db.query(VoiceRecording)
                .filter(VoiceRecording.user_id == user.id)
                .count()
            )
            transcriptions_count = (
                self.db.query(Transcription)
                .filter(Transcription.user_id == user.id)
                .count()
            )
            avg_quality = (
                self.db.query(func.avg(Transcription.quality))
                .filter(Transcription.user_id == user.id)
                .scalar()
                or 0.0
            )

            user_stats.append(
                {
                    "user_id": user.id,
                    "user_email": user.email,
                    "role": user.role.value,
                    "recordings_count": recordings_count,
                    "transcriptions_count": transcriptions_count,
                    "average_quality": float(avg_quality),
                    "created_at": user.created_at,
                }
            )

        return user_stats

    def _generate_quality_metrics(self) -> Dict[str, Any]:
        """Generate quality-related metrics."""
        return {
            "average_quality_score": self.db.query(
                func.avg(Transcription.quality)
            ).scalar()
            or 0.0,
            "average_confidence_score": self.db.query(
                func.avg(Transcription.confidence)
            ).scalar()
            or 0.0,
            "consensus_rate": (
                self.db.query(Transcription)
                .filter(Transcription.is_consensus.is_(True))
                .count()
                / max(self.db.query(Transcription).count(), 1)
            )
            * 100,
            "validation_rate": (
                self.db.query(Transcription)
                .filter(Transcription.is_validated.is_(True))
                .count()
                / max(self.db.query(Transcription).count(), 1)
            )
            * 100,
        }

    def _log_export_activity(
        self,
        export_id: str,
        user: User,
        export_type: str,
        format: ExportFormat,
        filters: Dict[str, Any],
        records_exported: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
    ):
        """Log export activity for audit purposes."""
        audit_log = ExportAuditLog(
            export_id=export_id,
            user_id=user.id,
            export_type=export_type,
            format=format.value,
            filters_applied=filters,
            records_exported=records_exported,
            file_size_bytes=file_size_bytes,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        self.db.add(audit_log)
        self.db.commit()
