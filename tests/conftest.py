import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing the app
os.environ["DATABASE_URL"] = "sqlite:///test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"
os.environ["USE_CELERY"] = "false"
os.environ["ENABLE_CACHING"] = "false"
os.environ["DEBUG"] = "true"

# Import app after environment variables are set
from app.main import app
from app.db.database import Base, get_db


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine and tables"""
    engine = create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Clean up - drop all tables after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_engine):
    """Create a database session for testing"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    """Create a test client for the FastAPI app with mocked dependencies"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock Redis and other external services
    with patch('app.core.redis_client.RedisClient') as mock_redis_class:
        mock_redis_instance = Mock()
        mock_redis_instance.ping.return_value = True
        mock_redis_instance.get.return_value = None
        mock_redis_instance.set.return_value = True
        mock_redis_instance.incr.return_value = 1
        mock_redis_instance.expire.return_value = True
        mock_redis_instance.lpush.return_value = 1
        mock_redis_instance.ltrim.return_value = True
        mock_redis_instance.lrange.return_value = []
        mock_redis_instance.hset.return_value = True
        mock_redis_instance.hgetall.return_value = {}
        mock_redis_instance.llen.return_value = 0
        mock_redis_class.return_value = mock_redis_instance
        
        with patch('app.core.cache.cache_manager') as mock_cache:
            mock_cache.redis = mock_redis_instance
            
            with patch('app.db.database.get_connection_pool_status') as mock_pool_status:
                mock_pool_status.return_value = {
                    "pool_size": 20,
                    "checked_in": 15,
                    "pool_status": "healthy"
                }
                
                with TestClient(app) as test_client:
                    yield test_client
    
    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def mock_db():
    """Mock database session for testing"""
    with patch('app.db.database.get_db') as mock_get_db:
        mock_session = Mock()
        mock_get_db.return_value = mock_session
        yield mock_session