import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_db, Base
from app.models.user import User, UserRole
from app.models.language import Language
from app.models.script import Script, DurationCategory
from app.core.security import get_password_hash

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_voice_recordings.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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
def test_language(client):
    """Create a test language in the database."""
    db = TestingSessionLocal()
    language = Language(name="Bangla", code="bn")
    db.add(language)
    db.commit()
    db.refresh(language)
    db.close()
    return language


@pytest.fixture
def contributor_user(client):
    """Create a contributor user and return auth token."""
    db = TestingSessionLocal()
    user = User(
        name="Contributor User",
        email="contributor@example.com",
        password_hash=get_password_hash("contributorpass123"),
        role=UserRole.CONTRIBUTOR
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    # Login to get token
    login_response = client.post("/api/auth/login", json={
        "email": "contributor@example.com",
        "password": "contributorpass123"
    })
    return login_response.json()["access_token"]


@pytest.fixture
def admin_user(client):
    """Create an admin user and return auth token."""
    db = TestingSessionLocal()
    user = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        role=UserRole.ADMIN
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    
    # Login to get token
    login_response = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "adminpass123"
    })
    return login_response.json()["access_token"]


@pytest.fixture
def sample_script(client, test_language):
    """Create a sample script for testing."""
    db = TestingSessionLocal()
    script = Script(
        text="এটি একটি নমুনা বাংলা স্ক্রিপ্ট যা পরীক্ষার জন্য ব্যবহৃত হচ্ছে। এই স্ক্রিপ্টটি দুই মিনিটের জন্য উপযুক্ত।",
        duration_category=DurationCategory.SHORT,
        language_id=test_language.id,
        meta_data={"source": "test"}
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    db.close()
    return script


def test_create_recording_session_success(client, contributor_user, sample_script):
    """Test successful recording session creation."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    session_data = {
        "script_id": sample_script.id,
        "language_id": sample_script.language_id
    }
    
    response = client.post("/api/recordings/sessions", json=session_data, headers=headers)
    
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
    headers = {"Authorization": f"Bearer {contributor_user}"}
    session_data = {
        "script_id": 999,  # Non-existent script
    }
    
    response = client.post("/api/recordings/sessions", json=session_data, headers=headers)
    
    assert response.status_code == 404
    assert "Script not found" in response.json()["detail"]


def test_create_recording_session_unauthorized(client, sample_script):
    """Test recording session creation without authentication."""
    session_data = {
        "script_id": sample_script.id,
    }
    
    response = client.post("/api/recordings/sessions", json=session_data)
    
    assert response.status_code in [401, 403]  # Either unauthorized or forbidden


def test_get_user_recordings_empty(client, contributor_user):
    """Test getting user recordings when none exist."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    
    response = client.get("/api/recordings/", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["recordings"] == []
    assert data["total"] == 0
    assert data["page"] == 1


def test_get_user_recordings_pagination(client, contributor_user):
    """Test user recordings pagination parameters."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    
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
    headers = {"Authorization": f"Bearer {admin_user}"}
    
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
    headers = {"Authorization": f"Bearer {contributor_user}"}
    
    response = client.get("/api/recordings/admin/statistics", headers=headers)
    
    assert response.status_code == 403


def test_get_all_recordings_admin(client, admin_user):
    """Test getting all recordings as admin."""
    headers = {"Authorization": f"Bearer {admin_user}"}
    
    response = client.get("/api/recordings/admin/all", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "recordings" in data
    assert "total" in data
    assert "page" in data
    assert "per_page" in data


def test_get_all_recordings_contributor_forbidden(client, contributor_user):
    """Test that contributors cannot access all recordings."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    
    response = client.get("/api/recordings/admin/all", headers=headers)
    
    assert response.status_code == 403


def test_get_nonexistent_recording(client, contributor_user):
    """Test getting a recording that doesn't exist."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    
    response = client.get("/api/recordings/999", headers=headers)
    
    assert response.status_code == 404
    assert "Recording not found" in response.json()["detail"]


def test_get_recording_progress_nonexistent(client, contributor_user):
    """Test getting progress for a recording that doesn't exist."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    
    response = client.get("/api/recordings/999/progress", headers=headers)
    
    assert response.status_code == 404
    assert "Recording not found" in response.json()["detail"]


def test_delete_nonexistent_recording(client, contributor_user):
    """Test deleting a recording that doesn't exist."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    
    response = client.delete("/api/recordings/999", headers=headers)
    
    assert response.status_code == 404
    assert "Recording not found" in response.json()["detail"]