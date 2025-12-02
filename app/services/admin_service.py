from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.models.audio_chunk import AudioChunk
from app.models.quality_review import QualityReview, ReviewDecision
from app.models.script import Script
from app.models.transcription import Transcription
from app.models.user import User, UserRole
from app.models.voice_recording import RecordingStatus, VoiceRecording
from app.schemas.admin import (
    FlaggedTranscriptionResponse,
    PlatformStatsResponse,
    QualityReviewItemResponse,
    SystemHealthResponse,
    UsageAnalyticsResponse,
    UserManagementResponse,
    UserStatsResponse,
)


class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_platform_statistics(self) -> PlatformStatsResponse:
        """Get comprehensive platform statistics."""
        # User counts by role
        user_counts = (
            self.db.query(User.role, func.count(User.id)).group_by(User.role).all()
        )

        user_stats = {role.value: 0 for role in UserRole}
        total_users = 0
        for role, count in user_counts:
            user_stats[role.value] = count
            total_users += count

        # Recording statistics
        total_recordings = self.db.query(func.count(VoiceRecording.id)).scalar() or 0
        avg_recording_duration = self.db.query(
            func.avg(VoiceRecording.duration)
        ).scalar()

        # Recording status breakdown
        recording_status_counts = (
            self.db.query(VoiceRecording.status, func.count(VoiceRecording.id))
            .group_by(VoiceRecording.status)
            .all()
        )

        recordings_by_status = {status.value: 0 for status in RecordingStatus}
        for status, count in recording_status_counts:
            recordings_by_status[status.value] = count

        # Chunk and transcription statistics
        total_chunks = self.db.query(func.count(AudioChunk.id)).scalar() or 0
        total_transcriptions = self.db.query(func.count(Transcription.id)).scalar() or 0
        total_validated = (
            self.db.query(func.count(Transcription.id))
            .filter(Transcription.is_validated == True)
            .scalar()
            or 0
        )

        # Transcription validation breakdown
        validated_count = (
            self.db.query(func.count(Transcription.id))
            .filter(Transcription.is_validated == True)
            .scalar()
            or 0
        )
        unvalidated_count = total_transcriptions - validated_count

        transcriptions_by_validation = {
            "validated": validated_count,
            "unvalidated": unvalidated_count,
        }

        # Quality statistics
        total_quality_reviews = (
            self.db.query(func.count(QualityReview.id)).scalar() or 0
        )
        avg_transcription_quality = self.db.query(
            func.avg(Transcription.quality)
        ).scalar()

        return PlatformStatsResponse(
            total_users=total_users,
            total_contributors=user_stats["contributor"],
            total_admins=user_stats["admin"],
            total_sworik_developers=user_stats["sworik_developer"],
            total_recordings=total_recordings,
            total_chunks=total_chunks,
            total_transcriptions=total_transcriptions,
            total_validated_transcriptions=total_validated,
            total_quality_reviews=total_quality_reviews,
            avg_recording_duration=avg_recording_duration,
            avg_transcription_quality=avg_transcription_quality,
            recordings_by_status=recordings_by_status,
            transcriptions_by_validation_status=transcriptions_by_validation,
        )

    def get_user_statistics(self, limit: int = 50) -> List[UserStatsResponse]:
        """Get detailed statistics for users."""
        # Query with subqueries for counts
        users_with_stats = (
            self.db.query(
                User,
                func.count(VoiceRecording.id).label("recordings_count"),
                func.count(Transcription.id).label("transcriptions_count"),
                func.count(QualityReview.id).label("quality_reviews_count"),
                func.avg(Transcription.quality).label("avg_quality"),
            )
            .outerjoin(VoiceRecording, User.id == VoiceRecording.user_id)
            .outerjoin(Transcription, User.id == Transcription.user_id)
            .outerjoin(QualityReview, User.id == QualityReview.reviewer_id)
            .group_by(User.id)
            .order_by(desc("recordings_count"), desc("transcriptions_count"))
            .limit(limit)
            .all()
        )

        result = []
        for user, rec_count, trans_count, review_count, avg_quality in users_with_stats:
            result.append(
                UserStatsResponse(
                    user_id=user.id,
                    name=user.name,
                    email=user.email,
                    role=user.role,
                    recordings_count=rec_count or 0,
                    transcriptions_count=trans_count or 0,
                    quality_reviews_count=review_count or 0,
                    avg_transcription_quality=(
                        float(avg_quality) if avg_quality else None
                    ),
                    created_at=user.created_at,
                )
            )

        return result

    def get_users_for_management(
        self, role_filter: Optional[UserRole] = None
    ) -> List[UserManagementResponse]:
        """Get users for management interface."""
        query = self.db.query(User)

        if role_filter:
            query = query.filter(User.role == role_filter)

        users = query.order_by(User.created_at.desc()).all()

        result = []
        for user in users:
            # Get user activity counts
            recordings_count = (
                self.db.query(func.count(VoiceRecording.id))
                .filter(VoiceRecording.user_id == user.id)
                .scalar()
                or 0
            )

            transcriptions_count = (
                self.db.query(func.count(Transcription.id))
                .filter(Transcription.user_id == user.id)
                .scalar()
                or 0
            )

            quality_reviews_count = (
                self.db.query(func.count(QualityReview.id))
                .filter(QualityReview.reviewer_id == user.id)
                .scalar()
                or 0
            )

            # Get last activity (most recent recording or transcription)
            last_recording = (
                self.db.query(func.max(VoiceRecording.created_at))
                .filter(VoiceRecording.user_id == user.id)
                .scalar()
            )

            last_transcription = (
                self.db.query(func.max(Transcription.created_at))
                .filter(Transcription.user_id == user.id)
                .scalar()
            )

            last_activity = None
            if last_recording and last_transcription:
                last_activity = max(last_recording, last_transcription)
            elif last_recording:
                last_activity = last_recording
            elif last_transcription:
                last_activity = last_transcription

            result.append(
                UserManagementResponse(
                    id=user.id,
                    name=user.name,
                    email=user.email,
                    role=user.role,
                    recordings_count=recordings_count,
                    transcriptions_count=transcriptions_count,
                    quality_reviews_count=quality_reviews_count,
                    created_at=user.created_at,
                    last_activity=last_activity,
                )
            )

        return result

    def update_user_role(self, user_id: int, new_role: UserRole) -> Optional[User]:
        """Update user role."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None

        user.role = new_role
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_quality_review_items(
        self, limit: int = 50
    ) -> List[QualityReviewItemResponse]:
        """Get quality review items with transcription details."""
        reviews = (
            self.db.query(
                QualityReview,
                Transcription.text,
                Transcription.chunk_id,
                User.name.label("contributor_name"),
                User.id.label("contributor_id"),
                AudioChunk.file_path,
                User.name.label("reviewer_name"),
            )
            .join(Transcription, QualityReview.transcription_id == Transcription.id)
            .join(AudioChunk, Transcription.chunk_id == AudioChunk.id)
            .join(User, Transcription.user_id == User.id)
            .outerjoin(User, QualityReview.reviewer_id == User.id)
            .order_by(QualityReview.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for (
            review,
            text,
            chunk_id,
            contributor_name,
            contributor_id,
            file_path,
            reviewer_name,
        ) in reviews:
            result.append(
                QualityReviewItemResponse(
                    id=review.id,
                    transcription_id=review.transcription_id,
                    chunk_id=chunk_id,
                    transcription_text=text,
                    contributor_name=contributor_name,
                    contributor_id=contributor_id,
                    decision=review.decision,
                    rating=review.rating,
                    comment=review.comment,
                    reviewer_name=reviewer_name,
                    created_at=review.created_at,
                    chunk_file_path=file_path,
                )
            )

        return result

    def get_flagged_transcriptions(
        self, limit: int = 50
    ) -> List[FlaggedTranscriptionResponse]:
        """Get transcriptions that need review (low quality or conflicting)."""
        # Get transcriptions with low quality scores or multiple conflicting transcriptions
        flagged = (
            self.db.query(
                Transcription,
                User.name.label("contributor_name"),
                AudioChunk.file_path,
                func.count(QualityReview.id).label("review_count"),
            )
            .join(User, Transcription.user_id == User.id)
            .join(AudioChunk, Transcription.chunk_id == AudioChunk.id)
            .outerjoin(
                QualityReview, Transcription.id == QualityReview.transcription_id
            )
            .filter(
                or_(
                    Transcription.quality < 0.7,  # Low quality threshold
                    Transcription.confidence < 0.6,  # Low confidence threshold
                    and_(
                        QualityReview.decision == ReviewDecision.FLAGGED,
                        QualityReview.id.isnot(None),
                    ),
                )
            )
            .group_by(Transcription.id, User.name, AudioChunk.file_path)
            .order_by(Transcription.quality.asc(), Transcription.confidence.asc())
            .limit(limit)
            .all()
        )

        result = []
        for transcription, contributor_name, file_path, review_count in flagged:
            result.append(
                FlaggedTranscriptionResponse(
                    transcription_id=transcription.id,
                    chunk_id=transcription.chunk_id,
                    text=transcription.text,
                    contributor_name=contributor_name,
                    contributor_id=transcription.user_id,
                    quality_score=transcription.quality,
                    confidence_score=transcription.confidence,
                    chunk_file_path=file_path,
                    created_at=transcription.created_at,
                    review_count=review_count or 0,
                )
            )

        return result

    def create_quality_review(
        self,
        transcription_id: int,
        reviewer_id: int,
        decision: ReviewDecision,
        rating: Optional[float] = None,
        comment: Optional[str] = None,
    ) -> QualityReview:
        """Create a new quality review."""
        review = QualityReview(
            transcription_id=transcription_id,
            reviewer_id=reviewer_id,
            decision=decision,
            rating=rating,
            comment=comment,
        )

        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review

    def get_system_health(self) -> SystemHealthResponse:
        """Get system health metrics."""
        # Database status (simple check)
        try:
            self.db.execute("SELECT 1")
            db_status = "healthy"
        except Exception:
            db_status = "unhealthy"

        # Active users in last 24h and 7d
        now = datetime.utcnow()
        day_ago = now - timedelta(days=1)
        week_ago = now - timedelta(days=7)

        active_24h = (
            self.db.query(func.count(func.distinct(User.id)))
            .join(VoiceRecording, User.id == VoiceRecording.user_id)
            .filter(VoiceRecording.created_at >= day_ago)
            .scalar()
            or 0
        )

        active_7d = (
            self.db.query(func.count(func.distinct(User.id)))
            .join(VoiceRecording, User.id == VoiceRecording.user_id)
            .filter(VoiceRecording.created_at >= week_ago)
            .scalar()
            or 0
        )

        # Failed recordings count
        failed_recordings = (
            self.db.query(func.count(VoiceRecording.id))
            .filter(VoiceRecording.status == RecordingStatus.FAILED)
            .scalar()
            or 0
        )

        # Processing queue size (recordings in processing state)
        processing_queue = (
            self.db.query(func.count(VoiceRecording.id))
            .filter(VoiceRecording.status == RecordingStatus.PROCESSING)
            .scalar()
            or 0
        )

        return SystemHealthResponse(
            database_status=db_status,
            active_users_last_24h=active_24h,
            active_users_last_7d=active_7d,
            processing_queue_size=processing_queue,
            failed_recordings_count=failed_recordings,
        )

    def get_usage_analytics(self, days: int = 30) -> UsageAnalyticsResponse:
        """Get usage analytics for the specified number of days."""
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        # Daily recordings
        daily_recordings = (
            self.db.query(
                func.date(VoiceRecording.created_at).label("date"),
                func.count(VoiceRecording.id).label("count"),
            )
            .filter(func.date(VoiceRecording.created_at) >= start_date)
            .group_by(func.date(VoiceRecording.created_at))
            .order_by("date")
            .all()
        )

        # Daily transcriptions
        daily_transcriptions = (
            self.db.query(
                func.date(Transcription.created_at).label("date"),
                func.count(Transcription.id).label("count"),
            )
            .filter(func.date(Transcription.created_at) >= start_date)
            .group_by(func.date(Transcription.created_at))
            .order_by("date")
            .all()
        )

        # User activity by role
        user_activity = (
            self.db.query(User.role, func.count(func.distinct(User.id)).label("count"))
            .join(VoiceRecording, User.id == VoiceRecording.user_id)
            .filter(VoiceRecording.created_at >= start_date)
            .group_by(User.role)
            .all()
        )

        # Popular script durations
        script_popularity = (
            self.db.query(
                Script.duration_category, func.count(VoiceRecording.id).label("count")
            )
            .join(VoiceRecording, Script.id == VoiceRecording.script_id)
            .filter(VoiceRecording.created_at >= start_date)
            .group_by(Script.duration_category)
            .all()
        )

        # Top contributors
        top_contributors = (
            self.db.query(
                User.id,
                User.name,
                (func.count(VoiceRecording.id) + func.count(Transcription.id)).label(
                    "contribution_count"
                ),
            )
            .outerjoin(VoiceRecording, User.id == VoiceRecording.user_id)
            .outerjoin(Transcription, User.id == Transcription.user_id)
            .group_by(User.id, User.name)
            .order_by(desc("contribution_count"))
            .limit(10)
            .all()
        )

        return UsageAnalyticsResponse(
            daily_recordings=[
                {"date": str(date), "count": count} for date, count in daily_recordings
            ],
            daily_transcriptions=[
                {"date": str(date), "count": count}
                for date, count in daily_transcriptions
            ],
            user_activity_by_role={role.value: count for role, count in user_activity},
            popular_script_durations={
                duration.value: count for duration, count in script_popularity
            },
            transcription_quality_trend=[],  # Could be implemented with more complex query
            top_contributors=[
                {"user_id": user_id, "name": name, "contribution_count": count}
                for user_id, name, count in top_contributors
            ],
        )
