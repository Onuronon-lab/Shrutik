import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_db, Base
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
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
def test_user_data():
    return {
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpassword123"
        # Note: role is intentionally excluded - public registration always creates CONTRIBUTOR
    }


@pytest.fixture
def admin_user(client: TestClient):
    """Create an admin user directly in the database for testing."""
    db = TestingSessionLocal()
    try:
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password_hash=get_password_hash("adminpass123"),
            role=UserRole.ADMIN
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        # Login to get token
        login_response = client.post("/api/auth/login", json={
            "email": "admin@example.com",
            "password": "adminpass123"
        })
        token = login_response.json()["access_token"]
        
        return {"user": admin, "token": token}
    finally:
        db.close()


def test_register_user(client: TestClient, test_user_data):
    """Test user registration - should always create CONTRIBUTOR role."""
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["name"] == test_user_data["name"]
    assert data["role"] == "contributor"  # Always CONTRIBUTOR for public registration
    assert "id" in data


def test_register_duplicate_email(client: TestClient, test_user_data):
    """Test registration with duplicate email fails."""
    # Register first user
    client.post("/api/auth/register", json=test_user_data)
    
    # Try to register with same email
    response = client.post("/api/auth/register", json=test_user_data)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login_success(client: TestClient, test_user_data):
    """Test successful login."""
    # Register user first
    client.post("/api/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client: TestClient, test_user_data):
    """Test login with invalid credentials."""
    # Register user first
    client.post("/api/auth/register", json=test_user_data)
    
    # Try login with wrong password
    login_data = {
        "email": test_user_data["email"],
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=login_data)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user(client: TestClient, test_user_data):
    """Test getting current user info with valid token."""
    # Register and login
    client.post("/api/auth/register", json=test_user_data)
    login_response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["name"] == test_user_data["name"]


def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 401


def test_admin_role_required(client: TestClient, test_user_data):
    """Test that admin endpoints require admin role."""
    # Register regular user
    client.post("/api/auth/register", json=test_user_data)
    login_response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    
    # Try to access admin endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/users", headers=headers)
    assert response.status_code == 403
    assert "Insufficient role" in response.json()["detail"]


def test_register_ignores_role_parameter(client: TestClient):
    """Test that public registration ignores any role parameter (security fix for privilege escalation)."""
    # Attempt to register as admin by sending role in request
    malicious_data = {
        "name": "Hacker",
        "email": "hacker@example.com",
        "password": "password123",
        "role": "admin"  # This should be rejected by Pydantic's extra="forbid"
    }
    response = client.post("/api/auth/register", json=malicious_data)
    # Should fail with 422 because extra fields are forbidden
    assert response.status_code == 422


def test_register_without_role_creates_contributor(client: TestClient):
    """Test that registration without role creates CONTRIBUTOR user."""
    user_data = {
        "name": "Regular User",
        "email": "user@example.com",
        "password": "password123"
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "contributor"


def test_admin_can_create_user_with_role(client: TestClient, admin_user):
    """Test that admin can create users with specific roles."""
    headers = {"Authorization": f"Bearer {admin_user['token']}"}
    
    # Create a new admin user
    new_admin_data = {
        "name": "New Admin",
        "email": "newadmin@example.com",
        "password": "adminpass456",
        "role": "admin"
    }
    response = client.post("/api/auth/users", json=new_admin_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "admin"
    assert data["email"] == "newadmin@example.com"


def test_non_admin_cannot_create_user_with_role(client: TestClient, test_user_data):
    """Test that non-admin users cannot access the admin user creation endpoint."""
    # Register and login as regular user
    client.post("/api/auth/register", json=test_user_data)
    login_response = client.post("/api/auth/login", json={
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to create an admin user
    new_admin_data = {
        "name": "Fake Admin",
        "email": "fakeadmin@example.com",
        "password": "password123",
        "role": "admin"
    }
    response = client.post("/api/auth/users", json=new_admin_data, headers=headers)
    assert response.status_code == 403