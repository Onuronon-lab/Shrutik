import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_transcription_endpoints_exist():
    """Test that transcription endpoints are properly registered."""

    # Test that the app includes transcription routes
    routes = [route.path for route in app.routes]

    # Check for key transcription endpoints
    expected_paths = [
        "/api/transcriptions/tasks",
        "/api/transcriptions/submit",
        "/api/transcriptions/skip",
        "/api/transcriptions/",
    ]

    for path in expected_paths:
        # Check if any route matches the expected path pattern
        matching_routes = [route for route in routes if path in str(route)]
        assert (
            len(matching_routes) > 0
        ), f"Expected transcription endpoint {path} not found"


def test_transcription_task_request_validation():
    """Test transcription task request validation."""
    from app.schemas.transcription import TranscriptionTaskRequest

    # Test valid request
    valid_request = TranscriptionTaskRequest(quantity=5)
    assert valid_request.quantity == 5

    # Test invalid quantity
    with pytest.raises(ValueError):
        TranscriptionTaskRequest(quantity=3)  # Not in allowed quantities

    # Test valid quantities
    for quantity in [2, 5, 10, 15, 20]:
        request = TranscriptionTaskRequest(quantity=quantity)
        assert request.quantity == quantity


def test_transcription_schemas():
    """Test transcription schema validation."""
    from app.schemas.transcription import (
        AudioChunkForTranscription,
        TranscriptionCreate,
    )

    # Test TranscriptionCreate
    transcription = TranscriptionCreate(
        chunk_id=1, text="This is a test transcription", language_id=1
    )
    assert transcription.chunk_id == 1
    assert transcription.text == "This is a test transcription"
    assert transcription.language_id == 1

    # Test empty text validation
    with pytest.raises(ValueError):
        TranscriptionCreate(chunk_id=1, text="", language_id=1)

    # Test AudioChunkForTranscription
    chunk = AudioChunkForTranscription(
        id=1,
        recording_id=1,
        chunk_index=0,
        file_path="/path/to/chunk.wav",
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
    )
    assert chunk.id == 1
    assert chunk.duration == 5.0


def test_app_health():
    """Test that the app is healthy and can handle requests."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


if __name__ == "__main__":
    pytest.main([__file__])
