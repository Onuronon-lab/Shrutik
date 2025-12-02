"""
Consensus and Quality Validation Service

This service implements the consensus engine for export optimization.
It calculates consensus quality for chunks with multiple transcriptions,
marks chunks ready for export when quality thresholds are met, and uses
Redis locks to prevent duplicate calculations.
"""

import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.export_metrics import consensus_metrics_collector
from app.core.redis_client import redis_client
from app.models.audio_chunk import AudioChunk
from app.models.quality_review import QualityReview, ReviewDecision
from app.models.transcription import Transcription
from app.models.user import User

logger = logging.getLogger(__name__)


@dataclass
class ConsensusResult:
    """Result of consensus evaluation for a chunk."""

    chunk_id: int
    consensus_text: str
    confidence_score: float
    requires_review: bool
    participant_count: int
    quality_score: float
    transcription_similarities: List[float]
    flagged_reasons: List[str]


@dataclass
class ValidationStatus:
    """Validation status for a chunk."""

    chunk_id: int
    is_validated: bool
    consensus_transcription_id: Optional[int]
    validation_confidence: float
    requires_manual_review: bool
    last_updated: datetime


class ConsensusService:
    """Service for consensus calculation and quality validation."""

    # Configuration constants
    MIN_TRANSCRIPTIONS_FOR_CONSENSUS = 2
    CONSENSUS_SIMILARITY_THRESHOLD = 0.7  # 70% similarity required
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    LOW_CONFIDENCE_THRESHOLD = 0.5
    MAX_TRANSCRIPTION_LENGTH_DIFF = 0.3  # 30% length difference tolerance

    def __init__(self, db: Session):
        self.db = db

    def evaluate_chunk_consensus(self, chunk_id: int) -> ConsensusResult:
        """
        Evaluate consensus for a chunk based on all its transcriptions.

        Args:
            chunk_id: ID of the audio chunk to evaluate

        Returns:
            ConsensusResult with consensus text and quality metrics
        """
        logger.info(f"Evaluating consensus for chunk {chunk_id}")

        # Get all transcriptions for this chunk
        transcriptions = (
            self.db.query(Transcription)
            .filter(Transcription.chunk_id == chunk_id)
            .all()
        )

        if len(transcriptions) < self.MIN_TRANSCRIPTIONS_FOR_CONSENSUS:
            logger.info(
                f"Chunk {chunk_id} has only {len(transcriptions)} transcriptions, "
                f"minimum {self.MIN_TRANSCRIPTIONS_FOR_CONSENSUS} required"
            )
            return ConsensusResult(
                chunk_id=chunk_id,
                consensus_text="",
                confidence_score=0.0,
                requires_review=True,
                participant_count=len(transcriptions),
                quality_score=0.0,
                transcription_similarities=[],
                flagged_reasons=["Insufficient transcriptions"],
            )

        # Calculate pairwise similarities
        similarities = self._calculate_pairwise_similarities(transcriptions)

        # Find consensus text
        consensus_text, consensus_confidence = self._find_consensus_text(
            transcriptions, similarities
        )

        # Calculate overall quality score
        quality_score = self._calculate_quality_score(transcriptions, similarities)

        # Determine if manual review is required
        flagged_reasons = []
        requires_review = self._requires_manual_review(
            transcriptions, similarities, consensus_confidence, flagged_reasons
        )

        result = ConsensusResult(
            chunk_id=chunk_id,
            consensus_text=consensus_text,
            confidence_score=consensus_confidence,
            requires_review=requires_review,
            participant_count=len(transcriptions),
            quality_score=quality_score,
            transcription_similarities=similarities,
            flagged_reasons=flagged_reasons,
        )

        logger.info(
            f"Consensus evaluation completed for chunk {chunk_id}: "
            f"confidence={consensus_confidence:.3f}, requires_review={requires_review}"
        )

        return result

    def update_chunk_validation_status(
        self, consensus_result: ConsensusResult
    ) -> ValidationStatus:
        """
        Update the validation status of a chunk based on consensus results.

        Args:
            consensus_result: Result from consensus evaluation

        Returns:
            ValidationStatus with updated validation information
        """
        chunk_id = consensus_result.chunk_id

        # Get or create consensus transcription
        consensus_transcription_id = None
        if consensus_result.consensus_text and not consensus_result.requires_review:
            consensus_transcription_id = self._create_or_update_consensus_transcription(
                consensus_result
            )

        # Update all transcriptions for this chunk
        transcriptions = (
            self.db.query(Transcription)
            .filter(Transcription.chunk_id == chunk_id)
            .all()
        )

        for transcription in transcriptions:
            # Mark consensus transcription
            transcription.is_consensus = transcription.id == consensus_transcription_id

            # Update validation status
            transcription.is_validated = not consensus_result.requires_review

            # Update quality and confidence scores
            transcription.quality = consensus_result.quality_score
            transcription.confidence = consensus_result.confidence_score

            # Update metadata with consensus information
            if transcription.meta_data is None:
                transcription.meta_data = {}

            transcription.meta_data.update(
                {
                    "consensus_evaluation": {
                        "evaluated_at": datetime.now(timezone.utc).isoformat(),
                        "participant_count": consensus_result.participant_count,
                        "requires_review": consensus_result.requires_review,
                        "flagged_reasons": consensus_result.flagged_reasons,
                        "similarity_scores": consensus_result.transcription_similarities,
                    }
                }
            )

        # Create quality review record if flagged
        if consensus_result.requires_review:
            self._create_automatic_quality_review(consensus_result)

        self.db.commit()

        validation_status = ValidationStatus(
            chunk_id=chunk_id,
            is_validated=not consensus_result.requires_review,
            consensus_transcription_id=consensus_transcription_id,
            validation_confidence=consensus_result.confidence_score,
            requires_manual_review=consensus_result.requires_review,
            last_updated=datetime.now(timezone.utc),
        )

        logger.info(
            f"Updated validation status for chunk {chunk_id}: "
            f"validated={validation_status.is_validated}"
        )

        return validation_status

    def get_chunks_requiring_review(
        self, limit: int = 50, skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get chunks that require manual review.

        Args:
            limit: Maximum number of chunks to return
            skip: Number of chunks to skip for pagination

        Returns:
            List of chunk information requiring review
        """
        # Find chunks with transcriptions requiring review
        query = (
            self.db.query(AudioChunk)
            .join(Transcription)
            .filter(
                and_(
                    Transcription.is_validated == False,
                    Transcription.meta_data.op("->>")("consensus_evaluation").op("->>")(
                        "requires_review"
                    )
                    == "true",
                )
            )
            .distinct()
        )

        chunks = query.offset(skip).limit(limit).all()

        result = []
        for chunk in chunks:
            # Get transcriptions for this chunk
            transcriptions = (
                self.db.query(Transcription)
                .filter(Transcription.chunk_id == chunk.id)
                .all()
            )

            # Get flagged reasons from metadata
            flagged_reasons = []
            for transcription in transcriptions:
                if (
                    transcription.meta_data
                    and "consensus_evaluation" in transcription.meta_data
                    and "flagged_reasons"
                    in transcription.meta_data["consensus_evaluation"]
                ):
                    flagged_reasons.extend(
                        transcription.meta_data["consensus_evaluation"][
                            "flagged_reasons"
                        ]
                    )

            result.append(
                {
                    "chunk_id": chunk.id,
                    "recording_id": chunk.recording_id,
                    "duration": chunk.duration,
                    "transcription_count": len(transcriptions),
                    "flagged_reasons": list(set(flagged_reasons)),
                    "transcriptions": [
                        {
                            "id": t.id,
                            "text": t.text,
                            "user_id": t.user_id,
                            "quality": t.quality,
                            "confidence": t.confidence,
                        }
                        for t in transcriptions
                    ],
                }
            )

        return result

    def manual_review_decision(
        self,
        chunk_id: int,
        reviewer_id: int,
        decision: ReviewDecision,
        selected_transcription_id: Optional[int] = None,
        comment: Optional[str] = None,
    ) -> bool:
        """
        Record a manual review decision for a chunk.

        Args:
            chunk_id: ID of the chunk being reviewed
            reviewer_id: ID of the reviewer
            decision: Review decision
            selected_transcription_id: ID of transcription to mark as consensus (if approved)
            comment: Optional review comment

        Returns:
            True if review was recorded successfully
        """
        try:
            # Get transcriptions for this chunk
            transcriptions = (
                self.db.query(Transcription)
                .filter(Transcription.chunk_id == chunk_id)
                .all()
            )

            if not transcriptions:
                logger.error(f"No transcriptions found for chunk {chunk_id}")
                return False

            # Create quality review records
            for transcription in transcriptions:
                quality_review = QualityReview(
                    transcription_id=transcription.id,
                    reviewer_id=reviewer_id,
                    decision=decision,
                    comment=comment,
                    meta_data={
                        "chunk_id": chunk_id,
                        "review_type": "manual_consensus_review",
                        "reviewed_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                self.db.add(quality_review)

            # Update transcription status based on decision
            if decision == ReviewDecision.APPROVED:
                # Mark all as validated
                for transcription in transcriptions:
                    transcription.is_validated = True
                    transcription.is_consensus = (
                        transcription.id == selected_transcription_id
                        if selected_transcription_id
                        else False
                    )

                    # Update metadata
                    if transcription.meta_data is None:
                        transcription.meta_data = {}

                    transcription.meta_data.update(
                        {
                            "manual_review": {
                                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                                "reviewer_id": reviewer_id,
                                "decision": decision.value,
                                "comment": comment,
                            }
                        }
                    )

            elif decision == ReviewDecision.REJECTED:
                # Mark all as requiring revision
                for transcription in transcriptions:
                    transcription.is_validated = False
                    transcription.is_consensus = False

            self.db.commit()

            logger.info(
                f"Manual review decision recorded for chunk {chunk_id}: {decision.value}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to record manual review decision for chunk {chunk_id}: {e}"
            )
            self.db.rollback()
            return False

    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about validation status across all chunks.

        Returns:
            Dictionary with validation statistics
        """
        # Total chunks with transcriptions
        total_chunks_with_transcriptions = (
            self.db.query(AudioChunk.id).join(Transcription).distinct().count()
        )

        # Validated chunks
        validated_chunks = (
            self.db.query(AudioChunk.id)
            .join(Transcription)
            .filter(Transcription.is_validated == True)
            .distinct()
            .count()
        )

        # Chunks requiring review
        chunks_requiring_review = (
            self.db.query(AudioChunk.id)
            .join(Transcription)
            .filter(
                and_(
                    Transcription.is_validated == False,
                    Transcription.meta_data.op("->>")("consensus_evaluation").op("->>")(
                        "requires_review"
                    )
                    == "true",
                )
            )
            .distinct()
            .count()
        )

        # Consensus transcriptions
        consensus_transcriptions = (
            self.db.query(Transcription)
            .filter(Transcription.is_consensus == True)
            .count()
        )

        # Average confidence scores
        avg_confidence = (
            self.db.query(func.avg(Transcription.confidence))
            .filter(Transcription.is_validated == True)
            .scalar()
            or 0.0
        )

        # Average quality scores
        avg_quality = (
            self.db.query(func.avg(Transcription.quality))
            .filter(Transcription.is_validated == True)
            .scalar()
            or 0.0
        )

        # Quality reviews by decision
        review_stats = (
            self.db.query(
                QualityReview.decision, func.count(QualityReview.id).label("count")
            )
            .group_by(QualityReview.decision)
            .all()
        )

        review_counts = {decision.value: 0 for decision in ReviewDecision}
        for stat in review_stats:
            review_counts[stat.decision.value] = stat.count

        return {
            "total_chunks_with_transcriptions": total_chunks_with_transcriptions,
            "validated_chunks": validated_chunks,
            "chunks_requiring_review": chunks_requiring_review,
            "consensus_transcriptions": consensus_transcriptions,
            "validation_rate": (
                (validated_chunks / total_chunks_with_transcriptions * 100)
                if total_chunks_with_transcriptions > 0
                else 0.0
            ),
            "average_confidence_score": round(float(avg_confidence), 3),
            "average_quality_score": round(float(avg_quality), 3),
            "quality_review_counts": review_counts,
        }

    def _calculate_pairwise_similarities(
        self, transcriptions: List[Transcription]
    ) -> List[float]:
        """Calculate pairwise text similarities between transcriptions."""
        if len(transcriptions) < 2:
            return []

        similarities = []
        texts = [t.text.strip().lower() for t in transcriptions]

        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = SequenceMatcher(None, texts[i], texts[j]).ratio()
                similarities.append(similarity)

        return similarities

    def _find_consensus_text(
        self, transcriptions: List[Transcription], similarities: List[float]
    ) -> Tuple[str, float]:
        """Find the consensus text and confidence score."""
        if not transcriptions:
            return "", 0.0

        if len(transcriptions) == 1:
            return (
                transcriptions[0].text,
                0.5,
            )  # Low confidence for single transcription

        # Calculate average similarity for each transcription
        texts = [t.text for t in transcriptions]
        text_scores = {}

        for i, text in enumerate(texts):
            scores = []
            for j, other_text in enumerate(texts):
                if i != j:
                    similarity = SequenceMatcher(
                        None, text.lower(), other_text.lower()
                    ).ratio()
                    scores.append(similarity)

            text_scores[i] = statistics.mean(scores) if scores else 0.0

        # Find text with highest average similarity
        best_index = max(text_scores.keys(), key=lambda k: text_scores[k])
        consensus_text = texts[best_index]
        confidence = text_scores[best_index]

        return consensus_text, confidence

    def _calculate_quality_score(
        self, transcriptions: List[Transcription], similarities: List[float]
    ) -> float:
        """Calculate overall quality score based on transcription agreement."""
        if not similarities:
            return 0.0

        # Base quality on average similarity
        avg_similarity = statistics.mean(similarities)

        # Adjust for number of transcriptions (more transcriptions = higher confidence)
        transcription_count_factor = min(
            len(transcriptions) / 5.0, 1.0
        )  # Cap at 5 transcriptions

        # Adjust for length consistency
        lengths = [len(t.text) for t in transcriptions]
        if len(lengths) > 1:
            length_std = statistics.stdev(lengths)
            avg_length = statistics.mean(lengths)
            length_consistency = (
                1.0 - min(length_std / avg_length, 1.0) if avg_length > 0 else 0.0
            )
        else:
            length_consistency = 1.0

        # Combine factors
        quality_score = (
            avg_similarity * 0.6
            + transcription_count_factor * 0.2
            + length_consistency * 0.2
        )

        return min(quality_score, 1.0)

    def _requires_manual_review(
        self,
        transcriptions: List[Transcription],
        similarities: List[float],
        consensus_confidence: float,
        flagged_reasons: List[str],
    ) -> bool:
        """Determine if manual review is required."""
        requires_review = False

        # Low consensus confidence
        if consensus_confidence < self.LOW_CONFIDENCE_THRESHOLD:
            flagged_reasons.append(
                f"Low consensus confidence: {consensus_confidence:.3f}"
            )
            requires_review = True

        # Low average similarity
        if (
            similarities
            and statistics.mean(similarities) < self.CONSENSUS_SIMILARITY_THRESHOLD
        ):
            avg_sim = statistics.mean(similarities)
            flagged_reasons.append(f"Low transcription similarity: {avg_sim:.3f}")
            requires_review = True

        # Large length differences
        lengths = [len(t.text) for t in transcriptions]
        if len(lengths) > 1:
            max_length = max(lengths)
            min_length = min(lengths)
            if (
                max_length > 0
                and (max_length - min_length) / max_length
                > self.MAX_TRANSCRIPTION_LENGTH_DIFF
            ):
                flagged_reasons.append("Large transcription length differences")
                requires_review = True

        # Very short or very long transcriptions
        for transcription in transcriptions:
            if len(transcription.text.strip()) < 5:
                flagged_reasons.append("Very short transcription detected")
                requires_review = True
            elif len(transcription.text.strip()) > 500:
                flagged_reasons.append("Very long transcription detected")
                requires_review = True

        return requires_review

    def _create_or_update_consensus_transcription(
        self, consensus_result: ConsensusResult
    ) -> Optional[int]:
        """Create or update the consensus transcription for a chunk."""
        # Find the transcription that matches the consensus text most closely
        transcriptions = (
            self.db.query(Transcription)
            .filter(Transcription.chunk_id == consensus_result.chunk_id)
            .all()
        )

        best_match_id = None
        best_similarity = 0.0

        for transcription in transcriptions:
            similarity = SequenceMatcher(
                None,
                transcription.text.lower(),
                consensus_result.consensus_text.lower(),
            ).ratio()

            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = transcription.id

        return best_match_id

    def _create_automatic_quality_review(
        self, consensus_result: ConsensusResult
    ) -> None:
        """Create automatic quality review records for flagged transcriptions."""
        transcriptions = (
            self.db.query(Transcription)
            .filter(Transcription.chunk_id == consensus_result.chunk_id)
            .all()
        )

        for transcription in transcriptions:
            quality_review = QualityReview(
                transcription_id=transcription.id,
                reviewer_id=None,  # System-generated review
                decision=ReviewDecision.FLAGGED,
                comment=f"Automatically flagged: {', '.join(consensus_result.flagged_reasons)}",
                meta_data={
                    "automatic_review": True,
                    "consensus_confidence": consensus_result.confidence_score,
                    "quality_score": consensus_result.quality_score,
                    "flagged_reasons": consensus_result.flagged_reasons,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )
            self.db.add(quality_review)

    # ========================================================================
    # Export Optimization Methods
    # ========================================================================

    def calculate_consensus_for_chunk(self, chunk_id: int) -> Optional[Transcription]:
        """
        Calculate consensus for a single chunk for export optimization.

        This method:
        1. Checks if chunk has >= 5 transcriptions
        2. Calculates consensus quality score
        3. Selects consensus transcript
        4. Updates chunk fields: consensus_quality, ready_for_export, consensus_transcript_id
        5. Returns the consensus transcription if quality threshold (90%) is met

        Args:
            chunk_id: ID of the audio chunk

        Returns:
            Consensus transcription if quality >= 90%, None otherwise
        """
        # Acquire Redis lock to prevent duplicate calculations
        lock_key = f"consensus_lock:chunk_{chunk_id}"
        lock_timeout = 60  # 60 seconds

        # Try to acquire lock (use SET with NX option for atomic lock acquisition)
        try:
            # Check if lock already exists
            if redis_client.exists(lock_key):
                logger.info(
                    f"Consensus calculation already in progress for chunk {chunk_id}, skipping"
                )
                return None

            # Acquire lock
            redis_client.set(lock_key, "1", ex=lock_timeout)
        except Exception as e:
            logger.warning(f"Failed to acquire Redis lock for chunk {chunk_id}: {e}")
            # Continue anyway if Redis is unavailable

        try:
            # Get chunk
            chunk = self.db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()
            if not chunk:
                logger.error(f"Chunk {chunk_id} not found")
                return None

            # Get all transcriptions for this chunk
            transcriptions = (
                self.db.query(Transcription)
                .filter(Transcription.chunk_id == chunk_id)
                .all()
            )

            # Check minimum transcription count (5 required)
            if len(transcriptions) < 5:
                logger.info(
                    f"Chunk {chunk_id} has only {len(transcriptions)} transcriptions, "
                    f"minimum 5 required for export consensus",
                    extra={
                        "operation_type": "consensus_calculation",
                        "chunk_id": chunk_id,
                        "transcript_count": len(transcriptions),
                        "status": "insufficient_transcriptions",
                    },
                )
                # Update chunk but don't mark ready
                chunk.transcript_count = len(transcriptions)
                chunk.consensus_quality = 0.0
                chunk.ready_for_export = False
                self.db.commit()
                return None

            # Calculate quality score
            quality_score = self.calculate_quality_score(transcriptions)

            # Get consensus transcript
            consensus_transcript = self.get_consensus_transcript(transcriptions)

            # Update chunk fields
            chunk.transcript_count = len(transcriptions)
            chunk.consensus_quality = quality_score
            chunk.consensus_transcript_id = (
                consensus_transcript.id if consensus_transcript else None
            )

            # Check if quality meets export threshold (90%)
            if quality_score >= 0.90:
                chunk.ready_for_export = True
                chunk.consensus_failed_count = 0  # Reset failure count on success
                logger.info(
                    f"Chunk {chunk_id} marked ready for export with quality {quality_score:.3f}",
                    extra={
                        "operation_type": "consensus_calculation",
                        "chunk_id": chunk_id,
                        "transcript_count": len(transcriptions),
                        "consensus_quality": quality_score,
                        "ready_for_export": True,
                        "status": "success",
                    },
                )
            else:
                chunk.ready_for_export = False
                logger.info(
                    f"Chunk {chunk_id} quality {quality_score:.3f} below 90% threshold, "
                    f"not ready for export",
                    extra={
                        "operation_type": "consensus_calculation",
                        "chunk_id": chunk_id,
                        "transcript_count": len(transcriptions),
                        "consensus_quality": quality_score,
                        "ready_for_export": False,
                        "status": "below_threshold",
                    },
                )

            self.db.commit()
            self.db.refresh(chunk)

            # Record metrics
            consensus_metrics_collector.record_consensus_calculated(
                chunk_id=chunk_id,
                quality_score=quality_score,
                ready_for_export=chunk.ready_for_export,
            )

            return consensus_transcript if chunk.ready_for_export else None

        except Exception as e:
            logger.error(
                f"Error calculating consensus for chunk {chunk_id}: {e}",
                extra={
                    "operation_type": "consensus_calculation",
                    "chunk_id": chunk_id,
                    "error": str(e),
                    "status": "failed",
                },
                exc_info=True,
            )
            self.db.rollback()

            # Increment failure count
            try:
                chunk = (
                    self.db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()
                )
                if chunk:
                    chunk.consensus_failed_count = (
                        chunk.consensus_failed_count or 0
                    ) + 1
                    self.db.commit()
                    logger.warning(
                        f"Incremented consensus_failed_count for chunk {chunk_id} "
                        f"to {chunk.consensus_failed_count}",
                        extra={
                            "operation_type": "consensus_calculation",
                            "chunk_id": chunk_id,
                            "consensus_failed_count": chunk.consensus_failed_count,
                            "status": "failure_tracked",
                        },
                    )
            except Exception as inner_e:
                logger.error(
                    f"Failed to increment consensus_failed_count for chunk {chunk_id}: {inner_e}",
                    extra={
                        "operation_type": "consensus_calculation",
                        "chunk_id": chunk_id,
                        "error": str(inner_e),
                    },
                )
                self.db.rollback()

            # Record failure metrics
            consensus_metrics_collector.record_consensus_failed(
                chunk_id=chunk_id, error_message=str(inner_e)
            )

            return None

        finally:
            # Release lock
            redis_client.delete(lock_key)

    def calculate_consensus_for_chunks(self, chunk_ids: List[int]) -> Dict[int, bool]:
        """
        Bulk calculate consensus for multiple chunks.

        Args:
            chunk_ids: List of chunk IDs to process

        Returns:
            Dictionary mapping chunk_id to ready_for_export status
        """
        results = {}

        for chunk_id in chunk_ids:
            try:
                consensus_transcript = self.calculate_consensus_for_chunk(chunk_id)

                # Get updated chunk to check ready_for_export status
                chunk = (
                    self.db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()
                )
                if chunk:
                    results[chunk_id] = chunk.ready_for_export
                else:
                    results[chunk_id] = False

            except Exception as e:
                logger.error(
                    f"Error processing chunk {chunk_id} in bulk operation: {e}"
                )
                results[chunk_id] = False

        logger.info(
            f"Bulk consensus calculation completed for {len(chunk_ids)} chunks. "
            f"Ready for export: {sum(results.values())}",
            extra={
                "operation_type": "consensus_calculation_bulk",
                "chunk_count": len(chunk_ids),
                "ready_for_export_count": sum(results.values()),
                "status": "completed",
            },
        )

        return results

    def get_consensus_transcript(
        self, transcriptions: List[Transcription]
    ) -> Optional[Transcription]:
        """
        Determine the consensus transcript from multiple transcriptions.

        Uses quality scores and text similarity to select the best transcript.
        The transcript with the highest average similarity to all other transcripts
        is selected as the consensus.

        Args:
            transcriptions: List of transcriptions for a chunk

        Returns:
            The consensus transcription, or None if no suitable consensus found
        """
        if not transcriptions:
            return None

        if len(transcriptions) == 1:
            return transcriptions[0]

        # Calculate average similarity for each transcription
        best_transcription = None
        best_score = -1.0

        for candidate in transcriptions:
            # Calculate similarity to all other transcriptions
            similarities = []
            for other in transcriptions:
                if candidate.id != other.id:
                    similarity = SequenceMatcher(
                        None, candidate.text.strip().lower(), other.text.strip().lower()
                    ).ratio()
                    similarities.append(similarity)

            # Average similarity score
            avg_similarity = statistics.mean(similarities) if similarities else 0.0

            # Factor in quality score if available
            quality_factor = candidate.quality if candidate.quality else 0.5

            # Combined score (70% similarity, 30% quality)
            combined_score = (avg_similarity * 0.7) + (quality_factor * 0.3)

            if combined_score > best_score:
                best_score = combined_score
                best_transcription = candidate

        return best_transcription

    def calculate_quality_score(self, transcriptions: List[Transcription]) -> float:
        """
        Calculate aggregate quality score from multiple transcriptions.

        The quality score is based on:
        - Text similarity between transcriptions (60%)
        - Individual quality scores (20%)
        - Length consistency (20%)

        Args:
            transcriptions: List of transcriptions for a chunk

        Returns:
            Quality score between 0.0 and 1.0
        """
        if not transcriptions:
            return 0.0

        if len(transcriptions) == 1:
            # Single transcription gets its own quality score or 0.5 default
            return transcriptions[0].quality if transcriptions[0].quality else 0.5

        # Calculate pairwise text similarities
        similarities = []
        texts = [t.text.strip().lower() for t in transcriptions]

        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                similarity = SequenceMatcher(None, texts[i], texts[j]).ratio()
                similarities.append(similarity)

        avg_similarity = statistics.mean(similarities) if similarities else 0.0

        # Calculate average individual quality scores
        quality_scores = [t.quality for t in transcriptions if t.quality is not None]
        avg_quality = statistics.mean(quality_scores) if quality_scores else 0.5

        # Calculate length consistency
        lengths = [len(t.text) for t in transcriptions]
        if len(lengths) > 1 and statistics.mean(lengths) > 0:
            length_std = statistics.stdev(lengths)
            avg_length = statistics.mean(lengths)
            length_consistency = 1.0 - min(length_std / avg_length, 1.0)
        else:
            length_consistency = 1.0

        # Combine factors
        quality_score = (
            avg_similarity * 0.6 + avg_quality * 0.2 + length_consistency * 0.2
        )

        return min(max(quality_score, 0.0), 1.0)  # Clamp to [0, 1]
