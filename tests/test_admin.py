import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.models.user import UserRole
from app.schemas.admin import PlatformStatsResponse, SystemHealthResponse


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_admin_user():
    """Mock admin user for testing"""
    user = Mock()
    user.id = 1
    user.name = "Admin User"
    user.email = "admin@example.com"
    user.role = UserRole.ADMIN
    return user


@pytest.fixture
def mock_sworik_user():
    """Mock sworik developer user for testing"""
    user = Mock()
    user.id = 2
    user.name = "Sworik Dev"
    user.email = "dev@sworik.com"
    user.role = UserRole.SWORIK_DEVELOPER
    return user


class TestAdminEndpoints:
    """Test admin API endpoints"""

    @patch('app.core.dependencies.get_current_active_user')
    @patch('app.services.admin_service.AdminService.get_platform_statistics')
    def test_get_platform_statistics_admin(self, mock_get_stats, mock_get_user, client, mock_admin_user):
        """Test platform statistics endpoint with admin user"""
        mock_get_user.return_value = mock_admin_user
        mock_stats = PlatformStatsResponse(
            total_users=100,
            total_contributors=80,
            total_admins=5,
            total_sworik_developers=3,
            total_recordings=500,
            total_chunks=2000,
            total_transcriptions=1500,
            total_validated_transcriptions=1200,
            total_quality_reviews=300,
            avg_recording_duration=120.5,
            avg_transcription_quality=0.85,
            recordings_by_status={"uploaded": 100, "processing": 50, "chunked": 350},
            transcriptions_by_validation_status={"validated": 1200, "unvalidated": 300}
        )
        mock_get_stats.return_value = mock_stats

        response = client.get("/api/admin/stats/platform")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 100
        assert data["total_contributors"] == 80
        assert data["total_recordings"] == 500

    @patch('app.core.dependencies.get_current_active_user')
    @patch('app.services.admin_service.AdminService.get_platform_statistics')
    def test_get_platform_statistics_sworik_dev(self, mock_get_stats, mock_get_user, client, mock_sworik_user):
        """Test platform statistics endpoint with sworik developer user"""
        mock_get_user.return_value = mock_sworik_user
        mock_stats = PlatformStatsResponse(
            total_users=100,
            total_contributors=80,
            total_admins=5,
            total_sworik_developers=3,
            total_recordings=500,
            total_chunks=2000,
            total_transcriptions=1500,
            total_validated_transcriptions=1200,
            total_quality_reviews=300,
            recordings_by_status={"uploaded": 100, "processing": 50, "chunked": 350},
            transcriptions_by_validation_status={"validated": 1200, "unvalidated": 300}
        )
        mock_get_stats.return_value = mock_stats

        response = client.get("/api/admin/stats/platform")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == 100

    @patch('app.core.dependencies.get_current_active_user')
    @patch('app.services.admin_service.AdminService.get_system_health')
    def test_get_system_health(self, mock_get_health, mock_get_user, client, mock_admin_user):
        """Test system health endpoint"""
        mock_get_user.return_value = mock_admin_user
        mock_health = SystemHealthResponse(
            database_status="healthy",
            active_users_last_24h=25,
            active_users_last_7d=150,
            processing_queue_size=5,
            failed_recordings_count=2
        )
        mock_get_health.return_value = mock_health

        response = client.get("/api/admin/system/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["database_status"] == "healthy"
        assert data["active_users_last_24h"] == 25
        assert data["processing_queue_size"] == 5

    @patch('app.core.dependencies.get_current_active_user')
    def test_get_users_for_management_admin_only(self, mock_get_user, client, mock_admin_user):
        """Test that user management endpoint requires admin role"""
        mock_get_user.return_value = mock_admin_user
        
        # Mock the database query to avoid actual DB calls
        with patch('app.services.admin_service.AdminService.get_users_for_management') as mock_get_users:
            mock_get_users.return_value = []
            
            response = client.get("/api/admin/users")
            assert response.status_code == 200

    def test_admin_endpoints_require_authentication(self, client):
        """Test that admin endpoints require authentication"""
        # Test without authentication
        response = client.get("/api/admin/stats/platform")
        assert response.status_code == 403  # Should be forbidden without auth

        response = client.get("/api/admin/users")
        assert response.status_code == 403

        response = client.get("/api/admin/system/health")
        assert response.status_code == 403

    @patch('app.core.dependencies.get_current_active_user')
    @patch('app.services.admin_service.AdminService.get_usage_analytics')
    def test_get_usage_analytics(self, mock_get_analytics, mock_get_user, client, mock_admin_user):
        """Test usage analytics endpoint"""
        mock_get_user.return_value = mock_admin_user
        mock_analytics = {
            "daily_recordings": [{"date": "2024-01-01", "count": 10}],
            "daily_transcriptions": [{"date": "2024-01-01", "count": 25}],
            "user_activity_by_role": {"contributor": 50, "admin": 2},
            "popular_script_durations": {"2_minutes": 100, "5_minutes": 75},
            "transcription_quality_trend": [],
            "top_contributors": [{"user_id": 1, "name": "Top User", "contribution_count": 100}]
        }
        mock_get_analytics.return_value = mock_analytics

        response = client.get("/api/admin/analytics/usage?days=30")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["daily_recordings"]) == 1
        assert data["user_activity_by_role"]["contributor"] == 50

    @patch('app.core.dependencies.get_current_active_user')
    @patch('app.services.admin_service.AdminService.update_user_role')
    def test_update_user_role(self, mock_update_role, mock_get_user, client, mock_admin_user):
        """Test updating user role"""
        mock_get_user.return_value = mock_admin_user
        
        updated_user = Mock()
        updated_user.id = 5
        updated_user.name = "Test User"
        updated_user.email = "test@example.com"
        updated_user.role = UserRole.ADMIN
        mock_update_role.return_value = updated_user

        response = client.put("/api/admin/users/5/role", json={"role": "admin"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    @patch('app.core.dependencies.get_current_active_user')
    @patch('app.services.admin_service.AdminService.create_quality_review')
    def test_create_quality_review(self, mock_create_review, mock_get_user, client, mock_admin_user):
        """Test creating quality review"""
        mock_get_user.return_value = mock_admin_user
        
        mock_review = Mock()
        mock_review.id = 1
        mock_create_review.return_value = mock_review

        response = client.post("/api/admin/quality-reviews/1", json={
            "decision": "approved",
            "rating": 4.5,
            "comment": "Good transcription"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "review_id" in data
        assert data["message"] == "Quality review created successfully"