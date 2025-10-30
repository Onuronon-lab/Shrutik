"""
Integration tests for consensus and quality validation system.

These tests verify that the consensus system works end-to-end
with the database and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_consensus_api_endpoints_exist():
    """Test that consensus API endpoints are properly registered."""
    # Test that the consensus endpoints are accessible
    response = client.get("/docs")
    assert response.status_code == 200
    
    # The OpenAPI docs should include our consensus endpoints
    openapi_json = client.get("/openapi.json")
    assert openapi_json.status_code == 200
    
    openapi_data = openapi_json.json()
    paths = openapi_data.get("paths", {})
    
    # Check that consensus endpoints are registered
    consensus_endpoints = [
        "/api/consensus/evaluate/{chunk_id}",
        "/api/consensus/validate/{chunk_id}",
        "/api/consensus/batch-calculate",
        "/api/consensus/review-queue",
        "/api/consensus/statistics"
    ]
    
    for endpoint in consensus_endpoints:
        assert endpoint in paths, f"Endpoint {endpoint} not found in OpenAPI spec"


def test_consensus_service_basic_functionality():
    """Test basic consensus service functionality without database."""
    from app.services.consensus_service import ConsensusService
    from app.models.transcription import Transcription
    
    # Create a mock consensus service (without database)
    class MockDB:
        pass
    
    consensus_service = ConsensusService(MockDB())
    
    # Test pairwise similarity calculation
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
    
    # Test consensus text finding
    consensus_text, confidence = consensus_service._find_consensus_text(transcriptions, similarities)
    
    assert consensus_text == "This is a test sentence."
    assert confidence > 0.5  # Should have reasonable confidence


def test_consensus_configuration_constants():
    """Test that consensus configuration constants are reasonable."""
    from app.services.consensus_service import ConsensusService
    
    # Test that configuration constants are within expected ranges
    assert 1 <= ConsensusService.MIN_TRANSCRIPTIONS_FOR_CONSENSUS <= 5
    assert 0.0 <= ConsensusService.CONSENSUS_SIMILARITY_THRESHOLD <= 1.0
    assert 0.0 <= ConsensusService.HIGH_CONFIDENCE_THRESHOLD <= 1.0
    assert 0.0 <= ConsensusService.LOW_CONFIDENCE_THRESHOLD <= 1.0
    assert 0.0 <= ConsensusService.MAX_TRANSCRIPTION_LENGTH_DIFF <= 1.0
    
    # Test logical relationships
    assert ConsensusService.LOW_CONFIDENCE_THRESHOLD < ConsensusService.HIGH_CONFIDENCE_THRESHOLD


def test_quality_scoring_algorithm():
    """Test the quality scoring algorithm logic."""
    from app.services.consensus_service import ConsensusService
    from app.models.transcription import Transcription
    
    class MockDB:
        pass
    
    consensus_service = ConsensusService(MockDB())
    
    # Test with high similarity transcriptions
    high_similarity_transcriptions = [
        Transcription(text="This is a test."),
        Transcription(text="This is a test."),
        Transcription(text="This is a test.")
    ]
    
    high_similarities = [1.0, 1.0, 1.0]  # Perfect similarity
    quality_score = consensus_service._calculate_quality_score(
        high_similarity_transcriptions, high_similarities
    )
    
    assert 0.8 <= quality_score <= 1.0  # Should be high quality
    
    # Test with low similarity transcriptions
    low_similarity_transcriptions = [
        Transcription(text="This is a test."),
        Transcription(text="Completely different text."),
        Transcription(text="Another unrelated sentence.")
    ]
    
    low_similarities = [0.1, 0.1, 0.1]  # Low similarity
    quality_score = consensus_service._calculate_quality_score(
        low_similarity_transcriptions, low_similarities
    )
    
    assert 0.0 <= quality_score <= 0.5  # Should be low quality


def test_flagging_conditions():
    """Test automatic flagging conditions for manual review."""
    from app.services.consensus_service import ConsensusService
    from app.models.transcription import Transcription
    
    class MockDB:
        pass
    
    consensus_service = ConsensusService(MockDB())
    
    # Test short transcription flagging
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
    
    # Test low confidence flagging
    normal_transcriptions = [
        Transcription(text="This is a normal length transcription."),
        Transcription(text="This is another normal transcription.")
    ]
    
    flagged_reasons = []
    requires_review = consensus_service._requires_manual_review(
        normal_transcriptions, [0.8], 0.3, flagged_reasons  # Low confidence
    )
    
    assert requires_review is True
    assert any("confidence" in reason.lower() for reason in flagged_reasons)


def test_celery_task_imports():
    """Test that Celery tasks can be imported successfully."""
    try:
        from app.tasks.audio_processing import calculate_consensus_for_chunks, recalculate_all_consensus
        assert callable(calculate_consensus_for_chunks)
        assert callable(recalculate_all_consensus)
    except ImportError as e:
        pytest.fail(f"Failed to import Celery consensus tasks: {e}")


def test_consensus_schemas():
    """Test that consensus schemas are properly defined."""
    from app.schemas.consensus import (
        ConsensusResult, ValidationStatus, ManualReviewRequest,
        ValidationStatistics, ChunkValidationStatus
    )
    
    # Test that schemas can be instantiated with valid data
    consensus_result = ConsensusResult(
        chunk_id=1,
        consensus_text="Test text",
        confidence_score=0.8,
        requires_review=False,
        participant_count=3,
        quality_score=0.9,
        transcription_similarities=[0.8, 0.9, 0.85],
        flagged_reasons=[]
    )
    
    assert consensus_result.chunk_id == 1
    assert consensus_result.confidence_score == 0.8
    
    # Test validation status
    from datetime import datetime, timezone
    validation_status = ValidationStatus(
        chunk_id=1,
        is_validated=True,
        validation_confidence=0.8,
        requires_manual_review=False,
        last_updated=datetime.now(timezone.utc)
    )
    
    assert validation_status.is_validated is True
    
    # Test manual review request
    from app.models.quality_review import ReviewDecision
    review_request = ManualReviewRequest(
        decision=ReviewDecision.APPROVED,
        selected_transcription_id=1,
        comment="Looks good"
    )
    
    assert review_request.decision == ReviewDecision.APPROVED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])