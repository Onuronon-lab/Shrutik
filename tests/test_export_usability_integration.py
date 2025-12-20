"""
Integration tests for export usability improvements.

This module tests the end-to-end workflows for the export usability improvements
including role-based batch creation, download limits, and frontend integration.
"""

import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import StorageConfig
from app.core.security import get_password_hash
from app.db.database import Base, get_db
from app.main import app
from app.models.audio_chunk import AudioChunk
from app.models.export_batch import ExportBatch, ExportBatchStatus, StorageType
from app.models.export_download import ExportDownload
from app.models.language import Language
from app.models.script import DurationCategory, Script
from app.models.transcription import Transcription
from app.models.user import User, UserRole
from app.models.voice_recording import RecordingStatus, VoiceRecording
from app.services.export_batch_service import ExportBatchService

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_export_usability_integration.db"
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
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        name="Admin User",
        email="admin@sworik.com",
        password_hash=get_password_hash("testpassword123"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


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
def export_batch_service(db_session):
    """Create ExportBatchService with test database session."""
    storage_config = StorageConfig(
        storage_type="local", local_export_dir=tempfile.mkdtemp()
    )
    return ExportBatchService(db_session, storage_config)


@pytest.fixture
def ready_chunks_50(db_session, contributor_user):
    """Create 50 chunks ready for export."""
    language = Language(name="Bengali", code="bn")
    db_session.add(language)
    db_session.commit()

    script = Script(
        text="Test script for export",
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
        duration=100.0,
        status=RecordingStatus.CHUNKED,
    )
    db_session.add(recording)
    db_session.commit()

    chunks = []
    for i in range(50):
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


@pytest.fixture
def ready_chunks_10(db_session, contributor_user):
    """Create 10 chunks ready for export."""
    language = Language(name="Bengali", code="bn")
    db_session.add(language)
    db_session.commit()

    script = Script(
        text="Test script for export",
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
        duration=20.0,
        status=RecordingStatus.CHUNKED,
    )
    db_session.add(recording)
    db_session.commit()

    chunks = []
    for i in range(10):
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


def get_auth_headers(
    client: TestClient, user_email: str, password: str = "testpassword123"
):
    """Get authentication headers for a user."""
    login_response = client.post(
        "/api/auth/login", json={"email": user_email, "password": password}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# Task 8.1: Test batch creation workflow
class TestBatchCreationWorkflow:
    """Test batch creation workflow with role-based permissions."""

    def test_sworik_developer_creates_batch_with_50_chunks(
        self, client, sworik_developer_user, ready_chunks_50
    ):
        """Test sworik_developer creates batch with 50 chunks."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        # Mock file operations for batch creation
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1024),
            patch(
                "app.services.export_batch_service.ExportBatchService.generate_export_archive",
                return_value=("/tmp/test.tar.zst", 1024),
            ),
            patch(
                "app.services.export_batch_service.ExportBatchService.upload_to_storage",
                return_value="/exports/test.tar.zst",
            ),
            patch(
                "app.services.export_batch_service.ExportBatchService._calculate_file_checksum",
                return_value="abc123",
            ),
        ):
            response = client.post(
                "/api/export/batch/create",
                json={"force_create": False},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] is not None
        assert data["chunk_count"] == 50
        assert data["status"] == "completed"

    def test_admin_creates_batch_with_10_chunks(
        self, client, admin_user, ready_chunks_10
    ):
        """Test admin creates batch with 10 chunks."""
        headers = get_auth_headers(client, admin_user.email)

        # Mock file operations for batch creation
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1024),
            patch(
                "app.services.export_batch_service.ExportBatchService.generate_export_archive",
                return_value=("/tmp/test.tar.zst", 1024),
            ),
            patch(
                "app.services.export_batch_service.ExportBatchService.upload_to_storage",
                return_value="/exports/test.tar.zst",
            ),
            patch(
                "app.services.export_batch_service.ExportBatchService._calculate_file_checksum",
                return_value="abc123",
            ),
        ):
            response = client.post(
                "/api/export/batch/create",
                json={"force_create": False},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] is not None
        assert data["chunk_count"] == 10
        assert data["status"] == "completed"

    def test_force_create_ignored_for_non_admin_users(
        self, client, sworik_developer_user, ready_chunks_10
    ):
        """Test force_create ignored for non-admin users."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        response = client.post(
            "/api/export/batch/create",
            json={"force_create": True},
            headers=headers,
        )

        # Should fail because sworik_developer needs 50 chunks minimum, but only 10 available
        assert response.status_code == 400
        data = response.json()

        # The error is wrapped in the global error handler format
        assert "error" in data
        assert "message" in data["error"]

        # The message contains the structured error information
        message = data["error"]["message"]
        assert "Insufficient chunks" in message

    def test_error_messages_for_insufficient_chunks(
        self, client, sworik_developer_user, ready_chunks_10
    ):
        """Test error messages for insufficient chunks."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        response = client.post(
            "/api/export/batch/create",
            json={"force_create": False},
            headers=headers,
        )

        assert response.status_code == 400
        data = response.json()

        # Debug: print the actual response structure
        print("Response data:", data)

        # Check structured error response (wrapped by global error handler)
        assert "error" in data
        assert "message" in data["error"]

        # The error message should contain the structured information
        message = data["error"]["message"]
        assert "Insufficient chunks for batch creation" in message

    def test_admin_force_create_with_insufficient_chunks(
        self, client, admin_user, ready_chunks_10
    ):
        """Test admin can use force_create with insufficient chunks."""
        headers = get_auth_headers(client, admin_user.email)

        # Mock file operations for batch creation
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1024),
            patch(
                "app.services.export_batch_service.ExportBatchService.generate_export_archive",
                return_value=("/tmp/test.tar.zst", 1024),
            ),
            patch(
                "app.services.export_batch_service.ExportBatchService.upload_to_storage",
                return_value="/exports/test.tar.zst",
            ),
            patch(
                "app.services.export_batch_service.ExportBatchService._calculate_file_checksum",
                return_value="abc123",
            ),
        ):
            response = client.post(
                "/api/export/batch/create",
                json={"force_create": True},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["batch_id"] is not None
        assert data["chunk_count"] == 10
        assert data["status"] == "completed"


# Task 8.2: Test download workflow
class TestDownloadWorkflow:
    """Test download workflow with role-based limits."""

    def test_admin_unlimited_downloads(
        self, client, admin_user, ready_chunks_10, db_session
    ):
        """Test admin unlimited downloads."""
        headers = get_auth_headers(client, admin_user.email)

        # Create a temporary file for the test
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.zst") as tmp_file:
            tmp_file.write(b"test archive content")
            temp_file_path = tmp_file.name

        # Create a completed batch
        batch = ExportBatch(
            batch_id="test-batch-admin",
            archive_path=temp_file_path,
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            status=ExportBatchStatus.COMPLETED,
            created_by_id=admin_user.id,
        )
        db_session.add(batch)
        db_session.commit()

        # Create 10 downloads today (would exceed sworik_developer limit)
        for i in range(10):
            download = ExportDownload(
                batch_id=f"batch-{i}",
                user_id=admin_user.id,
                downloaded_at=datetime.now(timezone.utc),
            )
            db_session.add(download)
        db_session.commit()

        try:
            # Admin should still be able to download (unlimited)
            response = client.get(
                f"/api/export/batch/{batch.batch_id}/download",
                headers=headers,
            )

            assert response.status_code == 200
        finally:
            # Clean up the temporary file
            import os

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def test_sworik_developer_quota_enforcement(
        self, client, sworik_developer_user, ready_chunks_10, db_session
    ):
        """Test sworik_developer quota enforcement."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        # Create a temporary file for the test
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".tar.zst") as tmp_file:
            tmp_file.write(b"test archive content")
            temp_file_path = tmp_file.name

        # Create a completed batch
        batch = ExportBatch(
            batch_id="test-batch-dev",
            archive_path=temp_file_path,
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            status=ExportBatchStatus.COMPLETED,
            created_by_id=sworik_developer_user.id,
        )
        db_session.add(batch)
        db_session.commit()

        # Create 5 downloads today (at limit for sworik_developer)
        for i in range(5):
            download = ExportDownload(
                batch_id=f"batch-{i}",
                user_id=sworik_developer_user.id,
                downloaded_at=datetime.now(timezone.utc),
            )
            db_session.add(download)
        db_session.commit()

        try:
            # Should be blocked by quota
            response = client.get(
                f"/api/export/batch/{batch.batch_id}/download",
                headers=headers,
            )

            assert response.status_code == 429
            data = response.json()
            # The error is wrapped in the global error handler format
            assert "Daily download limit exceeded" in str(data)
        finally:
            # Clean up the temporary file
            import os

            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def test_quota_exhaustion_error_handling(
        self, client, sworik_developer_user, ready_chunks_10, db_session
    ):
        """Test quota exhaustion error handling."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        # Create a completed batch
        batch = ExportBatch(
            batch_id="test-batch-quota",
            archive_path="/exports/test.tar.zst",
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            status=ExportBatchStatus.COMPLETED,
            created_by_id=sworik_developer_user.id,
        )
        db_session.add(batch)
        db_session.commit()

        # Create 5 downloads today (at limit)
        for i in range(5):
            download = ExportDownload(
                batch_id=f"batch-{i}",
                user_id=sworik_developer_user.id,
                downloaded_at=datetime.now(timezone.utc),
            )
            db_session.add(download)
        db_session.commit()

        response = client.get(
            f"/api/export/batch/{batch.batch_id}/download",
            headers=headers,
        )

        assert response.status_code == 429
        data = response.json()

        # Check structured error response (wrapped by global error handler)
        assert "error" in data
        assert "message" in data["error"]

        # The error message should contain quota information
        message = data["error"]["message"]
        assert "Daily download limit exceeded" in message

    def test_quota_reset_at_midnight_utc(
        self, client, sworik_developer_user, ready_chunks_10, db_session
    ):
        """Test quota reset at midnight UTC."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        # Create a completed batch
        batch = ExportBatch(
            batch_id="test-batch-reset",
            archive_path="/exports/test.tar.zst",
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            status=ExportBatchStatus.COMPLETED,
            created_by_id=sworik_developer_user.id,
        )
        db_session.add(batch)
        db_session.commit()

        # Create 5 downloads yesterday (should not count)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        for i in range(5):
            download = ExportDownload(
                batch_id=f"batch-yesterday-{i}",
                user_id=sworik_developer_user.id,
                downloaded_at=yesterday,
            )
            db_session.add(download)
        db_session.commit()

        # Should be able to download (quota reset)
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1024),
        ):
            response = client.get(
                f"/api/export/batch/{batch.batch_id}/download",
                headers=headers,
            )

        assert response.status_code == 200

    def test_download_quota_endpoint(self, client, sworik_developer_user, db_session):
        """Test download quota endpoint."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        # Create 2 downloads today
        for i in range(2):
            download = ExportDownload(
                batch_id=f"batch-{i}",
                user_id=sworik_developer_user.id,
                downloaded_at=datetime.now(timezone.utc),
            )
            db_session.add(download)
        db_session.commit()

        response = client.get(
            "/api/export/batch/download/quota",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["downloads_today"] == 2
        assert data["downloads_remaining"] == 3  # 5 - 2
        assert data["daily_limit"] == 5
        assert data["reset_time"] is not None

    def test_admin_quota_endpoint_unlimited(self, client, admin_user, db_session):
        """Test admin quota endpoint shows unlimited."""
        headers = get_auth_headers(client, admin_user.email)

        # Create 10 downloads today
        for i in range(10):
            download = ExportDownload(
                batch_id=f"batch-{i}",
                user_id=admin_user.id,
                downloaded_at=datetime.now(timezone.utc),
            )
            db_session.add(download)
        db_session.commit()

        response = client.get(
            "/api/export/batch/download/quota",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["downloads_today"] == 10
        assert data["downloads_remaining"] == -1  # Unlimited
        assert data["daily_limit"] == -1  # Unlimited
        assert data["reset_time"] is None  # No reset needed for unlimited


# Task 8.3: Test frontend integration
class TestFrontendIntegration:
    """Test frontend integration with enhanced features."""

    def test_immediate_download_button_after_batch_creation(
        self, client, admin_user, ready_chunks_10, db_session
    ):
        """Test immediate download button after batch creation."""
        headers = get_auth_headers(client, admin_user.email)

        # Mock file operations for batch creation
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1024),
            patch(
                "app.services.export_batch_service.ExportBatchService.generate_export_archive",
                return_value=("/tmp/test.tar.zst", 1024),
            ),
            patch(
                "app.services.export_batch_service.ExportBatchService.upload_to_storage",
                return_value="/exports/test.tar.zst",
            ),
            patch(
                "app.services.export_batch_service.ExportBatchService._calculate_file_checksum",
                return_value="abc123",
            ),
        ):
            # Create batch
            create_response = client.post(
                "/api/export/batch/create",
                json={"force_create": True},
                headers=headers,
            )

        assert create_response.status_code == 200
        batch_data = create_response.json()

        # Verify batch is immediately ready for download
        assert batch_data["status"] == "completed"
        assert batch_data["batch_id"] is not None

        # Test that download endpoint works immediately
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1024),
        ):
            download_response = client.get(
                f"/api/export/batch/{batch_data['batch_id']}/download",
                headers=headers,
            )

        assert download_response.status_code == 200

    def test_quota_card_updates_after_downloads(
        self, client, sworik_developer_user, ready_chunks_10, db_session
    ):
        """Test quota card updates after downloads."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        # Check initial quota
        quota_response = client.get(
            "/api/export/batch/download/quota",
            headers=headers,
        )
        assert quota_response.status_code == 200
        initial_quota = quota_response.json()
        assert initial_quota["downloads_today"] == 0
        assert initial_quota["downloads_remaining"] == 5

        # Create a completed batch
        batch = ExportBatch(
            batch_id="test-batch-quota-update",
            archive_path="/exports/test.tar.zst",
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            status=ExportBatchStatus.COMPLETED,
            created_by_id=sworik_developer_user.id,
        )
        db_session.add(batch)
        db_session.commit()

        # Download the batch
        with (
            patch("os.path.exists", return_value=True),
            patch("os.path.getsize", return_value=1024),
        ):
            download_response = client.get(
                f"/api/export/batch/{batch.batch_id}/download",
                headers=headers,
            )
        assert download_response.status_code == 200

        # Check updated quota
        updated_quota_response = client.get(
            "/api/export/batch/download/quota",
            headers=headers,
        )
        assert updated_quota_response.status_code == 200
        updated_quota = updated_quota_response.json()
        assert updated_quota["downloads_today"] == 1
        assert updated_quota["downloads_remaining"] == 4

    def test_error_message_display_with_suggestions(
        self, client, sworik_developer_user, ready_chunks_10
    ):
        """Test error message display with suggestions."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        # Try to create batch with insufficient chunks
        response = client.post(
            "/api/export/batch/create",
            json={"force_create": False},
            headers=headers,
        )

        assert response.status_code == 400
        data = response.json()

        # Verify structured error format that frontend can parse
        assert "error" in data
        assert "message" in data["error"]

        # The error message should contain the basic error information
        message = data["error"]["message"]
        assert "Insufficient chunks for batch creation" in message

    def test_disabled_download_buttons_with_tooltips(
        self, client, sworik_developer_user, ready_chunks_10, db_session
    ):
        """Test disabled download buttons with tooltips."""
        headers = get_auth_headers(client, sworik_developer_user.email)

        # Create a completed batch
        batch = ExportBatch(
            batch_id="test-batch-disabled",
            archive_path="/exports/test.tar.zst",
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            status=ExportBatchStatus.COMPLETED,
            created_by_id=sworik_developer_user.id,
        )
        db_session.add(batch)
        db_session.commit()

        # Exhaust quota (5 downloads)
        for i in range(5):
            download = ExportDownload(
                batch_id=f"batch-{i}",
                user_id=sworik_developer_user.id,
                downloaded_at=datetime.now(timezone.utc),
            )
            db_session.add(download)
        db_session.commit()

        # Check quota is exhausted
        quota_response = client.get(
            "/api/export/batch/download/quota",
            headers=headers,
        )
        assert quota_response.status_code == 200
        quota_data = quota_response.json()
        assert quota_data["downloads_remaining"] == 0

        # Try to download - should get detailed error for frontend tooltip
        download_response = client.get(
            f"/api/export/batch/{batch.batch_id}/download",
            headers=headers,
        )
        assert download_response.status_code == 429

        error_data = download_response.json()

        # The error is wrapped by the global error handler
        assert "error" in error_data
        assert "message" in error_data["error"]

        # The message should contain quota information
        message = error_data["error"]["message"]
        assert "Daily download limit exceeded" in message

    def test_batch_status_visibility_and_progress_indicators(
        self, client, admin_user, ready_chunks_10, db_session
    ):
        """Test batch status visibility and progress indicators."""
        headers = get_auth_headers(client, admin_user.email)

        # Create batches in different states
        batches = [
            ExportBatch(
                batch_id="batch-pending",
                archive_path="",
                storage_type=StorageType.LOCAL,
                chunk_count=10,
                chunk_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                status=ExportBatchStatus.PENDING,
                created_by_id=admin_user.id,
            ),
            ExportBatch(
                batch_id="batch-processing",
                archive_path="",
                storage_type=StorageType.LOCAL,
                chunk_count=10,
                chunk_ids=[11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                status=ExportBatchStatus.PROCESSING,
                created_by_id=admin_user.id,
            ),
            ExportBatch(
                batch_id="batch-completed",
                archive_path="/exports/completed.tar.zst",
                storage_type=StorageType.LOCAL,
                chunk_count=10,
                chunk_ids=[21, 22, 23, 24, 25, 26, 27, 28, 29, 30],
                status=ExportBatchStatus.COMPLETED,
                created_by_id=admin_user.id,
                completed_at=datetime.now(timezone.utc),
            ),
            ExportBatch(
                batch_id="batch-failed",
                archive_path="",
                storage_type=StorageType.LOCAL,
                chunk_count=10,
                chunk_ids=[31, 32, 33, 34, 35, 36, 37, 38, 39, 40],
                status=ExportBatchStatus.FAILED,
                error_message="Test error",
                created_by_id=admin_user.id,
            ),
        ]

        for batch in batches:
            db_session.add(batch)
        db_session.commit()

        # List batches
        response = client.get(
            "/api/export/batch/list",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all batch statuses are visible
        batch_statuses = {
            batch["batch_id"]: batch["status"] for batch in data["batches"]
        }
        assert batch_statuses["batch-pending"] == "pending"
        assert batch_statuses["batch-processing"] == "processing"
        assert batch_statuses["batch-completed"] == "completed"
        assert batch_statuses["batch-failed"] == "failed"

        # Verify completed batch has completion time
        completed_batch = next(
            b for b in data["batches"] if b["batch_id"] == "batch-completed"
        )
        assert completed_batch["completed_at"] is not None

        # Verify failed batch has error message
        failed_batch = next(
            b for b in data["batches"] if b["batch_id"] == "batch-failed"
        )
        assert failed_batch["error_message"] == "Test error"

    def test_batch_list_filtering_and_pagination(self, client, admin_user, db_session):
        """Test batch list filtering and pagination."""
        headers = get_auth_headers(client, admin_user.email)

        # Create multiple batches with different statuses and dates
        now = datetime.now(timezone.utc)
        batches = []

        for i in range(15):
            status = (
                ExportBatchStatus.COMPLETED if i % 3 == 0 else ExportBatchStatus.PENDING
            )
            created_at = now - timedelta(days=i)

            batch = ExportBatch(
                batch_id=f"batch-{i:02d}",
                archive_path=(
                    f"/exports/batch-{i:02d}.tar.zst"
                    if status == ExportBatchStatus.COMPLETED
                    else ""
                ),
                storage_type=StorageType.LOCAL,
                chunk_count=10,
                chunk_ids=list(range(i * 10, (i + 1) * 10)),
                status=status,
                created_by_id=admin_user.id,
                created_at=created_at,
                completed_at=(
                    created_at if status == ExportBatchStatus.COMPLETED else None
                ),
            )
            batches.append(batch)
            db_session.add(batch)

        db_session.commit()

        # Test pagination
        response = client.get(
            "/api/export/batch/list?page=1&page_size=5",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["batches"]) == 5
        assert data["total_count"] == 15
        assert data["page"] == 1
        assert data["page_size"] == 5

        # Test status filtering
        response = client.get(
            "/api/export/batch/list?status_filter=completed",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert all(batch["status"] == "completed" for batch in data["batches"])

        # Test date filtering
        date_from = (now - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%S")
        response = client.get(
            f"/api/export/batch/list?date_from={date_from}",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        # Should have batches from last 5 days (6 batches: 0, 1, 2, 3, 4, 5)
        assert len(data["batches"]) == 6

    def test_role_based_batch_access_control(
        self, client, admin_user, sworik_developer_user, db_session
    ):
        """Test role-based batch access control."""
        admin_headers = get_auth_headers(client, admin_user.email)
        dev_headers = get_auth_headers(client, sworik_developer_user.email)

        # Create batches by different users
        admin_batch = ExportBatch(
            batch_id="admin-batch",
            archive_path="/exports/admin.tar.zst",
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            status=ExportBatchStatus.COMPLETED,
            created_by_id=admin_user.id,
        )

        dev_batch = ExportBatch(
            batch_id="dev-batch",
            archive_path="/exports/dev.tar.zst",
            storage_type=StorageType.LOCAL,
            chunk_count=10,
            chunk_ids=[11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            status=ExportBatchStatus.COMPLETED,
            created_by_id=sworik_developer_user.id,
        )

        db_session.add(admin_batch)
        db_session.add(dev_batch)
        db_session.commit()

        # Admin can see all batches
        admin_list_response = client.get(
            "/api/export/batch/list",
            headers=admin_headers,
        )
        assert admin_list_response.status_code == 200
        admin_batches = admin_list_response.json()["batches"]
        admin_batch_ids = {batch["batch_id"] for batch in admin_batches}
        assert "admin-batch" in admin_batch_ids
        assert "dev-batch" in admin_batch_ids

        # Developer can only see their own batches
        dev_list_response = client.get(
            "/api/export/batch/list",
            headers=dev_headers,
        )
        assert dev_list_response.status_code == 200
        dev_batches = dev_list_response.json()["batches"]
        dev_batch_ids = {batch["batch_id"] for batch in dev_batches}
        assert "admin-batch" not in dev_batch_ids
        assert "dev-batch" in dev_batch_ids

        # Developer cannot access admin's batch directly
        dev_access_response = client.get(
            "/api/export/batch/admin-batch",
            headers=dev_headers,
        )
        assert dev_access_response.status_code == 403

        # Admin can access any batch
        admin_access_response = client.get(
            "/api/export/batch/dev-batch",
            headers=admin_headers,
        )
        assert admin_access_response.status_code == 200
