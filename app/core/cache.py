"""
Caching Infrastructure

This module provides caching utilities for frequently accessed data and API responses.
Implements Redis-based caching with TTL support and cache invalidation strategies.
"""

import hashlib
import json
import logging
import pickle
from functools import wraps
from typing import Any, Callable, Dict, Optional

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


class CacheManager:
    """Centralized cache management with Redis backend."""

    def __init__(self, redis_client=redis_client):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour default TTL

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from prefix and arguments."""
        key_parts = [prefix]

        # Add positional arguments
        for arg in args:
            if isinstance(arg, (dict, list)):
                key_parts.append(
                    hashlib.md5(json.dumps(arg, sort_keys=True).encode()).hexdigest()
                )
            else:
                key_parts.append(str(arg))

        # Add keyword arguments
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = json.dumps(sorted_kwargs, sort_keys=True)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest())

        return ":".join(key_parts)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with automatic deserialization."""
        try:
            cached_data = self.redis.get(key)
            if cached_data is None:
                return None

            # Try to deserialize as JSON first, then pickle
            try:
                return json.loads(cached_data)
            except (json.JSONDecodeError, TypeError):
                try:
                    return pickle.loads(cached_data.encode("latin1"))
                except (pickle.PickleError, AttributeError):
                    return cached_data

        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with automatic serialization."""
        try:
            ttl = ttl or self.default_ttl

            # Try JSON serialization first, then pickle
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                try:
                    serialized_value = pickle.dumps(value).decode("latin1")
                except pickle.PickleError:
                    serialized_value = str(value)

            return self.redis.set(key, serialized_value, ex=ttl)

        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return self.redis.delete(key)
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        try:
            keys = self.redis.client.keys(pattern)
            if keys:
                return self.redis.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache DELETE_PATTERN error for pattern {pattern}: {e}")
            return 0

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        return self.redis.exists(key)

    def increment(
        self, key: str, amount: int = 1, ttl: Optional[int] = None
    ) -> Optional[int]:
        """Increment counter with optional TTL."""
        try:
            result = self.redis.incr(key, amount)
            if ttl and result == amount:  # First time setting
                self.redis.expire(key, ttl)
            return result
        except Exception as e:
            logger.error(f"Cache INCREMENT error for key {key}: {e}")
            return None


# Global cache manager instance
cache_manager = CacheManager()


def cache_result(
    prefix: str, ttl: Optional[int] = None, key_func: Optional[Callable] = None
):
    """
    Decorator for caching function results.

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Custom function to generate cache key from arguments
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cached_result

            # Execute function and cache result
            logger.debug(f"Cache MISS for key: {cache_key}")
            result = await func(*args, **kwargs)

            if result is not None:
                cache_manager.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = cache_manager._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cached_result

            # Execute function and cache result
            logger.debug(f"Cache MISS for key: {cache_key}")
            result = func(*args, **kwargs)

            if result is not None:
                cache_manager.set(cache_key, result, ttl)

            return result

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class APIResponseCache:
    """Specialized cache for API responses with request-based invalidation."""

    def __init__(self, cache_manager: CacheManager = cache_manager):
        self.cache = cache_manager
        self.api_cache_ttl = 300  # 5 minutes for API responses

    def get_response_key(
        self, endpoint: str, user_id: Optional[int] = None, **params
    ) -> str:
        """Generate cache key for API response."""
        key_parts = ["api_response", endpoint]

        if user_id:
            key_parts.append(f"user_{user_id}")

        if params:
            param_hash = hashlib.md5(
                json.dumps(params, sort_keys=True).encode()
            ).hexdigest()
            key_parts.append(param_hash)

        return ":".join(key_parts)

    def cache_response(
        self,
        endpoint: str,
        response_data: Any,
        user_id: Optional[int] = None,
        ttl: Optional[int] = None,
        **params,
    ) -> bool:
        """Cache API response."""
        cache_key = self.get_response_key(endpoint, user_id, **params)
        return self.cache.set(cache_key, response_data, ttl or self.api_cache_ttl)

    def get_cached_response(
        self, endpoint: str, user_id: Optional[int] = None, **params
    ) -> Optional[Any]:
        """Get cached API response."""
        cache_key = self.get_response_key(endpoint, user_id, **params)
        return self.cache.get(cache_key)

    def invalidate_endpoint(self, endpoint: str, user_id: Optional[int] = None) -> int:
        """Invalidate all cached responses for an endpoint."""
        if user_id:
            pattern = f"api_response:{endpoint}:user_{user_id}:*"
        else:
            pattern = f"api_response:{endpoint}:*"

        return self.cache.delete_pattern(pattern)

    def invalidate_user_cache(self, user_id: int) -> int:
        """Invalidate all cached responses for a user."""
        pattern = f"api_response:*:user_{user_id}:*"
        return self.cache.delete_pattern(pattern)


