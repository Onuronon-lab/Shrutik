import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import Base
from app.main import app
from app.models.audio_chunk import AudioChunk
from app.models.language import Language
from app.models.script import DurationCategory, Script
from app.models.transcription import Transcription
from app.models.user import User, UserRole
from app.models.voice_recording import RecordingStatus, VoiceRecording
from app.services.transcription_service import TranscriptionService

client = TestClient(app)

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_transcriptions.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    # Health endpoint returns detailed status, just verify it has a status field
    response_data = response.json()
    assert "status" in response_data
    assert response_data["status"] in ["healthy", "degraded", "critical"]


@pytest.fixture(scope="session")
def db_engine():
    """Create database engine once per test session."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(db_engine):
    """Create a test database session and rollback after each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def sample_user(db_session: Session):
    """Create a sample user for testing."""
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash="dummy_hash",
        role=UserRole.CONTRIBUTOR,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def sample_language(db_session: Session):
    """Create a sample language for testing."""
    language = Language(name="English", code="en")
    db_session.add(language)
    db_session.commit()
    return language


@pytest.fixture
def sample_chunks(db_session: Session, sample_user, sample_language):
    """Create sample audio chunks with varying transcript counts."""
    # Create script
    script = Script(
        language_id=sample_language.id,
        text="Test script",
        duration_category=DurationCategory.SHORT,
    )
    db_session.add(script)
    db_session.commit()

    # Create recording
    recording = VoiceRecording(
        user_id=sample_user.id,
        script_id=script.id,
        language_id=sample_language.id,
        file_path="/test/path.wav",
        duration=30.0,
        status=RecordingStatus.CHUNKED,
    )
    db_session.add(recording)
    db_session.commit()

    # Create chunks with different transcript counts
    chunks = []
    for i in range(5):
        chunk = AudioChunk(
            recording_id=recording.id,
            chunk_index=i,
            file_path=f"/test/chunk_{i}.wav",
            start_time=i * 5.0,
            end_time=(i + 1) * 5.0,
            duration=5.0,
            transcript_count=i,  # 0, 1, 2, 3, 4
            ready_for_export=False,
        )
        db_session.add(chunk)
        chunks.append(chunk)

    db_session.commit()
    return chunks


