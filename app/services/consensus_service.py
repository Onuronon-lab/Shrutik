"""
Consensus and Quality Validation Service

This service implements the consensus engine to compare multiple transcriptions
per chunk, calculate quality scores, and manage validation status with audit trails.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass
from difflib import SequenceMatcher
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.transcription import Transcription
from app.models.quality_review import QualityReview, ReviewDecision
from app.models.audio_chunk import AudioChunk
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
        transcriptions = self.db.query(Transcription).filter(
            Transcription.chunk_id == chunk_id
        ).all()
        
        if len(transcriptions) < self.MIN_TRANSCRIPTIONS_FOR_CONSENSUS:
            logger.info(f"Chunk {chunk_id} has only {len(transcriptions)} transcriptions, "
                       f"minimum {self.MIN_TRANSCRIPTIONS_FOR_CONSENSUS} required")
            return ConsensusResult(
                chunk_id=chunk_id,
                consensus_text="",
                confidence_score=0.0,
                requires_review=True,
                participant_count=len(transcriptions),
                quality_score=0.0,
                transcription_similarities=[],
                flagged_reasons=["Insufficient transcriptions"]
            )
        
        # Calculate pairwise similarities
        similarities = self._calculate_pairwise_similarities(transcriptions)
        
        # Find consensus text
        consensus_text, consensus_confidence = self._find_consensus_text(transcriptions, similarities)
        
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
            flagged_reasons=flagged_reasons
        )
        
        logger.info(f"Consensus evaluation completed for chunk {chunk_id}: "
                   f"confidence={consensus_confidence:.3f}, requires_review={requires_review}")
        
        return result
    
    def update_chunk_validation_status(self, consensus_result: ConsensusResult) -> ValidationStatus:
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
        transcriptions = self.db.query(Transcription).filter(
            Transcription.chunk_id == chunk_id
        ).all()
        
        for transcription in transcriptions:
            # Mark consensus transcription
            transcription.is_consensus = (transcription.id == consensus_transcription_id)
            
            # Update validation status
            transcription.is_validated = not consensus_result.requires_review
            
            # Update quality and confidence scores
            transcription.quality = consensus_result.quality_score
            transcription.confidence = consensus_result.confidence_score
            
            # Update metadata with consensus information
            if transcription.meta_data is None:
                transcription.meta_data = {}
            
            transcription.meta_data.update({
                "consensus_evaluation": {
                    "evaluated_at": datetime.now(timezone.utc).isoformat(),
                    "participant_count": consensus_result.participant_count,
                    "requires_review": consensus_result.requires_review,
                    "flagged_reasons": consensus_result.flagged_reasons,
                    "similarity_scores": consensus_result.transcription_similarities
                }
            })
        
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
            last_updated=datetime.now(timezone.utc)
        )
        
        logger.info(f"Updated validation status for chunk {chunk_id}: "
                   f"validated={validation_status.is_validated}")
        
        return validation_status
    
    def get_chunks_requiring_review(
        self, 
        limit: int = 50, 
        skip: int = 0
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
        query = self.db.query(AudioChunk).join(Transcription).filter(
            and_(
                Transcription.is_validated == False,
                Transcription.meta_data.op('->>')('consensus_evaluation').op('->>')('requires_review') == 'true'
            )
        ).distinct()
        
        chunks = query.offset(skip).limit(limit).all()
        
        result = []
        for chunk in chunks:
            # Get transcriptions for this chunk
            transcriptions = self.db.query(Transcription).filter(
                Transcription.chunk_id == chunk.id
            ).all()
            
            # Get flagged reasons from metadata
            flagged_reasons = []
            for transcription in transcriptions:
                if (transcription.meta_data and 
                    'consensus_evaluation' in transcription.meta_data and
                    'flagged_reasons' in transcription.meta_data['consensus_evaluation']):
                    flagged_reasons.extend(
                        transcription.meta_data['consensus_evaluation']['flagged_reasons']
                    )
            
            result.append({
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
                        "confidence": t.confidence
                    }
                    for t in transcriptions
                ]
            })
        
        return result
    
    def manual_review_decision(
        self, 
        chunk_id: int, 
        reviewer_id: int, 
        decision: ReviewDecision,
        selected_transcription_id: Optional[int] = None,
        comment: Optional[str] = None
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
            transcriptions = self.db.query(Transcription).filter(
                Transcription.chunk_id == chunk_id
            ).all()
            
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
                        "reviewed_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                self.db.add(quality_review)
            
            # Update transcription status based on decision
            if decision == ReviewDecision.APPROVED:
                # Mark all as validated
                for transcription in transcriptions:
                    transcription.is_validated = True
                    transcription.is_consensus = (
                        transcription.id == selected_transcription_id 
                        if selected_transcription_id else False
                    )
                    
                    # Update metadata
                    if transcription.meta_data is None:
                        transcription.meta_data = {}
                    
                    transcription.meta_data.update({
                        "manual_review": {
                            "reviewed_at": datetime.now(timezone.utc).isoformat(),
                            "reviewer_id": reviewer_id,
                            "decision": decision.value,
                            "comment": comment
                        }
                    })
            
            elif decision == ReviewDecision.REJECTED:
                # Mark all as requiring revision
                for transcription in transcriptions:
                    transcription.is_validated = False
                    transcription.is_consensus = False
            
            self.db.commit()
            
            logger.info(f"Manual review decision recorded for chunk {chunk_id}: {decision.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record manual review decision for chunk {chunk_id}: {e}")
            self.db.rollback()
            return False
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about validation status across all chunks.
        
        Returns:
            Dictionary with validation statistics
        """
        # Total chunks with transcriptions
        total_chunks_with_transcriptions = self.db.query(AudioChunk.id).join(Transcription).distinct().count()
        
        # Validated chunks
        validated_chunks = self.db.query(AudioChunk.id).join(Transcription).filter(
            Transcription.is_validated == True
        ).distinct().count()
        
        # Chunks requiring review
        chunks_requiring_review = self.db.query(AudioChunk.id).join(Transcription).filter(
            and_(
                Transcription.is_validated == False,
                Transcription.meta_data.op('->>')('consensus_evaluation').op('->>')('requires_review') == 'true'
            )
        ).distinct().count()
        
        # Consensus transcriptions
        consensus_transcriptions = self.db.query(Transcription).filter(
            Transcription.is_consensus == True
        ).count()
        
        # Average confidence scores
        avg_confidence = self.db.query(func.avg(Transcription.confidence)).filter(
            Transcription.is_validated == True
        ).scalar() or 0.0
        
        # Average quality scores
        avg_quality = self.db.query(func.avg(Transcription.quality)).filter(
            Transcription.is_validated == True
        ).scalar() or 0.0
        
        # Quality reviews by decision
        review_stats = self.db.query(
            QualityReview.decision,
            func.count(QualityReview.id).label('count')
        ).group_by(QualityReview.decision).all()
        
        review_counts = {decision.value: 0 for decision in ReviewDecision}
        for stat in review_stats:
            review_counts[stat.decision.value] = stat.count
        
        return {
            "total_chunks_with_transcriptions": total_chunks_with_transcriptions,
            "validated_chunks": validated_chunks,
            "chunks_requiring_review": chunks_requiring_review,
            "consensus_transcriptions": consensus_transcriptions,
            "validation_rate": (validated_chunks / total_chunks_with_transcriptions * 100) 
                              if total_chunks_with_transcriptions > 0 else 0.0,
            "average_confidence_score": round(float(avg_confidence), 3),
            "average_quality_score": round(float(avg_quality), 3),
            "quality_review_counts": review_counts
        }
    
    def _calculate_pairwise_similarities(self, transcriptions: List[Transcription]) -> List[float]:
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
        self, 
        transcriptions: List[Transcription], 
        similarities: List[float]
    ) -> Tuple[str, float]:
        """Find the consensus text and confidence score."""
        if not transcriptions:
            return "", 0.0
        
        if len(transcriptions) == 1:
            return transcriptions[0].text, 0.5  # Low confidence for single transcription
        
        # Calculate average similarity for each transcription
        texts = [t.text for t in transcriptions]
        text_scores = {}
        
        for i, text in enumerate(texts):
            scores = []
            for j, other_text in enumerate(texts):
                if i != j:
                    similarity = SequenceMatcher(None, text.lower(), other_text.lower()).ratio()
                    scores.append(similarity)
            
            text_scores[i] = statistics.mean(scores) if scores else 0.0
        
        # Find text with highest average similarity
        best_index = max(text_scores.keys(), key=lambda k: text_scores[k])
        consensus_text = texts[best_index]
        confidence = text_scores[best_index]
        
        return consensus_text, confidence
    
    def _calculate_quality_score(
        self, 
        transcriptions: List[Transcription], 
        similarities: List[float]
    ) -> float:
        """Calculate overall quality score based on transcription agreement."""
        if not similarities:
            return 0.0
        
        # Base quality on average similarity
        avg_similarity = statistics.mean(similarities)
        
        # Adjust for number of transcriptions (more transcriptions = higher confidence)
        transcription_count_factor = min(len(transcriptions) / 5.0, 1.0)  # Cap at 5 transcriptions
        
        # Adjust for length consistency
        lengths = [len(t.text) for t in transcriptions]
        if len(lengths) > 1:
            length_std = statistics.stdev(lengths)
            avg_length = statistics.mean(lengths)
            length_consistency = 1.0 - min(length_std / avg_length, 1.0) if avg_length > 0 else 0.0
        else:
            length_consistency = 1.0
        
        # Combine factors
        quality_score = (
            avg_similarity * 0.6 +
            transcription_count_factor * 0.2 +
            length_consistency * 0.2
        )
        
        return min(quality_score, 1.0)
    
    def _requires_manual_review(
        self, 
        transcriptions: List[Transcription], 
        similarities: List[float],
        consensus_confidence: float,
        flagged_reasons: List[str]
    ) -> bool:
        """Determine if manual review is required."""
        requires_review = False
        
        # Low consensus confidence
        if consensus_confidence < self.LOW_CONFIDENCE_THRESHOLD:
            flagged_reasons.append(f"Low consensus confidence: {consensus_confidence:.3f}")
            requires_review = True
        
        # Low average similarity
        if similarities and statistics.mean(similarities) < self.CONSENSUS_SIMILARITY_THRESHOLD:
            avg_sim = statistics.mean(similarities)
            flagged_reasons.append(f"Low transcription similarity: {avg_sim:.3f}")
            requires_review = True
        
        # Large length differences
        lengths = [len(t.text) for t in transcriptions]
        if len(lengths) > 1:
            max_length = max(lengths)
            min_length = min(lengths)
            if max_length > 0 and (max_length - min_length) / max_length > self.MAX_TRANSCRIPTION_LENGTH_DIFF:
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
    
    def _create_or_update_consensus_transcription(self, consensus_result: ConsensusResult) -> Optional[int]:
        """Create or update the consensus transcription for a chunk."""
        # Find the transcription that matches the consensus text most closely
        transcriptions = self.db.query(Transcription).filter(
            Transcription.chunk_id == consensus_result.chunk_id
        ).all()
        
        best_match_id = None
        best_similarity = 0.0
        
        for transcription in transcriptions:
            similarity = SequenceMatcher(
                None, 
                transcription.text.lower(), 
                consensus_result.consensus_text.lower()
            ).ratio()
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = transcription.id
        
        return best_match_id
    
    def _create_automatic_quality_review(self, consensus_result: ConsensusResult) -> None:
        """Create automatic quality review records for flagged transcriptions."""
        transcriptions = self.db.query(Transcription).filter(
            Transcription.chunk_id == consensus_result.chunk_id
        ).all()
        
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
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            )
            self.db.add(quality_review)