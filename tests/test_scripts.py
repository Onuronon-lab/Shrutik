import pytest
from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.language import Language
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
def test_language(db_session):
    """Create a test language in the database."""
    language = Language(name="Bangla", code="bn")
    db_session.add(language)
    db_session.commit()
    db_session.refresh(language)
    return language


@pytest.fixture
def admin_user(db_session):
    """Create an admin user."""
    user = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=get_password_hash("TestPass123!"),
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def contributor_user(db_session):
    """Create a contributor user."""
    user = User(
        name="Contributor User",
        email="contributor@example.com",
        password_hash=get_password_hash("TestPass123!"),
        role=UserRole.CONTRIBUTOR,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(client):
    """Create an admin user and return auth token."""
    db = TestingSessionLocal()
    user = User(
        name="Admin User",
        email="admin@example.com",
        password_hash=get_password_hash("adminpass123"),
        role=UserRole.ADMIN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"},
    )
    return login_response.json()["access_token"]


@pytest.fixture
def contributor_user(client):
    """Create a contributor user and return auth token."""
    db = TestingSessionLocal()
    user = User(
        name="Contributor User",
        email="contributor@example.com",
        password_hash=get_password_hash("contributorpass123"),
        role=UserRole.CONTRIBUTOR,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    # Login to get token
    login_response = client.post(
        "/api/auth/login",
        json={"email": "contributor@example.com", "password": "contributorpass123"},
    )
    return login_response.json()["access_token"]


@pytest.fixture
def sample_script_data(test_language):
    """Sample script data for testing."""
    return {
        "text": "এটি একটি নমুনা বাংলা স্ক্রিপ্ট যা পরীক্ষার জন্য ব্যবহৃত হচ্ছে। এই স্ক্রিপ্টটি দুই মিনিটের জন্য উপযুক্ত। এতে পর্যাপ্ত শব্দ রয়েছে যা একজন ব্যক্তি দুই মিনিটে পড়তে পারবেন। এটি একটি সম্পূর্ণ এবং অর্থপূর্ণ বাক্য গঠন করে।",
        "duration_category": "2_minutes",
        "language_id": test_language.id,
        "meta_data": {"source": "test"},
    }


def test_create_script_success(client, admin_user, sample_script_data):
    """Test successful script creation by admin."""
    headers = {"Authorization": f"Bearer {admin_user}"}
    response = client.post("/api/scripts/", json=sample_script_data, headers=headers)

    assert response.status_code == 201
    data = response.json()
    assert data["text"] == sample_script_data["text"]
    assert data["duration_category"] == sample_script_data["duration_category"]
    assert data["language_id"] == sample_script_data["language_id"]
    assert "id" in data
    assert "created_at" in data


def test_create_script_contributor_forbidden(
    client, contributor_user, sample_script_data
):
    """Test that contributors cannot create scripts."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    response = client.post("/api/scripts/", json=sample_script_data, headers=headers)

    assert response.status_code == 403


def test_create_script_invalid_language(client, admin_user, sample_script_data):
    """Test script creation with invalid language ID."""
    sample_script_data["language_id"] = 999  # Non-existent language
    headers = {"Authorization": f"Bearer {admin_user}"}
    response = client.post("/api/scripts/", json=sample_script_data, headers=headers)

    assert response.status_code == 400
    assert "Language with ID 999 not found" in response.json()["detail"]


def test_create_script_empty_text(client, admin_user, sample_script_data):
    """Test script creation with empty text."""
    sample_script_data["text"] = ""
    headers = {"Authorization": f"Bearer {admin_user}"}
    response = client.post("/api/scripts/", json=sample_script_data, headers=headers)

    assert response.status_code == 422  # Validation error


def test_get_random_script_success(
    client, admin_user, contributor_user, sample_script_data
):
    """Test getting random script by contributor."""
    # First create a script as admin
    headers = {"Authorization": f"Bearer {admin_user}"}
    client.post("/api/scripts/", json=sample_script_data, headers=headers)

    # Then get random script as contributor
    headers = {"Authorization": f"Bearer {contributor_user}"}
    response = client.get(
        "/api/scripts/random?duration_category=2_minutes", headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == sample_script_data["text"]
    assert data["duration_category"] == "2_minutes"


def test_get_random_script_not_found(client, contributor_user, test_language):
    """Test getting random script when none exist."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    response = client.get(
        f"/api/scripts/random?duration_category=5_minutes&language_id={test_language.id}",
        headers=headers,
    )

    assert response.status_code == 404
    assert "No scripts found" in response.json()["detail"]


def test_list_scripts_admin(client, admin_user, sample_script_data):
    """Test listing scripts as admin."""
    # Create a script first
    headers = {"Authorization": f"Bearer {admin_user}"}
    client.post("/api/scripts/", json=sample_script_data, headers=headers)

    # List scripts
    response = client.get("/api/scripts/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "scripts" in data
    assert "total" in data
    assert data["total"] >= 1
    assert len(data["scripts"]) >= 1


def test_list_scripts_contributor_forbidden(client, contributor_user):
    """Test that contributors cannot list all scripts."""
    headers = {"Authorization": f"Bearer {contributor_user}"}
    response = client.get("/api/scripts/", headers=headers)

    assert response.status_code == 403


def test_get_script_by_id(client, admin_user, sample_script_data):
    """Test getting specific script by ID."""
    headers = {"Authorization": f"Bearer {admin_user}"}

    # Create script
    create_response = client.post(
        "/api/scripts/", json=sample_script_data, headers=headers
    )
    script_id = create_response.json()["id"]

    # Get script by ID
    response = client.get(f"/api/scripts/{script_id}", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == script_id
    assert data["text"] == sample_script_data["text"]


def test_update_script(client, admin_user, sample_script_data):
    """Test updating a script."""
    headers = {"Authorization": f"Bearer {admin_user}"}

    # Create script
    create_response = client.post(
        "/api/scripts/", json=sample_script_data, headers=headers
    )
    script_id = create_response.json()["id"]

    # Update script with longer text that meets validation requirements
    update_data = {
        "text": "আপডেট করা স্ক্রিপ্ট টেক্সট যা পরীক্ষার জন্য ব্যবহৃত হচ্ছে। এটি একটি দীর্ঘ টেক্সট যা যথেষ্ট শব্দ রয়েছে। এই স্ক্রিপ্টটি দুই মিনিটের জন্য উপযুক্ত। এতে পর্যাপ্ত শব্দ রয়েছে যা একজন ব্যক্তি দুই মিনিটে পড়তে পারবেন।"
    }
    response = client.put(
        f"/api/scripts/{script_id}", json=update_data, headers=headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == update_data["text"]


def test_delete_script(client, admin_user, sample_script_data):
    """Test deleting a script."""
    headers = {"Authorization": f"Bearer {admin_user}"}

    # Create script
    create_response = client.post(
        "/api/scripts/", json=sample_script_data, headers=headers
    )
    script_id = create_response.json()["id"]

    # Delete script
    response = client.delete(f"/api/scripts/{script_id}", headers=headers)

    assert response.status_code == 204

    # Verify script is deleted
    get_response = client.get(f"/api/scripts/{script_id}", headers=headers)
    assert get_response.status_code == 404


def test_validate_script_content(client, admin_user):
    """Test script content validation endpoint."""
    headers = {"Authorization": f"Bearer {admin_user}"}

    response = client.post(
        "/api/scripts/validate",
        params={"text": "এটি একটি পরীক্ষার স্ক্রিপ্ট।", "duration_category": "2_minutes"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "is_valid" in data
    assert "word_count" in data
    assert "character_count" in data
    assert "estimated_duration" in data


def test_get_script_statistics(client, admin_user, sample_script_data):
    """Test getting script statistics."""
    headers = {"Authorization": f"Bearer {admin_user}"}

    # Create a script first
    client.post("/api/scripts/", json=sample_script_data, headers=headers)

    # Get statistics
    response = client.get("/api/scripts/statistics", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_scripts" in data
    assert "by_duration" in data
    assert "by_language" in data
    assert data["total_scripts"] >= 1