class TestTranscriptionServiceBulkOperations:
    """Test cases for TranscriptionService bulk operations."""

    def test_get_prioritized_chunks_orders_by_transcript_count(
        self, db_session: Session, sample_user, sample_chunks
    ):
        """Test that get_prioritized_chunks returns chunks ordered by transcript_count ascending."""
        service = TranscriptionService(db_session)

        # Get prioritized chunks
        chunks = service.get_prioritized_chunks(user_id=sample_user.id, quantity=5)

        # Verify we got chunks
        assert len(chunks) == 5

        # Verify they are ordered by transcript_count ascending
        transcript_counts = [chunk.transcript_count for chunk in chunks]
        assert transcript_counts == [0, 1, 2, 3, 4]

    def test_get_prioritized_chunks_excludes_ready_for_export(
        self, db_session: Session, sample_user, sample_chunks
    ):
        """Test that get_prioritized_chunks excludes chunks with ready_for_export=True."""
        service = TranscriptionService(db_session)

        # Mark one chunk as ready for export
        sample_chunks[0].ready_for_export = True
        db_session.commit()

        # Get prioritized chunks
        chunks = service.get_prioritized_chunks(user_id=sample_user.id, quantity=5)

        # Verify the ready chunk is excluded
        chunk_ids = [chunk.id for chunk in chunks]
        assert sample_chunks[0].id not in chunk_ids
        assert len(chunks) == 4

    def test_get_prioritized_chunks_excludes_user_transcribed(
        self, db_session: Session, sample_user, sample_chunks, sample_language
    ):
        """Test that get_prioritized_chunks excludes chunks already transcribed by user."""
        service = TranscriptionService(db_session)

        # Create a transcription by the user for the first chunk
        transcription = Transcription(
            chunk_id=sample_chunks[0].id,
            user_id=sample_user.id,
            language_id=sample_language.id,
            text="Already transcribed by this user",
        )
        db_session.add(transcription)
        db_session.commit()

        # Get prioritized chunks
        chunks = service.get_prioritized_chunks(user_id=sample_user.id, quantity=5)

        # Verify the transcribed chunk is excluded
        chunk_ids = [chunk.id for chunk in chunks]
        assert sample_chunks[0].id not in chunk_ids
        assert len(chunks) == 4

    def test_get_prioritized_chunks_filters_by_language(
        self, db_session: Session, sample_user, sample_chunks, sample_language
    ):
        """Test that get_prioritized_chunks filters by language_id."""
        service = TranscriptionService(db_session)

        # Create another language
        other_language = Language(name="Spanish", code="es")
        db_session.add(other_language)
        db_session.commit()

        # Get chunks filtered by language
        chunks = service.get_prioritized_chunks(
            user_id=sample_user.id, quantity=5, language_id=sample_language.id
        )

        # Verify all chunks are from the correct language
        assert len(chunks) == 5
        for chunk in chunks:
            assert chunk.recording.language_id == sample_language.id

    def test_submit_transcriptions_bulk_insert(
        self, db_session: Session, sample_user, sample_chunks, sample_language
    ):
        """Test bulk insert of transcriptions."""
        from app.schemas.transcription import (
            TranscriptionCreate,
            TranscriptionSubmission,
        )

        service = TranscriptionService(db_session)

        # Create a session
        session_id = "test-session-123"
        chunk_ids = [sample_chunks[0].id, sample_chunks[1].id]
        from app.services.transcription_service import TranscriptionSession

        session = TranscriptionSession(session_id, sample_user.id, chunk_ids)
        service._active_sessions[session_id] = session

        # Create submission with multiple transcriptions
        transcriptions = [
            TranscriptionCreate(
                chunk_id=sample_chunks[0].id,
                language_id=sample_language.id,
                text="First transcription",
            ),
            TranscriptionCreate(
                chunk_id=sample_chunks[1].id,
                language_id=sample_language.id,
                text="Second transcription",
            ),
        ]

        submission = TranscriptionSubmission(
            session_id=session_id, transcriptions=transcriptions
        )

        # Submit transcriptions
        response = service.submit_transcriptions(sample_user.id, submission)

        # Verify response
        assert response.submitted_count == 2
        assert len(response.transcriptions) == 2

        # Verify transcriptions were created
        db_transcriptions = (
            db_session.query(Transcription)
            .filter(Transcription.user_id == sample_user.id)
            .all()
        )
        assert len(db_transcriptions) == 2

    def test_submit_transcriptions_updates_transcript_count(
        self, db_session: Session, sample_user, sample_chunks, sample_language
    ):
        """Test that submit_transcriptions updates transcript_count atomically."""
        from app.schemas.transcription import (
            TranscriptionCreate,
            TranscriptionSubmission,
        )

        service = TranscriptionService(db_session)

        # Get initial transcript_count
        initial_count = sample_chunks[0].transcript_count

        # Create a session
        session_id = "test-session-456"
        chunk_ids = [sample_chunks[0].id]
        from app.services.transcription_service import TranscriptionSession

        session = TranscriptionSession(session_id, sample_user.id, chunk_ids)
        service._active_sessions[session_id] = session

        # Create submission
        transcriptions = [
            TranscriptionCreate(
                chunk_id=sample_chunks[0].id,
                language_id=sample_language.id,
                text="Test transcription",
            )
        ]

        submission = TranscriptionSubmission(
            session_id=session_id, transcriptions=transcriptions
        )

        # Submit transcription
        service.submit_transcriptions(sample_user.id, submission)

        # Refresh chunk and verify transcript_count was incremented
        db_session.refresh(sample_chunks[0])
        assert sample_chunks[0].transcript_count == initial_count + 1

    def test_submit_transcriptions_triggers_consensus(
        self,
        db_session: Session,
        sample_user,
        sample_chunks,
        sample_language,
        monkeypatch,
    ):
        """Test that submit_transcriptions triggers consensus calculation."""
        from app.schemas.transcription import (
            TranscriptionCreate,
            TranscriptionSubmission,
        )

        service = TranscriptionService(db_session)

        # Track if consensus was triggered
        consensus_triggered = []

        def mock_trigger_consensus(chunk_ids):
            consensus_triggered.extend(chunk_ids)

        # Patch the trigger method
        monkeypatch.setattr(
            service, "_trigger_consensus_calculation", mock_trigger_consensus
        )

        # Create a session
        session_id = "test-session-789"
        chunk_ids = [sample_chunks[0].id]
        from app.services.transcription_service import TranscriptionSession

        session = TranscriptionSession(session_id, sample_user.id, chunk_ids)
        service._active_sessions[session_id] = session

        # Create submission
        transcriptions = [
            TranscriptionCreate(
                chunk_id=sample_chunks[0].id,
                language_id=sample_language.id,
                text="Test transcription",
            )
        ]

        submission = TranscriptionSubmission(
            session_id=session_id, transcriptions=transcriptions
        )

        # Submit transcription
        service.submit_transcriptions(sample_user.id, submission)

        # Verify consensus was triggered for the chunk
        assert sample_chunks[0].id in consensus_triggered


if __name__ == "__main__":
    pytest.main([__file__])