# Global API response cache instance
api_cache = APIResponseCache()


class DatabaseQueryCache:
    """Specialized cache for database query results."""

    def __init__(self, cache_manager: CacheManager = cache_manager):
        self.cache = cache_manager
        self.query_cache_ttl = 1800  # 30 minutes for query results

    def cache_query_result(
        self, query_key: str, result: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache database query result."""
        cache_key = f"db_query:{query_key}"
        return self.cache.set(cache_key, result, ttl or self.query_cache_ttl)

    def get_cached_query(self, query_key: str) -> Optional[Any]:
        """Get cached database query result."""
        cache_key = f"db_query:{query_key}"
        return self.cache.get(cache_key)

    def invalidate_table_cache(self, table_name: str) -> int:
        """Invalidate all cached queries for a table."""
        pattern = f"db_query:*{table_name}*"
        return self.cache.delete_pattern(pattern)

    def generate_query_key(
        self,
        table: str,
        filters: Dict = None,
        order_by: str = None,
        limit: int = None,
        offset: int = None,
    ) -> str:
        """Generate standardized query cache key."""
        key_parts = [table]

        if filters:
            filter_hash = hashlib.md5(
                json.dumps(filters, sort_keys=True).encode()
            ).hexdigest()
            key_parts.append(f"filters_{filter_hash}")

        if order_by:
            key_parts.append(f"order_{order_by}")

        if limit:
            key_parts.append(f"limit_{limit}")

        if offset:
            key_parts.append(f"offset_{offset}")

        return ":".join(key_parts)


# Global database query cache instance
db_cache = DatabaseQueryCache()


class StatisticsCache:
    """Specialized cache for statistics and aggregated data."""

    def __init__(self, cache_manager: CacheManager = cache_manager):
        self.cache = cache_manager
        self.stats_cache_ttl = 900  # 15 minutes for statistics

    def cache_statistics(
        self, stat_type: str, data: Any, ttl: Optional[int] = None
    ) -> bool:
        """Cache statistics data."""
        cache_key = f"stats:{stat_type}"
        return self.cache.set(cache_key, data, ttl or self.stats_cache_ttl)

    def get_cached_statistics(self, stat_type: str) -> Optional[Any]:
        """Get cached statistics data."""
        cache_key = f"stats:{stat_type}"
        return self.cache.get(cache_key)

    def invalidate_statistics(self, stat_type: str = None) -> int:
        """Invalidate statistics cache."""
        if stat_type:
            return self.cache.delete(f"stats:{stat_type}")
        else:
            return self.cache.delete_pattern("stats:*")


# Global statistics cache instance
stats_cache = StatisticsCache()


def invalidate_related_caches(table_name: str, user_id: Optional[int] = None):
    """
    Invalidate related caches when data changes.

    Args:
        table_name: Name of the table that was modified
        user_id: User ID if the change affects user-specific data
    """
    try:
        # Invalidate database query cache for the table
        db_cache.invalidate_table_cache(table_name)

        # Invalidate statistics cache
        stats_cache.invalidate_statistics()

        # Invalidate user-specific API cache if user_id provided
        if user_id:
            api_cache.invalidate_user_cache(user_id)

        # Invalidate specific endpoint caches based on table
        endpoint_mappings = {
            "voice_recordings": ["recordings", "admin/recordings"],
            "audio_chunks": ["chunks", "transcriptions/tasks"],
            "transcriptions": ["transcriptions", "admin/transcriptions"],
            "scripts": ["scripts"],
            "users": ["admin/users"],
        }

        if table_name in endpoint_mappings:
            for endpoint in endpoint_mappings[table_name]:
                api_cache.invalidate_endpoint(endpoint)

        logger.info(f"Invalidated caches for table: {table_name}, user: {user_id}")

    except Exception as e:
        logger.error(f"Error invalidating caches for table {table_name}: {e}")
