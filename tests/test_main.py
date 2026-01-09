from unittest.mock import patch, Mock


def test_root_endpoint(client):
    """Test the root endpoint returns correct message"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Shrutik (শ্রুতিক) - Voice Data Collection Platform API"
    assert data["description"] == "Empowering communities through voice technology"
    assert data["version"] == "1.0.0"


def test_health_check(client):
    """Test the health check endpoint"""
    # Mock the entire health check function to return a simple healthy status
    with patch('app.main.run_health_check') as mock_health_check:
        mock_health_check.return_value = {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",
            "database_status": "healthy",
            "active_users_last_24h": 25,
            "active_users_last_7d": 150,
            "processing_queue_size": 5,
            "failed_recordings_count": 2,
        }
        
        # Also mock the connection pool status and cache manager
        with patch('app.main.get_connection_pool_status') as mock_pool_status, \
             patch('app.main.cache_manager') as mock_cache_manager:
            
            mock_pool_status.return_value = {
                "pool_size": 20,
                "checked_in": 15,
                "pool_status": "healthy"
            }
            
            mock_redis = Mock()
            mock_redis.ping.return_value = True
            mock_cache_manager.redis = mock_redis
            
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
