"""
Tests for export functionality.

This module tests the secure data export system including dataset export,
metadata export, audit logging, and access control for Sworik developers.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.security import get_password_hash
from app.db.database import Base, get_db
from app.main import app
from app.models.audio_chunk import AudioChunk
from app.models.export_audit import ExportAuditLog
from app.models.language import Language
from app.models.script import DurationCategory, Script
from app.models.transcription import Transcription
from app.models.user import User, UserRole
from app.models.voice_recording import RecordingStatus, VoiceRecording

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_export.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sworik_developer_user(db_session):
    """Create a Sworik developer user for testing."""
    user = User(
        name="Sworik Developer",
        email="developer@sworik.com",
        password_hash=get_password_hash("testpassword123"),
        role=UserRole.SWORIK_DEVELOPER,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def contributor_user(db_session):
    """Create a contributor user for testing."""
    user = User(
        name="Test Contributor",
        email="contributor@example.com",
        password_hash=get_password_hash("testpassword123"),
        role=UserRole.CONTRIBUTOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_data(db_session, contributor_user):
    """Create test data for export testing."""
    # Create language
    language = Language(name="Bangla", code="bn")
    db_session.add(language)
    db_session.commit()
    db_session.refresh(language)

    # Create script
    script = Script(
        text="এটি একটি পরীক্ষার স্ক্রিপ্ট।",
        duration_category=DurationCategory.SHORT,
        language_id=language.id,
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)

    # Create voice recording
    recording = VoiceRecording(
        user_id=contributor_user.id,
        script_id=script.id,
        language_id=language.id,
        file_path="/test/recording.wav",
        duration=10.5,
        status=RecordingStatus.CHUNKED,
    )
    db_session.add(recording)
    db_session.commit()
    db_session.refresh(recording)

    # Create audio chunk
    chunk = AudioChunk(
        recording_id=recording.id,
        chunk_index=0,
        file_path="/test/chunk_0.wav",
        start_time=0.0,
        end_time=5.0,
        duration=5.0,
        sentence_hint="এটি একটি পরীক্ষার স্ক্রিপ্ট।",
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)

    # Create transcription
    transcription = Transcription(
        chunk_id=chunk.id,
        user_id=contributor_user.id,
        language_id=language.id,
        text="এটি একটি পরীক্ষার স্ক্রিপ্ট।",
        quality=0.95,
        confidence=0.90,
        is_consensus=True,
        is_validated=True,
    )
    db_session.add(transcription)
    db_session.commit()
    db_session.refresh(transcription)

    return {
        "language": language,
        "script": script,
        "recording": recording,
        "chunk": chunk,
        "transcription": transcription,
    }


def get_auth_headers(
    client: TestClient, user_email: str, password: str = "testpassword123"
):
    """Get authentication headers for a user."""
    login_response = client.post(
        "/api/auth/login", json={"email": user_email, "password": password}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_export_dataset_success(client: TestClient, sworik_developer_user, test_data):
    """Test successful dataset export by Sworik developer."""
    headers = get_auth_headers(client, sworik_developer_user.email)

    export_request = {
        "format": "json",
        "quality_filters": {"min_confidence": 0.8, "consensus_only": True},
        "include_metadata": True,
    }

    response = client.post("/api/export/dataset", json=export_request, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "export_id" in data
    assert "data" in data
    assert "statistics" in data
    assert data["format"] == "json"
    assert data["total_records"] == 1

    # Check exported data structure
    exported_item = data["data"][0]
    assert "chunk_id" in exported_item
    assert "transcription_text" in exported_item
    assert "quality_score" in exported_item
    assert exported_item["is_consensus"] == True


def test_export_dataset_access_denied_contributor(
    client: TestClient, contributor_user, test_data
):
    """Test that contributors cannot access export endpoints."""
    headers = get_auth_headers(client, contributor_user.email)

    export_request = {"format": "json"}

    response = client.post("/api/export/dataset", json=export_request, headers=headers)
    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()["detail"]


def test_export_metadata_success(client: TestClient, sworik_developer_user, test_data):
    """Test successful metadata export by Sworik developer."""
    headers = get_auth_headers(client, sworik_developer_user.email)

    export_request = {
        "format": "json",
        "include_statistics": True,
        "include_quality_metrics": True,
    }

    response = client.post("/api/export/metadata", json=export_request, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "export_id" in data
    assert "statistics" in data
    assert "platform_metrics" in data
    assert "quality_metrics" in data
    assert data["format"] == "json"


def test_export_history(client: TestClient, sworik_developer_user, test_data):
    """Test export history retrieval."""
    headers = get_auth_headers(client, sworik_developer_user.email)

    # First, perform an export to create history
    export_request = {"format": "json"}
    client.post("/api/export/dataset", json=export_request, headers=headers)

    # Then get export history
    response = client.get("/api/export/history", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "logs" in data
    assert "total_count" in data
    assert data["total_count"] >= 1

    # Check audit log structure
    if data["logs"]:
        log = data["logs"][0]
        assert "export_id" in log
        assert "user_email" in log
        assert "export_type" in log
        assert "records_exported" in log


def test_export_formats_endpoint(client: TestClient, sworik_developer_user):
    """Test supported formats endpoint."""
    headers = get_auth_headers(client, sworik_developer_user.email)

    response = client.get("/api/export/formats", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "dataset_formats" in data
    assert "metadata_formats" in data
    assert "json" in data["dataset_formats"]
    assert "csv" in data["dataset_formats"]


def test_export_stats_endpoint(client: TestClient, sworik_developer_user, test_data):
    """Test export statistics endpoint."""
    headers = get_auth_headers(client, sworik_developer_user.email)

    response = client.get("/api/export/stats", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert "statistics" in data
    assert "platform_metrics" in data
    assert "quality_metrics" in data
    assert "last_updated" in data


def test_export_with_filters(client: TestClient, sworik_developer_user, test_data):
    """Test dataset export with various filters."""
    headers = get_auth_headers(client, sworik_developer_user.email)

    export_request = {
        "format": "json",
        "quality_filters": {"min_quality": 0.9, "validated_only": True},
        "language_ids": [test_data["language"].id],
        "max_records": 10,
    }

    response = client.post("/api/export/dataset", json=export_request, headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total_records"] == 1  # Should match our test data

    # Verify filters were applied in statistics
    stats = data["statistics"]
    assert "filters_applied" in stats
    assert stats["filters_applied"]["quality_filters"]["validated_only"] == True


def test_export_audit_logging(
    client: TestClient, db_session, sworik_developer_user, test_data
):
    """Test that export operations are properly logged."""
    headers = get_auth_headers(client, sworik_developer_user.email)

    # Count existing audit logs
    initial_count = db_session.query(ExportAuditLog).count()

    # Perform export
    export_request = {"format": "json"}
    response = client.post("/api/export/dataset", json=export_request, headers=headers)
    assert response.status_code == 200

    # Check that audit log was created
    final_count = db_session.query(ExportAuditLog).count()
    assert final_count == initial_count + 1

    # Check audit log details
    audit_log = (
        db_session.query(ExportAuditLog).order_by(ExportAuditLog.id.desc()).first()
    )
    assert audit_log.user_id == sworik_developer_user.id
    assert audit_log.export_type == "dataset"
    assert audit_log.format == "json"
    assert audit_log.records_exported == 1


def test_export_unauthorized_no_token(client: TestClient):
    """Test that export endpoints require authentication."""
    export_request = {"format": "json"}

    response = client.post("/api/export/dataset", json=export_request)
    assert response.status_code == 403  # FastAPI returns 403 for missing auth header


def test_export_history_pagination(
    client: TestClient, sworik_developer_user, test_data
):
    """Test export history pagination."""
    headers = get_auth_headers(client, sworik_developer_user.email)

    # Create multiple export records
    for i in range(3):
        export_request = {"format": "json"}
        client.post("/api/export/dataset", json=export_request, headers=headers)

    # Test pagination
    response = client.get("/api/export/history?page=1&page_size=2", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data["logs"]) <= 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total_count"] >= 3


# Export Batch Service Tests (Export Optimization)

import os
import tempfile
from unittest.mock import patch

from app.core.config import StorageConfig
from app.core.exceptions import ValidationError
from app.models.export_batch import ExportBatch, ExportBatchStatus, StorageType
from app.models.export_download import ExportDownload
from app.services.export_batch_service import ExportBatchService


@pytest.fixture
def export_batch_service(db_session):
    """Create ExportBatchService with test database session."""
    storage_config = StorageConfig(
        storage_type="local", local_export_dir=tempfile.mkdtemp()
    )
    return ExportBatchService(db_session, storage_config)


@pytest.fixture
def ready_chunks(db_session, contributor_user):
    """Create chunks ready for export."""
    language = Language(name="Bengali", code="bn")
    db_session.add(language)
    db_session.commit()

    script = Script(
        text="Test script",
        duration_category=DurationCategory.SHORT,
        language_id=language.id,
    )
    db_session.add(script)
    db_session.commit()

    recording = VoiceRecording(
        user_id=contributor_user.id,
        script_id=script.id,
        language_id=language.id,
        file_path="/test/recording.wav",
        duration=10.0,
        status=RecordingStatus.CHUNKED,
    )
    db_session.add(recording)
    db_session.commit()

    chunks = []
    for i in range(5):
        chunk = AudioChunk(
            recording_id=recording.id,
            chunk_index=i,
            file_path=f"/test/chunk_{i}.webm",
            start_time=i * 2.0,
            end_time=(i + 1) * 2.0,
            duration=2.0,
            ready_for_export=True,
            transcript_count=5,
            consensus_quality=0.95,
        )
        db_session.add(chunk)
        db_session.commit()

        # Add consensus transcription
        transcription = Transcription(
            chunk_id=chunk.id,
            user_id=contributor_user.id,
            language_id=language.id,
            text=f"Test transcription {i}",
            quality=0.95,
            confidence=0.90,
            is_consensus=True,
            is_validated=True,
        )
        db_session.add(transcription)
        db_session.commit()

        chunk.consensus_transcript_id = transcription.id
        db_session.commit()

        chunks.append(chunk)

    db_session.refresh(recording)
    for chunk in chunks:
        db_session.refresh(chunk)

    return chunks


def test_check_r2_free_tier_limits_disabled(export_batch_service):
    """Test R2 free tier check when guard is disabled."""
    with patch("app.core.config.settings.R2_ENABLE_FREE_TIER_GUARD", False):
        result = export_batch_service.check_r2_free_tier_limits()
        assert result is True


def test_check_r2_free_tier_limits_local_storage(export_batch_service):
    """Test R2 free tier check with local storage (should skip)."""
    result = export_batch_service.check_r2_free_tier_limits()
    assert result is True


def test_check_r2_free_tier_limits_within_limits(db_session):
    """Test R2 free tier check when within limits."""
    storage_config = StorageConfig(
        storage_type="r2",
        r2_account_id="test",
        r2_access_key_id="test",
        r2_secret_access_key="test",
        r2_bucket_name="test",
        r2_endpoint_url="https://test.r2.cloudflarestorage.com",
    )
    service = ExportBatchService(db_session, storage_config)

    with patch("app.core.config.settings.R2_ENABLE_FREE_TIER_GUARD", True):
        result = service.check_r2_free_tier_limits()
        assert result is True


def test_create_export_batch_insufficient_chunks(export_batch_service, ready_chunks):
    """Test that scheduled export fails with insufficient chunks."""
    with pytest.raises(ValidationError) as exc_info:
        export_batch_service.create_export_batch(max_chunks=200, force_create=False)

    assert "Insufficient chunks" in str(exc_info.value)


def test_create_export_batch_force_create(
    export_batch_service, ready_chunks, db_session
):
    """Test that force_create allows batch with fewer chunks."""
    # Mock file operations
    with (
        patch("os.path.exists", return_value=True),
        patch("os.path.getsize", return_value=1024),
        patch.object(
            export_batch_service,
            "generate_export_archive",
            return_value=("/tmp/test.tar.zst", 1024),
        ),
        patch.object(
            export_batch_service,
            "upload_to_storage",
            return_value="/exports/test.tar.zst",
        ),
        patch.object(
            export_batch_service, "_calculate_file_checksum", return_value="abc123"
        ),
    ):

        batch = export_batch_service.create_export_batch(
            max_chunks=200, force_create=True
        )

        assert batch is not None
        assert batch.status == ExportBatchStatus.COMPLETED
        assert batch.chunk_count == 5
        assert len(batch.chunk_ids) == 5


def test_create_export_batch_filters_oversized_chunks(
    export_batch_service, ready_chunks, db_session
):
    """Test that oversized chunks are filtered out."""
    # Mock one chunk as oversized
    with (
        patch("os.path.exists", return_value=True),
        patch(
            "os.path.getsize", side_effect=[1024, 1024, 100 * 1024 * 1024, 1024, 1024]
        ),
        patch.object(
            export_batch_service,
            "generate_export_archive",
            return_value=("/tmp/test.tar.zst", 1024),
        ),
        patch.object(
            export_batch_service,
            "upload_to_storage",
            return_value="/exports/test.tar.zst",
        ),
        patch.object(
            export_batch_service, "_calculate_file_checksum", return_value="abc123"
        ),
    ):

        batch = export_batch_service.create_export_batch(
            max_chunks=200, force_create=True
        )

        # Should have 4 chunks (1 filtered out)
        assert batch.chunk_count == 4


def test_create_export_batch_excludes_already_exported(
    export_batch_service, ready_chunks, db_session
):
    """Test that chunks in completed batches are excluded."""
    # Create a completed batch with first 3 chunks
    existing_batch = ExportBatch(
        batch_id="existing-batch",
        archive_path="/exports/existing.tar.zst",
        storage_type=StorageType.LOCAL,
        chunk_count=3,
        chunk_ids=[ready_chunks[0].id, ready_chunks[1].id, ready_chunks[2].id],
        status=ExportBatchStatus.COMPLETED,
        exported=True,
    )
    db_session.add(existing_batch)
    db_session.commit()

    # Create new batch - should only get remaining 2 chunks
    with (
        patch("os.path.exists", return_value=True),
        patch("os.path.getsize", return_value=1024),
        patch.object(
            export_batch_service,
            "generate_export_archive",
            return_value=("/tmp/test.tar.zst", 1024),
        ),
        patch.object(
            export_batch_service,
            "upload_to_storage",
            return_value="/exports/test.tar.zst",
        ),
        patch.object(
            export_batch_service, "_calculate_file_checksum", return_value="abc123"
        ),
    ):

        batch = export_batch_service.create_export_batch(
            max_chunks=200, force_create=True
        )

        assert batch.chunk_count == 2
        assert ready_chunks[0].id not in batch.chunk_ids
        assert ready_chunks[1].id not in batch.chunk_ids
        assert ready_chunks[2].id not in batch.chunk_ids


def test_create_export_batch_date_filter(
    export_batch_service, ready_chunks, db_session
):
    """Test export batch creation with date range filter."""
    from datetime import datetime, timedelta, timezone

    # Set different created_at times for chunks
    now = datetime.now(timezone.utc)
    ready_chunks[0].created_at = now - timedelta(days=10)
    ready_chunks[1].created_at = now - timedelta(days=5)
    ready_chunks[2].created_at = now - timedelta(days=3)
    ready_chunks[3].created_at = now - timedelta(days=1)
    ready_chunks[4].created_at = now
    db_session.commit()

    # Filter for last 4 days
    date_from = now - timedelta(days=4)

    with (
        patch("os.path.exists", return_value=True),
        patch("os.path.getsize", return_value=1024),
        patch.object(
            export_batch_service,
            "generate_export_archive",
            return_value=("/tmp/test.tar.zst", 1024),
        ),
        patch.object(
            export_batch_service,
            "upload_to_storage",
            return_value="/exports/test.tar.zst",
        ),
        patch.object(
            export_batch_service, "_calculate_file_checksum", return_value="abc123"
        ),
    ):

        batch = export_batch_service.create_export_batch(
            max_chunks=200, date_from=date_from, force_create=True
        )

        # Should have 3 chunks (last 3 days)
        assert batch.chunk_count == 3


def test_create_export_batch_duration_filter(
    export_batch_service, ready_chunks, db_session
):
    """Test export batch creation with duration filter."""
    # Set different durations
    ready_chunks[0].duration = 1.5
    ready_chunks[1].duration = 3.0
    ready_chunks[2].duration = 5.0
    ready_chunks[3].duration = 7.0
    ready_chunks[4].duration = 9.0
    db_session.commit()

    with (
        patch("os.path.exists", return_value=True),
        patch("os.path.getsize", return_value=1024),
        patch.object(
            export_batch_service,
            "generate_export_archive",
            return_value=("/tmp/test.tar.zst", 1024),
        ),
        patch.object(
            export_batch_service,
            "upload_to_storage",
            return_value="/exports/test.tar.zst",
        ),
        patch.object(
            export_batch_service, "_calculate_file_checksum", return_value="abc123"
        ),
    ):

        batch = export_batch_service.create_export_batch(
            max_chunks=200, min_duration=3.0, max_duration=7.0, force_create=True
        )

        # Should have 3 chunks (3.0, 5.0, 7.0)
        assert batch.chunk_count == 3


def test_cleanup_exported_chunks(export_batch_service, ready_chunks, db_session):
    """Test cleanup of exported chunks."""
    chunk_ids = [chunk.id for chunk in ready_chunks[:3]]

    # Mock file deletion
    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_remove:

        export_batch_service.cleanup_exported_chunks(chunk_ids)

        # Verify chunks deleted from database
        remaining_chunks = (
            db_session.query(AudioChunk).filter(AudioChunk.id.in_(chunk_ids)).count()
        )
        assert remaining_chunks == 0

        # Verify transcriptions deleted
        remaining_transcriptions = (
            db_session.query(Transcription)
            .filter(Transcription.chunk_id.in_(chunk_ids))
            .count()
        )
        assert remaining_transcriptions == 0

        # Verify file deletion called
        assert mock_remove.call_count == 3


def test_get_export_batch(export_batch_service, db_session):
    """Test retrieving export batch by ID."""
    batch = ExportBatch(
        batch_id="test-batch-123",
        archive_path="/exports/test.tar.zst",
        storage_type=StorageType.LOCAL,
        chunk_count=5,
        chunk_ids=[1, 2, 3, 4, 5],
        status=ExportBatchStatus.COMPLETED,
    )
    db_session.add(batch)
    db_session.commit()

    retrieved = export_batch_service.get_export_batch("test-batch-123")
    assert retrieved is not None
    assert retrieved.batch_id == "test-batch-123"
    assert retrieved.chunk_count == 5


def test_list_export_batches(export_batch_service, db_session):
    """Test listing export batches with pagination."""
    # Create multiple batches
    for i in range(5):
        batch = ExportBatch(
            batch_id=f"batch-{i}",
            archive_path=f"/exports/batch-{i}.tar.zst",
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=list(range(i * 10, (i + 1) * 10)),
            status=ExportBatchStatus.COMPLETED,
        )
        db_session.add(batch)
    db_session.commit()

    # Test pagination
    batches = export_batch_service.list_export_batches(skip=0, limit=3)
    assert len(batches) == 3

    batches = export_batch_service.list_export_batches(skip=3, limit=3)
    assert len(batches) == 2


def test_download_export_batch_success(
    export_batch_service, db_session, contributor_user
):
    """Test successful export batch download."""
    batch = ExportBatch(
        batch_id="download-test",
        archive_path="/exports/test.tar.zst",
        storage_type=StorageType.LOCAL,
        chunk_count=5,
        chunk_ids=[1, 2, 3, 4, 5],
        status=ExportBatchStatus.COMPLETED,
    )
    db_session.add(batch)
    db_session.commit()

    file_path, mime_type = export_batch_service.download_export_batch(
        batch_id="download-test",
        user_id=contributor_user.id,
        ip_address="127.0.0.1",
        user_agent="test-agent",
    )

    assert file_path == "/exports/test.tar.zst"
    assert mime_type == "application/x-tar"

    # Verify download recorded
    download = (
        db_session.query(ExportDownload)
        .filter(ExportDownload.batch_id == "download-test")
        .first()
    )
    assert download is not None
    assert download.user_id == contributor_user.id
    assert download.ip_address == "127.0.0.1"


def test_download_export_batch_limit_exceeded(
    export_batch_service, db_session, contributor_user
):
    """Test download limit enforcement."""
    batch = ExportBatch(
        batch_id="limit-test",
        archive_path="/exports/test.tar.zst",
        storage_type=StorageType.LOCAL,
        chunk_count=5,
        chunk_ids=[1, 2, 3, 4, 5],
        status=ExportBatchStatus.COMPLETED,
    )
    db_session.add(batch)
    db_session.commit()

    # Create 2 downloads today (at limit)
    from datetime import datetime, timezone

    for i in range(2):
        download = ExportDownload(
            batch_id="limit-test",
            user_id=contributor_user.id,
            downloaded_at=datetime.now(timezone.utc),
        )
        db_session.add(download)
    db_session.commit()

    # Third download should fail
    with pytest.raises(ValidationError) as exc_info:
        export_batch_service.download_export_batch(
            batch_id="limit-test", user_id=contributor_user.id
        )

    assert "Daily download limit exceeded" in str(exc_info.value)


def test_check_download_limit(export_batch_service, db_session, contributor_user):
    """Test download limit checking."""
    # No downloads yet
    can_download, reset_time = export_batch_service.check_download_limit(
        contributor_user.id
    )
    assert can_download is True
    assert reset_time is not None

    # Add 2 downloads (at limit)
    from datetime import datetime, timezone

    for i in range(2):
        download = ExportDownload(
            batch_id=f"batch-{i}",
            user_id=contributor_user.id,
            downloaded_at=datetime.now(timezone.utc),
        )
        db_session.add(download)
    db_session.commit()

    # Should be at limit
    can_download, reset_time = export_batch_service.check_download_limit(
        contributor_user.id
    )
    assert can_download is False


def test_get_user_download_count_today(
    export_batch_service, db_session, contributor_user
):
    """Test counting user downloads today."""
    from datetime import datetime, timedelta, timezone

    # Add 2 downloads today
    now = datetime.now(timezone.utc)
    for i in range(2):
        download = ExportDownload(
            batch_id=f"batch-{i}", user_id=contributor_user.id, downloaded_at=now
        )
        db_session.add(download)

    # Add 1 download yesterday (should not count)
    yesterday = now - timedelta(days=1)
    download = ExportDownload(
        batch_id="batch-old", user_id=contributor_user.id, downloaded_at=yesterday
    )
    db_session.add(download)
    db_session.commit()

    count = export_batch_service.get_user_download_count_today(contributor_user.id)
    assert count == 2


def test_upload_to_local_storage(export_batch_service):
    """Test uploading archive to local storage."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.zst") as tmp_file:
        tmp_file.write(b"test data")
        tmp_path = tmp_file.name

    try:
        storage_path = export_batch_service._upload_to_local_storage(
            tmp_path, "test-batch"
        )

        # Verify file moved to export directory
        assert os.path.exists(storage_path)
        assert storage_path.endswith(".tar.zst")

        # Verify permissions (600)
        stat_info = os.stat(storage_path)
        assert oct(stat_info.st_mode)[-3:] == "600"

        # Cleanup
        os.remove(storage_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_calculate_file_checksum(export_batch_service):
    """Test SHA256 checksum calculation."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(b"test data for checksum")
        tmp_path = tmp_file.name

    try:
        checksum = export_batch_service._calculate_file_checksum(tmp_path)

        # Verify it's a valid SHA256 hash (64 hex characters)
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

        # Verify consistency
        checksum2 = export_batch_service._calculate_file_checksum(tmp_path)
        assert checksum == checksum2
    finally:
        os.remove(tmp_path)


def test_cleanup_old_local_archives(export_batch_service):
    """Test cleanup of old local archives."""
    from datetime import datetime, timedelta, timezone

    export_dir = Path(export_batch_service.storage_config.local_export_dir)

    # Create test archive files with different ages
    old_file = export_dir / "export_batch_old.tar.zst"
    recent_file = export_dir / "export_batch_recent.tar.zst"

    old_file.write_text("old data")
    recent_file.write_text("recent data")

    # Set old file modification time to 100 days ago
    old_time = (datetime.now(timezone.utc) - timedelta(days=100)).timestamp()
    os.utime(old_file, (old_time, old_time))

    # Cleanup archives older than 90 days
    deleted_count = export_batch_service.cleanup_old_local_archives(days_old=90)

    # Verify old file deleted, recent file kept
    assert not old_file.exists()
    assert recent_file.exists()
    assert deleted_count == 1

    # Cleanup
    recent_file.unlink()


def test_celery_export_tasks_import():
    """Test that export optimization Celery tasks can be imported successfully."""
    try:
        from app.tasks.export_optimization import (
            calculate_consensus_for_chunks_export,
            cleanup_exported_chunks,
            create_export_batch_task,
        )

        assert callable(calculate_consensus_for_chunks_export)
        assert callable(create_export_batch_task)
        assert callable(cleanup_exported_chunks)
    except ImportError as e:
        pytest.fail(f"Failed to import export optimization Celery tasks: {e}")


def test_celery_task_routing_configuration():
    """Test that Celery task routing is properly configured."""
    from app.core.celery_app import celery_app

    # Check that export tasks are routed to correct queues
    task_routes = celery_app.conf.task_routes

    assert "calculate_consensus_for_chunks_export" in task_routes
    assert (
        task_routes["calculate_consensus_for_chunks_export"]["queue"] == "high_priority"
    )

    assert "create_export_batch_task" in task_routes
    assert task_routes["create_export_batch_task"]["queue"] == "high_priority"

    assert "cleanup_exported_chunks" in task_routes
    assert task_routes["cleanup_exported_chunks"]["queue"] == "low_priority"


def test_celery_priority_queues_configured():
    """Test that priority queues are properly configured."""
    from app.core.celery_app import celery_app

    queues = celery_app.conf.task_queues

    # Check priority queues exist
    assert "high_priority" in queues
    assert "medium_priority" in queues
    assert "low_priority" in queues

    # Check priority levels
    assert queues["high_priority"]["priority"] == 10
    assert queues["medium_priority"]["priority"] == 5
    assert queues["low_priority"]["priority"] == 1


def test_celery_task_rate_limits_configured():
    """Test that task rate limits are properly configured."""
    from app.core.celery_app import celery_app

    annotations = celery_app.conf.task_annotations

    # Check rate limits
    assert "calculate_consensus_for_chunks_export" in annotations
    assert annotations["calculate_consensus_for_chunks_export"]["rate_limit"] == "100/m"

    assert "create_export_batch_task" in annotations
    assert annotations["create_export_batch_task"]["rate_limit"] == "10/h"

    assert "cleanup_exported_chunks" in annotations
    assert annotations["cleanup_exported_chunks"]["rate_limit"] == "50/m"


def test_celery_beat_schedule_includes_export():
    """Test that beat schedule includes export batch creation."""
    from app.core.celery_app import celery_app

    beat_schedule = celery_app.conf.beat_schedule

    # Check export batch task is scheduled
    assert "create-export-batch" in beat_schedule
    assert beat_schedule["create-export-batch"]["task"] == "create_export_batch_task"
