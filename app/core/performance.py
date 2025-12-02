"""
Performance Monitoring and Optimization

This module provides performance monitoring, metrics collection, and optimization
utilities for the Voice Data Collection Platform.
"""

import logging
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

import psutil

from app.core.cache import cache_manager
from app.core.redis_client import redis_client
from app.db.database import get_connection_pool_status

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Collector for performance metrics."""

    def __init__(self, redis_client=redis_client):
        self.redis = redis_client
        self.metrics_ttl = 86400  # 24 hours

    def record_request_time(
        self, endpoint: str, method: str, duration: float, status_code: int
    ):
        """Record request processing time."""
        try:
            timestamp = int(time.time())
            metric_key = f"metrics:request_time:{endpoint}:{method}"

            # Store individual request time
            self.redis.lpush(metric_key, f"{timestamp}:{duration}:{status_code}")

            # Keep only last 1000 requests per endpoint
            self.redis.ltrim(metric_key, 0, 999)
            self.redis.expire(metric_key, self.metrics_ttl)

            # Update aggregated metrics
            self._update_aggregated_metrics(endpoint, method, duration, status_code)

        except Exception as e:
            logger.error(f"Error recording request time: {e}")

    def _update_aggregated_metrics(
        self, endpoint: str, method: str, duration: float, status_code: int
    ):
        """Update aggregated performance metrics."""
        try:
            # Daily aggregates
            today = datetime.now().strftime("%Y-%m-%d")
            agg_key = f"metrics:daily:{today}:{endpoint}:{method}"

            # Increment request count
            self.redis.incr(f"{agg_key}:count")

            # Track response times
            self.redis.lpush(f"{agg_key}:times", str(duration))
            self.redis.ltrim(f"{agg_key}:times", 0, 999)

            # Track status codes
            self.redis.incr(f"{agg_key}:status:{status_code}")

            # Set expiration
            self.redis.expire(f"{agg_key}:count", self.metrics_ttl)
            self.redis.expire(f"{agg_key}:times", self.metrics_ttl)
            self.redis.expire(f"{agg_key}:status:{status_code}", self.metrics_ttl)

        except Exception as e:
            logger.error(f"Error updating aggregated metrics: {e}")

    def get_endpoint_metrics(
        self, endpoint: str, method: str, days: int = 1
    ) -> Dict[str, Any]:
        """Get performance metrics for an endpoint."""
        try:
            metrics = {"endpoint": endpoint, "method": method, "daily_stats": []}

            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                agg_key = f"metrics:daily:{date}:{endpoint}:{method}"

                # Get request count
                count = self.redis.get(f"{agg_key}:count")
                count = int(count) if count else 0

                # Get response times
                times = self.redis.lrange(f"{agg_key}:times", 0, -1)
                times = [float(t) for t in times if t]

                # Calculate statistics
                if times:
                    avg_time = sum(times) / len(times)
                    min_time = min(times)
                    max_time = max(times)
                    p95_time = (
                        sorted(times)[int(len(times) * 0.95)]
                        if len(times) > 20
                        else max_time
                    )
                else:
                    avg_time = min_time = max_time = p95_time = 0

                # Get status code distribution
                status_codes = {}
                for code in [200, 201, 400, 401, 403, 404, 422, 429, 500]:
                    count_key = f"{agg_key}:status:{code}"
                    status_count = self.redis.get(count_key)
                    if status_count:
                        status_codes[str(code)] = int(status_count)

                daily_stat = {
                    "date": date,
                    "request_count": count,
                    "avg_response_time": round(avg_time, 3),
                    "min_response_time": round(min_time, 3),
                    "max_response_time": round(max_time, 3),
                    "p95_response_time": round(p95_time, 3),
                    "status_codes": status_codes,
                }

                metrics["daily_stats"].append(daily_stat)

            return metrics

        except Exception as e:
            logger.error(f"Error getting endpoint metrics: {e}")
            return {"error": str(e)}

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Memory metrics
            memory = psutil.virtual_memory()

            # Disk metrics
            disk = psutil.disk_usage("/")

            # Database connection pool
            db_pool = get_connection_pool_status()

            # Redis metrics
            redis_info = self._get_redis_metrics()

            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "core_count": cpu_count,
                    "load_average": (
                        list(psutil.getloadavg())
                        if hasattr(psutil, "getloadavg")
                        else None
                    ),
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "usage_percent": memory.percent,
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "usage_percent": (disk.used / disk.total) * 100,
                },
                "database": db_pool,
                "redis": redis_info,
            }

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {"error": str(e)}

    def _get_redis_metrics(self) -> Dict[str, Any]:
        """Get Redis performance metrics."""
        try:
            info = self.redis.client.info()
            return {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
            }
        except Exception as e:
            logger.error(f"Error getting Redis metrics: {e}")
            return {"error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate."""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0


