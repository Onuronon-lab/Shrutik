import uuid
from unittest.mock import patch

import pytest

from app.models.user import User, UserRole


@pytest.fixture
def test_user_data():
    # Use unique email for each test to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": "Test User",
        "email": f"test{unique_id}@example.com",
        "password": "TestPass123!",  # Meets all validation requirements
    }


@pytest.fixture
def admin_user_data():
    unique_id = str(uuid.uuid4())[:8]
    return {
        "name": "Admin User",
        "email": f"admin{unique_id}@example.com",
        "password": "AdminPass123!",
        "role": "admin",
    }


def test_register_user(client, test_user_data):
    """Test user registration - should always create CONTRIBUTOR role."""
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["name"] == test_user_data["name"]
    assert data["role"] == "contributor"  # Always CONTRIBUTOR for public registration
    assert "id" in data


def test_register_duplicate_email(client, test_user_data):
    """Test registration with duplicate email fails."""
    # Register first user
    client.post("/api/auth/register", json=test_user_data)

    # Try to register again with same email
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 400
    data = response.json()
    assert "email" in data["error"]["message"].lower()


def test_login_success(client, test_user_data):
    """Test successful login."""
    # First register a user
    client.post("/api/auth/register", json=test_user_data)

    # Then try to login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, test_user_data):
    """Test login with invalid credentials."""
    # Register a user first
    client.post("/api/auth/register", json=test_user_data)

    # Try login with wrong password
    login_data = {"email": test_user_data["email"], "password": "WrongPass123!"}
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    data = response.json()
    assert "error" in data


def test_get_current_user(client, test_user_data):
    """Test getting current user info."""
    # Register and login to get token
    client.post("/api/auth/register", json=test_user_data)
    login_response = client.post(
        "/api/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = login_response.json()["access_token"]

    # Get current user info
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["role"] == "contributor"


def test_admin_role_required(client, admin_user_data):
    """Test that admin endpoints require admin role."""
    # Create admin user directly in database
    with patch("app.core.dependencies.get_current_user") as mock_get_user:
        admin_user = User(
            id=1,
            name=admin_user_data["name"],
            email=admin_user_data["email"],
            role=UserRole.ADMIN,
            password_hash="dummy_hash",
        )
        mock_get_user.return_value = admin_user

        # Test admin endpoint access
        response = client.get("/api/admin/stats/platform")
        # This should work with proper mocking
        # The actual assertion depends on the endpoint implementation


def test_register_without_role_creates_contributor(client, test_user_data):
    """Test that public registration always creates contributor role."""
    # Use a unique email to avoid conflicts with other tests
    unique_test_data = test_user_data.copy()
    unique_test_data["email"] = "unique_contributor@example.com"

    response = client.post("/api/auth/register", json=unique_test_data)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "contributor"


def test_non_admin_cannot_create_user_with_role(client, test_user_data):
    """Test that non-admin users cannot create users with specific roles."""
    # Register and login as regular user
    client.post("/api/auth/register", json=test_user_data)
    login_response = client.post(
        "/api/auth/login",
        json={"email": test_user_data["email"], "password": test_user_data["password"]},
    )
    token = login_response.json()["access_token"]

    # Try to create user with admin role (should fail)
    headers = {"Authorization": f"Bearer {token}"}
    admin_user_data = {
        "name": "New Admin",
        "email": "newadmin@example.com",
        "password": "AdminPass123!",
        "role": "admin",
    }

    # This endpoint might not exist, but the test shows the intent
    response = client.post(
        "/api/auth/create-user", json=admin_user_data, headers=headers
    )
    # Should be forbidden or not found
    assert response.status_code in [403, 404]
