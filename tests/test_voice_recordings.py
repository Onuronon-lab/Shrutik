import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.language import Language
from app.models.script import DurationCategory, Script
from app.models.user import User, UserRole


def get_auth_headers(client: TestClient, email: str, password: str = "TestPass123!"):
    """Helper function to get authentication headers."""
    login_response = client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    if login_response.status_code != 200:
        raise Exception(f"Login failed: {login_response.text}")

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        name=f"Test User {unique_id}",
        email=f"test-{unique_id}@example.com",
        password_hash=get_password_hash("TestPass123!"),
        role=UserRole.CONTRIBUTOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_language(db_session):
    """Create a test language in the database."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    language = Language(name=f"Bangla-{unique_id}", code=f"bn-{unique_id}")
    db_session.add(language)
    db_session.commit()
    db_session.refresh(language)
    return language


@pytest.fixture
def contributor_user(db_session):
    """Create a contributor user."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        name=f"Contributor User {unique_id}",
        email=f"contributor-{unique_id}@example.com",
        password_hash=get_password_hash("TestPass123!"),
        role=UserRole.CONTRIBUTOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user."""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user = User(
        name=f"Admin User {unique_id}",
        email=f"admin-{unique_id}@example.com",
        password_hash=get_password_hash("TestPass123!"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_script(db_session, test_language):
    """Create a sample script for testing."""
    script = Script(
        text="এটি একটি নমুনা বাংলা স্ক্রিপ্ট যা পরীক্ষার জন্য ব্যবহৃত হচ্ছে। এই স্ক্রিপ্টটি দুই মিনিটের জন্য উপযুক্ত।",
        duration_category=DurationCategory.SHORT,
        language_id=test_language.id,
        meta_data={"source": "test"},
    )
    db_session.add(script)
    db_session.commit()
    db_session.refresh(script)
    return script


def test_create_recording_session_success(client, contributor_user, sample_script):
    """Test successful recording session creation."""
    headers = get_auth_headers(client, contributor_user.email)
    session_data = {
        "script_id": sample_script.id,
        "language_id": sample_script.language_id,
    }

    response = client.post(
        "/api/recordings/sessions", json=session_data, headers=headers
    )

    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["script_id"] == sample_script.id
    assert data["script_text"] == sample_script.text
    assert data["language_id"] == sample_script.language_id
    assert "created_at" in data
    assert "expires_at" in data


def test_create_recording_session_invalid_script(client, contributor_user):
    """Test recording session creation with invalid script ID."""
    headers = get_auth_headers(client, contributor_user.email)
    session_data = {
        "script_id": 999,  # Non-existent script
    }

    response = client.post(
        "/api/recordings/sessions", json=session_data, headers=headers
    )

    assert response.status_code == 404
    assert "Script not found" in response.json()["error"]["message"]


def test_create_recording_session_unauthorized(client, sample_script):
    """Test recording session creation without authentication."""
    session_data = {
        "script_id": sample_script.id,
    }

    response = client.post("/api/recordings/sessions", json=session_data)

    assert response.status_code in [401, 403]  # Either unauthorized or forbidden


def test_get_user_recordings_empty(client, contributor_user):
    """Test getting user recordings when none exist."""
    headers = get_auth_headers(client, contributor_user.email)

    response = client.get("/api/recordings/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["recordings"] == []
    assert data["total"] == 0
    assert data["page"] == 1


def test_get_user_recordings_pagination(client, contributor_user):
    """Test user recordings pagination parameters."""
    headers = get_auth_headers(client, contributor_user.email)

    response = client.get("/api/recordings/?skip=10&limit=5", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "recordings" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data
    assert data["per_page"] == 5


def test_get_recording_statistics_admin(client, admin_user):
    """Test getting recording statistics as admin."""
    headers = get_auth_headers(client, admin_user.email)

    response = client.get("/api/recordings/admin/statistics", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_recordings" in data
    assert "by_status" in data
    assert "by_duration_category" in data
    assert "by_language" in data
    assert "total_duration_hours" in data
    assert "average_duration_minutes" in data


def test_get_recording_statistics_contributor_forbidden(client, contributor_user):
    """Test that contributors cannot access recording statistics."""
    headers = get_auth_headers(client, contributor_user.email)

    response = client.get("/api/recordings/admin/statistics", headers=headers)

    assert response.status_code == 403


def test_get_all_recordings_admin(client, admin_user):
    """Test getting all recordings as admin."""
    headers = get_auth_headers(client, admin_user.email)

    response = client.get("/api/recordings/admin/all", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "recordings" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


def test_get_all_recordings_contributor_forbidden(client, contributor_user):
    """Test that contributors cannot access all recordings."""
    headers = get_auth_headers(client, contributor_user.email)

    response = client.get("/api/recordings/admin/all", headers=headers)

    assert response.status_code == 403


def test_get_nonexistent_recording(client, contributor_user):
    """Test getting a recording that doesn't exist."""
    headers = get_auth_headers(client, contributor_user.email)

    response = client.get("/api/recordings/999", headers=headers)

    assert response.status_code == 404
    assert "Recording not found" in response.json()["error"]["message"]


def test_get_recording_progress_nonexistent(client, contributor_user):
    """Test getting progress for a recording that doesn't exist."""
    headers = get_auth_headers(client, contributor_user.email)

    response = client.get("/api/recordings/999/progress", headers=headers)

    assert response.status_code == 404
    assert "Recording not found" in response.json()["error"]["message"]


def test_delete_nonexistent_recording(client, contributor_user):
    """Test deleting a recording that doesn't exist."""
    headers = get_auth_headers(client, contributor_user.email)

    response = client.delete("/api/recordings/999", headers=headers)

    assert response.status_code == 404
    assert "Recording not found" in response.json()["error"]["message"]
