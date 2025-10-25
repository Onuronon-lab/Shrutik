def test_root_endpoint(client):
    """Test the root endpoint returns correct message"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Voice Data Collection Platform API"}


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}