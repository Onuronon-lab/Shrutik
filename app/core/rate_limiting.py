"""
Rate Limiting and Request Throttling

This module provides rate limiting functionality to prevent abuse and ensure
fair usage of API endpoints. Uses Redis for distributed rate limiting.
"""

import logging
import time
from typing import Dict, Optional, Tuple

from fastapi import Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter using sliding window algorithm."""

    def __init__(self, redis_client=redis_client):
        self.redis = redis_client

    def is_allowed(
        self, key: str, limit: int, window: int
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed based on rate limit.

        Args:
            key: Unique identifier for the rate limit (e.g., user_id, ip_address)
            limit: Maximum number of requests allowed
            window: Time window in seconds

        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window

            # Use Redis pipeline for atomic operations
            pipe = self.redis.client.pipeline()

            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests in window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration for cleanup
            pipe.expire(key, window + 1)

            results = pipe.execute()
            current_count = results[1]

            # Check if limit exceeded
            is_allowed = current_count < limit

            if not is_allowed:
                # Remove the request we just added since it's not allowed
                self.redis.client.zrem(key, str(current_time))

            # Calculate reset time
            reset_time = current_time + window
            remaining = max(0, limit - current_count - (1 if is_allowed else 0))

            rate_limit_info = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "retry_after": window if not is_allowed else 0,
            }

            return is_allowed, rate_limit_info

        except Exception as e:
            logger.error(f"Rate limiting error for key {key}: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {
                "limit": limit,
                "remaining": limit - 1,
                "reset": int(time.time()) + window,
                "retry_after": 0,
            }

    def reset_limit(self, key: str) -> bool:
        """Reset rate limit for a key."""
        try:
            return self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error resetting rate limit for key {key}: {e}")
            return False


# Global rate limiter instance
rate_limiter = RateLimiter()


class RateLimitConfig:
    """Rate limit configuration for different endpoints and user types."""

    # Default rate limits (requests per minute)
    DEFAULT_LIMITS = {
        "anonymous": 60,  # 60 requests per minute for anonymous users
        "authenticated": 300,  # 300 requests per minute for authenticated users
        "admin": 1000,  # 1000 requests per minute for admins
        "sworik_developer": 2000,  # 2000 requests per minute for Sworik developers
    }

    # Endpoint-specific rate limits (requests per minute)
    ENDPOINT_LIMITS = {
        "/api/auth/login": 10,  # Login attempts
        "/api/auth/register": 5,  # Registration attempts
        "/api/recordings/upload": 20,  # File uploads
        "/api/transcriptions/submit": 100,  # Transcription submissions
        "/api/export/dataset": 5,  # Data exports (very limited)
    }

    # Burst limits for specific operations (requests per second)
    BURST_LIMITS = {
        "/api/chunks/*/audio": 10,  # Audio file serving
        "/api/transcriptions/tasks": 5,  # Task requests
    }

    @classmethod
    def get_user_limit(cls, user_role: Optional[str] = None) -> int:
        """Get rate limit for user based on role."""
        if not user_role:
            return cls.DEFAULT_LIMITS["anonymous"]
        return cls.DEFAULT_LIMITS.get(user_role, cls.DEFAULT_LIMITS["authenticated"])

    @classmethod
    def get_endpoint_limit(cls, endpoint: str) -> Optional[int]:
        """Get specific rate limit for endpoint."""
        # Check exact match first
        if endpoint in cls.ENDPOINT_LIMITS:
            return cls.ENDPOINT_LIMITS[endpoint]

        # Check pattern matches
        for pattern, limit in cls.ENDPOINT_LIMITS.items():
            if "*" in pattern:
                pattern_parts = pattern.split("*")
                if len(pattern_parts) == 2:
                    prefix, suffix = pattern_parts
                    if endpoint.startswith(prefix) and endpoint.endswith(suffix):
                        return limit

        return None

    @classmethod
    def get_burst_limit(cls, endpoint: str) -> Optional[int]:
        """Get burst rate limit for endpoint."""
        return cls.BURST_LIMITS.get(endpoint)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for applying rate limits to requests."""

    def __init__(self, app, rate_limiter: RateLimiter = rate_limiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.config = RateLimitConfig()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Apply rate limiting to incoming requests."""
        try:
            # Skip rate limiting for health checks and static files
            if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
                return await call_next(request)

            # Get user information from request
            user = getattr(request.state, "user", None)
            user_id = user.id if user else None
            user_role = user.role if user else None

            # Generate rate limit key
            if user_id:
                rate_key = f"rate_limit:user:{user_id}"
            else:
                # Use IP address for anonymous users
                client_ip = self._get_client_ip(request)
                rate_key = f"rate_limit:ip:{client_ip}"

            # Determine rate limits
            endpoint = request.url.path
            request.method

            # Check endpoint-specific limits first
            endpoint_limit = self.config.get_endpoint_limit(endpoint)
            if endpoint_limit:
                endpoint_key = f"{rate_key}:endpoint:{endpoint}"
                is_allowed, rate_info = self.rate_limiter.is_allowed(
                    endpoint_key, endpoint_limit, 60  # 1 minute window
                )

                if not is_allowed:
                    return self._create_rate_limit_response(
                        rate_info, "Endpoint rate limit exceeded"
                    )

            # Check burst limits for high-frequency endpoints
            burst_limit = self.config.get_burst_limit(endpoint)
            if burst_limit:
                burst_key = f"{rate_key}:burst:{endpoint}"
                is_allowed, rate_info = self.rate_limiter.is_allowed(
                    burst_key, burst_limit, 1  # 1 second window
                )

                if not is_allowed:
                    return self._create_rate_limit_response(
                        rate_info, "Burst rate limit exceeded"
                    )

            # Apply general user rate limits
            user_limit = self.config.get_user_limit(user_role)
            general_key = f"{rate_key}:general"
            is_allowed, rate_info = self.rate_limiter.is_allowed(
                general_key, user_limit, 60  # 1 minute window
            )

            if not is_allowed:
                return self._create_rate_limit_response(
                    rate_info, "Rate limit exceeded"
                )

            # Process request
            response = await call_next(request)

            # Add rate limit headers to response
            response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(rate_info["reset"])

            return response

        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # Fail open - continue with request if middleware fails
            return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for forwarded headers first (for load balancers/proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"

    def _create_rate_limit_response(
        self, rate_info: Dict[str, int], message: str
    ) -> Response:
        """Create rate limit exceeded response."""
        headers = {
            "X-RateLimit-Limit": str(rate_info["limit"]),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(rate_info["reset"]),
            "Retry-After": str(rate_info["retry_after"]),
        }

        return Response(
            content=f'{{"detail": "{message}", "retry_after": {rate_info["retry_after"]}}}',
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers,
            media_type="application/json",
        )


def rate_limit(limit: int, window: int = 60, key_func: Optional[callable] = None):
    """
    Decorator for applying rate limits to specific endpoints.

    Args:
        limit: Maximum number of requests allowed
        window: Time window in seconds (default: 60)
        key_func: Custom function to generate rate limit key
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented for specific use cases
            # For now, rely on middleware for general rate limiting
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class RateLimitManager:
    """Manager for rate limit operations and monitoring."""

    def __init__(self, rate_limiter: RateLimiter = rate_limiter):
        self.rate_limiter = rate_limiter

    def get_user_rate_limit_status(self, user_id: int) -> Dict[str, any]:
        """Get current rate limit status for a user."""
        try:
            rate_key = f"rate_limit:user:{user_id}:general"

            # Get current count in window
            current_time = int(time.time())
            window_start = current_time - 60  # 1 minute window

            current_count = self.rate_limiter.redis.client.zcount(
                rate_key, window_start, current_time
            )

            return {
                "user_id": user_id,
                "current_requests": current_count,
                "window_start": window_start,
                "window_end": current_time,
            }

        except Exception as e:
            logger.error(f"Error getting rate limit status for user {user_id}: {e}")
            return {"error": str(e)}

    def reset_user_rate_limit(self, user_id: int) -> bool:
        """Reset rate limits for a specific user."""
        try:
            pattern = f"rate_limit:user:{user_id}:*"
            keys = self.rate_limiter.redis.client.keys(pattern)

            if keys:
                return bool(self.rate_limiter.redis.client.delete(*keys))
            return True

        except Exception as e:
            logger.error(f"Error resetting rate limit for user {user_id}: {e}")
            return False

    def get_rate_limit_statistics(self) -> Dict[str, any]:
        """Get overall rate limiting statistics."""
        try:
            # Get all rate limit keys
            all_keys = self.rate_limiter.redis.client.keys("rate_limit:*")

            stats = {
                "total_rate_limited_entities": len(all_keys),
                "user_limits": 0,
                "ip_limits": 0,
                "endpoint_limits": 0,
                "burst_limits": 0,
            }

            for key in all_keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                if ":user:" in key_str:
                    stats["user_limits"] += 1
                elif ":ip:" in key_str:
                    stats["ip_limits"] += 1
                elif ":endpoint:" in key_str:
                    stats["endpoint_limits"] += 1
                elif ":burst:" in key_str:
                    stats["burst_limits"] += 1

            return stats

        except Exception as e:
            logger.error(f"Error getting rate limit statistics: {e}")
            return {"error": str(e)}


# Global rate limit manager instance
rate_limit_manager = RateLimitManager()
