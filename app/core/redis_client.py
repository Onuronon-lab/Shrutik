"""
Redis Client Configuration

This module provides Redis client configuration and utilities for
job monitoring, caching, and session management.
"""

import logging
from typing import Any, Dict, Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper with connection management."""

    def __init__(self, url: str = None):
        """
        Initialize Redis client.

        Args:
            url: Redis connection URL
        """
        self.url = url or settings.REDIS_URL
        self._client: Optional[redis.Redis] = None

    @property
    def client(self) -> redis.Redis:
        """Get Redis client instance."""
        if self._client is None:
            try:
                self._client = redis.from_url(
                    self.url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )
                # Test connection
                self._client.ping()
                logger.info("Redis client connected successfully")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise

        return self._client

    def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set key-value pair with optional expiration."""
        try:
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key."""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    def lpush(self, key: str, *values) -> Optional[int]:
        """Push values to the left of a list."""
        try:
            return self.client.lpush(key, *values)
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {e}")
            return None

    def lrange(self, key: str, start: int = 0, end: int = -1) -> list:
        """Get range of elements from a list."""
        try:
            return self.client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {e}")
            return []

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to specified range."""
        try:
            return self.client.ltrim(key, start, end)
        except Exception as e:
            logger.error(f"Redis LTRIM error for key {key}: {e}")
            return False

    def llen(self, key: str) -> int:
        """Get length of a list."""
        try:
            return self.client.llen(key)
        except Exception as e:
            logger.error(f"Redis LLEN error for key {key}: {e}")
            return 0

    def expire(self, key: str, time: int) -> bool:
        """Set expiration time for a key."""
        try:
            return self.client.expire(key, time)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash fields."""
        try:
            return self.client.hset(name, mapping=mapping)
        except Exception as e:
            logger.error(f"Redis HSET error for hash {name}: {e}")
            return 0

    def hget(self, name: str, key: str) -> Optional[str]:
        """Get hash field value."""
        try:
            return self.client.hget(name, key)
        except Exception as e:
            logger.error(f"Redis HGET error for hash {name}, key {key}: {e}")
            return None

    def hgetall(self, name: str) -> Dict[str, str]:
        """Get all hash fields and values."""
        try:
            return self.client.hgetall(name)
        except Exception as e:
            logger.error(f"Redis HGETALL error for hash {name}: {e}")
            return {}

    def hdel(self, name: str, *keys) -> int:
        """Delete hash fields."""
        try:
            return self.client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis HDEL error for hash {name}: {e}")
            return 0

    def incr(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment key value."""
        try:
            return self.client.incr(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error for key {key}: {e}")
            return None

    def incrby(self, key: str, amount: int) -> Optional[int]:
        """Increment key value by amount."""
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCRBY error for key {key}: {e}")
            return None

    def decr(self, key: str, amount: int = 1) -> Optional[int]:
        """Decrement key value."""
        try:
            return self.client.decr(key, amount)
        except Exception as e:
            logger.error(f"Redis DECR error for key {key}: {e}")
            return None

    def ping(self) -> bool:
        """Test Redis connection."""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis PING error: {e}")
            return False

    def flushdb(self) -> bool:
        """Flush current database."""
        try:
            return self.client.flushdb()
        except Exception as e:
            logger.error(f"Redis FLUSHDB error: {e}")
            return False

    def close(self):
        """Close Redis connection."""
        if self._client:
            try:
                self._client.close()
                logger.info("Redis client connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._client = None


# Global Redis client instance
redis_client = RedisClient()