class PerformanceMonitor:
    """Performance monitoring decorator and context manager."""

    def __init__(self, metrics: PerformanceMetrics = None):
        self.metrics = metrics or PerformanceMetrics()

    def monitor_endpoint(self, endpoint: str = None):
        """Decorator to monitor endpoint performance."""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                status_code = 200

                try:
                    # Extract endpoint and method from request if available
                    request = None
                    for arg in args:
                        if hasattr(arg, "method") and hasattr(arg, "url"):
                            request = arg
                            break

                    endpoint_name = endpoint or (
                        request.url.path if request else func.__name__
                    )
                    method = request.method if request else "GET"

                    result = await func(*args, **kwargs)

                    # Extract status code from response if available
                    if hasattr(result, "status_code"):
                        status_code = result.status_code

                    return result

                except Exception as e:
                    status_code = 500
                    raise

                finally:
                    duration = time.time() - start_time
                    self.metrics.record_request_time(
                        endpoint_name, method, duration, status_code
                    )

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                status_code = 200

                try:
                    result = func(*args, **kwargs)
                    return result

                except Exception as e:
                    status_code = 500
                    raise

                finally:
                    duration = time.time() - start_time
                    endpoint_name = endpoint or func.__name__
                    self.metrics.record_request_time(
                        endpoint_name, "SYNC", duration, status_code
                    )

            # Return appropriate wrapper
            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    @contextmanager
    def measure_time(self, operation_name: str):
        """Context manager to measure operation time."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            logger.info(f"Operation '{operation_name}' took {duration:.3f} seconds")

            # Store in cache for monitoring
            cache_key = f"perf:operation:{operation_name}"
            cache_manager.set(cache_key, duration, 3600)


class QueryOptimizer:
    """Database query optimization utilities."""

    def __init__(self):
        self.slow_query_threshold = 1.0  # 1 second
        self.query_cache_ttl = 300  # 5 minutes

    def monitor_query(self, query_name: str):
        """Decorator to monitor database query performance."""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    result = await func(*args, **kwargs)
                    return result

                finally:
                    duration = time.time() - start_time

                    if duration > self.slow_query_threshold:
                        logger.warning(
                            f"Slow query detected: {query_name} took {duration:.3f} seconds"
                        )

                    # Record query performance
                    cache_key = f"query_perf:{query_name}"
                    cache_manager.set(cache_key, duration, self.query_cache_ttl)

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)
                    return result

                finally:
                    duration = time.time() - start_time

                    if duration > self.slow_query_threshold:
                        logger.warning(
                            f"Slow query detected: {query_name} took {duration:.3f} seconds"
                        )

                    # Record query performance
                    cache_key = f"query_perf:{query_name}"
                    cache_manager.set(cache_key, duration, self.query_cache_ttl)

            # Return appropriate wrapper
            import asyncio

            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper

        return decorator

    def get_query_performance_report(self) -> Dict[str, Any]:
        """Get performance report for monitored queries."""
        try:
            # Get all query performance keys
            pattern = "query_perf:*"
            keys = cache_manager.redis.client.keys(pattern)

            report = {
                "total_queries": len(keys),
                "slow_queries": [],
                "average_times": {},
            }

            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                query_name = key_str.replace("query_perf:", "")

                duration = cache_manager.get(key_str)
                if duration:
                    report["average_times"][query_name] = duration

                    if duration > self.slow_query_threshold:
                        report["slow_queries"].append(
                            {"query": query_name, "duration": duration}
                        )

            return report

        except Exception as e:
            logger.error(f"Error generating query performance report: {e}")
            return {"error": str(e)}


class PerformanceOptimizer:
    """Automatic performance optimization utilities."""

    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.monitor = PerformanceMonitor(self.metrics)
        self.query_optimizer = QueryOptimizer()

    def optimize_cache_settings(self) -> Dict[str, Any]:
        """Analyze and optimize cache settings based on usage patterns."""
        try:
            # Get Redis metrics
            redis_metrics = self.metrics._get_redis_metrics()
            hit_rate = redis_metrics.get("hit_rate", 0)

            recommendations = []

            # Analyze hit rate
            if hit_rate < 70:
                recommendations.append(
                    {
                        "type": "cache_ttl",
                        "message": "Low cache hit rate detected. Consider increasing TTL for frequently accessed data.",
                        "current_hit_rate": hit_rate,
                    }
                )

            # Check memory usage
            used_memory = redis_metrics.get("used_memory", 0)
            if used_memory > 1024 * 1024 * 1024:  # 1GB
                recommendations.append(
                    {
                        "type": "memory_usage",
                        "message": "High Redis memory usage. Consider implementing cache eviction policies.",
                        "used_memory_mb": used_memory / (1024 * 1024),
                    }
                )

            return {
                "current_metrics": redis_metrics,
                "recommendations": recommendations,
            }

        except Exception as e:
            logger.error(f"Error optimizing cache settings: {e}")
            return {"error": str(e)}

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive performance dashboard data."""
        try:
            return {
                "system_metrics": self.metrics.get_system_metrics(),
                "cache_optimization": self.optimize_cache_settings(),
                "query_performance": self.query_optimizer.get_query_performance_report(),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating performance dashboard: {e}")
            return {"error": str(e)}


# Global instances
performance_metrics = PerformanceMetrics()
performance_monitor = PerformanceMonitor(performance_metrics)
query_optimizer = QueryOptimizer()
performance_optimizer = PerformanceOptimizer()
