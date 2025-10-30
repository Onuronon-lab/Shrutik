"""
Tests for consensus and quality validation functionality.

These tests cover the consensus engine, quality scoring algorithms,
and validation status management.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.services.consensus_service import ConsensusService
from app.models.transcription import Transcription
from app.models.quality_review import QualityReview, ReviewDecision
from app.models.audio_chunk import AudioChunk
from app.models.voice_recording import VoiceRecording, RecordingStatus
from app.models.user import User, UserRole
from app.models.language import Language


class TestConsensusService:
    """Test cases for the ConsensusService."""
    
    def test_evaluate_chunk_consensus_insufficient_transcriptions(self, db_session: Session, sample_chunk):
        """Test consensus evaluation with insufficient transcriptions."""
        consensus_service = ConsensusService(db_session)
        
        # Create only one transcription (below minimum)
        transcription = Transcription(
            chunk_id=sample_chunk.id,
            user_id=1,
            language_id=1,
            text="This is a test transcription."
        )
        db_session.add(transcription)
        db_session.commit()
        
        result = consensus_service.evaluate_chunk_consensus(sample_chunk.id)
        
        assert result.chunk_id == sample_chunk.id
        assert result.consensus_text == ""
        assert result.confidence_score == 0.0
        assert result.requires_review is True
        assert result.participant_count == 1
        assert "Insufficient transcriptions" in result.flagged_reasons
    
    def test_evaluate_chunk_consensus_high_similarity(self, db_session: Session, sample_chunk):
        """Test consensus evaluation with high similarity transcriptions."""
        consensus_service = ConsensusService(db_session)
        
        # Create similar transcriptions
        transcriptions = [
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=1,
                language_id=1,
                text="This is a test sentence."
            ),
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=2,
                language_id=1,
                text="This is a test sentence."
            ),
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=3,
                language_id=1,
                text="This is a test sentence"  # Minor difference
            )
        ]
        
        for t in transcriptions:
            db_session.add(t)
        db_session.commit()
        
        result = consensus_service.evaluate_chunk_consensus(sample_chunk.id)
        
        assert result.chunk_id == sample_chunk.id
        assert result.consensus_text == "This is a test sentence."
        assert result.confidence_score > 0.8  # High confidence
        assert result.requires_review is False
        assert result.participant_count == 3
        assert result.quality_score > 0.7
    
    def test_evaluate_chunk_consensus_low_similarity(self, db_session: Session, sample_chunk):
        """Test consensus evaluation with low similarity transcriptions."""
        consensus_service = ConsensusService(db_session)
        
        # Create dissimilar transcriptions
        transcriptions = [
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=1,
                language_id=1,
                text="This is a test sentence."
            ),
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=2,
                language_id=1,
                text="Completely different text here."
            ),
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=3,
                language_id=1,
                text="Another unrelated transcription."
            )
        ]
        
        for t in transcriptions:
            db_session.add(t)
        db_session.commit()
        
        result = consensus_service.evaluate_chunk_consensus(sample_chunk.id)
        
        assert result.chunk_id == sample_chunk.id
        assert result.requires_review is True
        assert result.participant_count == 3
        assert len(result.flagged_reasons) > 0
        assert any("similarity" in reason.lower() for reason in result.flagged_reasons)
    
    def test_update_chunk_validation_status(self, db_session: Session, sample_chunk):
        """Test updating chunk validation status."""
        consensus_service = ConsensusService(db_session)
        
        # Create transcriptions
        transcriptions = [
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=1,
                language_id=1,
                text="This is a test sentence."
            ),
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=2,
                language_id=1,
                text="This is a test sentence."
            )
        ]
        
        for t in transcriptions:
            db_session.add(t)
        db_session.commit()
        
        # Evaluate consensus
        consensus_result = consensus_service.evaluate_chunk_consensus(sample_chunk.id)
        
        # Update validation status
        validation_status = consensus_service.update_chunk_validation_status(consensus_result)
        
        assert validation_status.chunk_id == sample_chunk.id
        assert validation_status.is_validated == (not consensus_result.requires_review)
        
        # Check that transcriptions were updated
        updated_transcriptions = db_session.query(Transcription).filter(
            Transcription.chunk_id == sample_chunk.id
        ).all()
        
        for transcription in updated_transcriptions:
            assert transcription.is_validated == validation_status.is_validated
            assert transcription.quality == consensus_result.quality_score
            assert transcription.confidence == consensus_result.confidence_score
            assert "consensus_evaluation" in transcription.meta_data
    
    def test_manual_review_decision_approved(self, db_session: Session, sample_chunk, sample_user):
        """Test manual review decision with approval."""
        consensus_service = ConsensusService(db_session)
        
        # Create transcriptions
        transcriptions = [
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=1,
                language_id=1,
                text="First transcription."
            ),
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=2,
                language_id=1,
                text="Second transcription."
            )
        ]
        
        for t in transcriptions:
            db_session.add(t)
        db_session.commit()
        db_session.refresh(transcriptions[0])
        
        # Make manual review decision
        success = consensus_service.manual_review_decision(
            chunk_id=sample_chunk.id,
            reviewer_id=sample_user.id,
            decision=ReviewDecision.APPROVED,
            selected_transcription_id=transcriptions[0].id,
            comment="Approved after manual review"
        )
        
        assert success is True
        
        # Check that quality reviews were created
        reviews = db_session.query(QualityReview).filter(
            QualityReview.transcription_id.in_([t.id for t in transcriptions])
        ).all()
        
        assert len(reviews) == 2
        for review in reviews:
            assert review.decision == ReviewDecision.APPROVED
            assert review.reviewer_id == sample_user.id
            assert review.comment == "Approved after manual review"
        
        # Check that transcriptions were updated
        updated_transcriptions = db_session.query(Transcription).filter(
            Transcription.chunk_id == sample_chunk.id
        ).all()
        
        for transcription in updated_transcriptions:
            assert transcription.is_validated is True
            if transcription.id == transcriptions[0].id:
                assert transcription.is_consensus is True
            else:
                assert transcription.is_consensus is False
    
    def test_get_chunks_requiring_review(self, db_session: Session, sample_chunk):
        """Test getting chunks that require manual review."""
        consensus_service = ConsensusService(db_session)
        
        # Create transcriptions with metadata indicating review needed
        transcription = Transcription(
            chunk_id=sample_chunk.id,
            user_id=1,
            language_id=1,
            text="Test transcription",
            is_validated=False,
            meta_data={
                "consensus_evaluation": {
                    "requires_review": True,
                    "flagged_reasons": ["Low consensus confidence"]
                }
            }
        )
        db_session.add(transcription)
        db_session.commit()
        
        chunks = consensus_service.get_chunks_requiring_review(limit=10)
        
        assert len(chunks) == 1
        assert chunks[0]["chunk_id"] == sample_chunk.id
        assert chunks[0]["transcription_count"] == 1
        assert "Low consensus confidence" in chunks[0]["flagged_reasons"]
    
    def test_get_validation_statistics(self, db_session: Session, sample_chunk):
        """Test getting validation statistics."""
        consensus_service = ConsensusService(db_session)
        
        # Create some transcriptions with different validation states
        transcriptions = [
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=1,
                language_id=1,
                text="Validated transcription",
                is_validated=True,
                is_consensus=True,
                quality=0.9,
                confidence=0.8
            ),
            Transcription(
                chunk_id=sample_chunk.id,
                user_id=2,
                language_id=1,
                text="Unvalidated transcription",
                is_validated=False,
                quality=0.5,
                confidence=0.4
            )
        ]
        
        for t in transcriptions:
            db_session.add(t)
        db_session.commit()
        
        stats = consensus_service.get_validation_statistics()
        
        assert stats["total_chunks_with_transcriptions"] >= 1
        assert stats["validated_chunks"] >= 1
        assert stats["consensus_transcriptions"] >= 1
        assert 0 <= stats["validation_rate"] <= 100
        assert 0 <= stats["average_confidence_score"] <= 1
        assert 0 <= stats["average_quality_score"] <= 1
        assert isinstance(stats["quality_review_counts"], dict)
    
    def test_calculate_pairwise_similarities(self, db_session: Session):
        """Test pairwise similarity calculation."""
        consensus_service = ConsensusService(db_session)
        
        transcriptions = [
            Transcription(text="This is a test sentence."),
            Transcription(text="This is a test sentence."),  # Identical
            Transcription(text="This is a different sentence.")  # Different
        ]
        
        similarities = consensus_service._calculate_pairwise_similarities(transcriptions)
        
        assert len(similarities) == 3  # 3 pairs from 3 transcriptions
        assert similarities[0] == 1.0  # Identical texts
        assert 0 < similarities[1] < 1.0  # Similar but not identical
        assert 0 < similarities[2] < 1.0  # Similar but not identical
    
    def test_find_consensus_text(self, db_session: Session):
        """Test finding consensus text."""
        consensus_service = ConsensusService(db_session)
        
        transcriptions = [
            Transcription(text="This is the correct text."),
            Transcription(text="This is the correct text."),
            Transcription(text="This is different text.")
        ]
        
        similarities = consensus_service._calculate_pairwise_similarities(transcriptions)
        consensus_text, confidence = consensus_service._find_consensus_text(transcriptions, similarities)
        
        assert consensus_text == "This is the correct text."
        assert confidence > 0.5  # Should have reasonable confidence
    
    def test_requires_manual_review_conditions(self, db_session: Session):
        """Test different conditions that require manual review."""
        consensus_service = ConsensusService(db_session)
        
        # Test very short transcription
        short_transcriptions = [
            Transcription(text="Hi"),
            Transcription(text="Hello")
        ]
        
        flagged_reasons = []
        requires_review = consensus_service._requires_manual_review(
            short_transcriptions, [0.3], 0.6, flagged_reasons
        )
        
        assert requires_review is True
        assert any("short" in reason.lower() for reason in flagged_reasons)
        
        # Test very long transcription
        long_text = "This is a very long transcription that exceeds the normal length limits " * 10
        long_transcriptions = [
            Transcription(text=long_text),
            Transcription(text="Short text")
        ]
        
        flagged_reasons = []
        requires_review = consensus_service._requires_manual_review(
            long_transcriptions, [0.1], 0.6, flagged_reasons
        )
        
        assert requires_review is True
        assert any("long" in reason.lower() for reason in flagged_reasons)


@pytest.fixture
def sample_chunk(db_session: Session):
    """Create a sample audio chunk for testing."""
    # Create required dependencies
    user = User(name="Test User", email="test@example.com", role=UserRole.CONTRIBUTOR)
    db_session.add(user)
    
    language = Language(name="English", code="en")
    db_session.add(language)
    
    recording = VoiceRecording(
        user_id=1,
        language_id=1,
        file_path="/test/path.wav",
        duration=10.0,
        status=RecordingStatus.CHUNKED
    )
    db_session.add(recording)
    db_session.commit()
    
    chunk = AudioChunk(
        recording_id=recording.id,
        chunk_index=0,
        file_path="/test/chunk.wav",
        start_time=0.0,
        end_time=5.0,
        duration=5.0
    )
    db_session.add(chunk)
    db_session.commit()
    
    return chunk


@pytest.fixture
def sample_user(db_session: Session):
    """Create a sample user for testing."""
    user = User(
        name="Reviewer User",
        email="reviewer@example.com",
        role=UserRole.ADMIN
    )
    db_session.add(user)
    db_session.commit()
    return user