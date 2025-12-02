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
    assert exported_item["is_consensus"] is True


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
    assert stats["filters_applied"]["quality_filters"]["validated_only"] is True


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
