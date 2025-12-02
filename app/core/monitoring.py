"""
Monitoring and alerting utilities for the Voice Data Collection Platform.

This module provides monitoring capabilities, health checks, and alerting
mechanisms for critical system failures and performance issues.
"""

import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil
from sqlalchemy import text

from app.core.redis_client import redis_client
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """System performance metrics."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    active_connections: int
    redis_connected: bool
    database_connected: bool
    celery_workers: int
    queue_size: int
    error_rate: float
    response_time_avg: float


@dataclass
class Alert:
    """System alert information."""

    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    component: str
    metrics: Optional[Dict[str, Any]] = None
    resolved: bool = False


class HealthChecker:
    """System health monitoring and alerting."""

    def __init__(self):
        self.alerts: List[Alert] = []
        self.metrics_history: List[SystemMetrics] = []
        self.max_history_size = 1000
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "error_rate": 5.0,  # 5% error rate
            "response_time_avg": 5000.0,  # 5 seconds
            "queue_size": 1000,
        }

    async def collect_system_metrics(self) -> SystemMetrics:
        """
        Collect current system metrics.

        Returns:
            SystemMetrics object with current system state
        """
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Database connection check
            db_connected = await self._check_database_connection()

            # Redis connection check
            redis_connected = await self._check_redis_connection()

            # Celery metrics
            celery_workers, queue_size = await self._get_celery_metrics()

            # Application metrics
            error_rate = await self._get_error_rate()
            response_time_avg = await self._get_average_response_time()

            metrics = SystemMetrics(
                timestamp=datetime.now(timezone.utc),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                active_connections=len(psutil.net_connections()),
                redis_connected=redis_connected,
                database_connected=db_connected,
                celery_workers=celery_workers,
                queue_size=queue_size,
                error_rate=error_rate,
                response_time_avg=response_time_avg,
            )

            # Store metrics
            self.metrics_history.append(metrics)
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)

            # Store in Redis for external monitoring
            await self._store_metrics_in_redis(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}", exc_info=True)
            raise

    async def _check_database_connection(self) -> bool:
        """Check database connectivity."""
        try:
            db = SessionLocal()
            try:
                db.execute(text("SELECT 1"))
                return True
            finally:
                db.close()
        except Exception as e:
            logger.warning(f"Database connection check failed: {e}")
            return False

    async def _check_redis_connection(self) -> bool:
        """Check Redis connectivity."""
        try:
            return redis_client.client.ping()
        except Exception as e:
            logger.warning(f"Redis connection check failed: {e}")
            return False

    async def _get_celery_metrics(self) -> tuple[int, int]:
        """Get Celery worker and queue metrics."""
        try:
            from app.core.celery_app import celery_app

            # Get active workers
            inspect = celery_app.control.inspect()
            active_workers = inspect.active()
            worker_count = len(active_workers) if active_workers else 0

            # Get queue size (approximate)
            queue_size = 0
            try:
                queue_info = redis_client.llen("celery")
                queue_size = queue_info if queue_info else 0
            except Exception:
                pass

            return worker_count, queue_size

        except Exception as e:
            logger.warning(f"Failed to get Celery metrics: {e}")
            return 0, 0

    async def _get_error_rate(self) -> float:
        """Calculate error rate from recent logs."""
        try:
            # Get error count from Redis (stored by error tracking middleware)
            error_count_key = "error_count:last_hour"
            total_count_key = "request_count:last_hour"

            error_count = redis_client.get(error_count_key) or "0"
            total_count = redis_client.get(total_count_key) or "0"

            # Convert to int safely
            error_count = (
                int(error_count) if isinstance(error_count, (str, bytes)) else 0
            )
            total_count = (
                int(total_count) if isinstance(total_count, (str, bytes)) else 0
            )

            if total_count > 0:
                return (float(error_count) / float(total_count)) * 100
            return 0.0

        except Exception as e:
            logger.warning(f"Failed to calculate error rate: {e}")
            return 0.0

    async def _get_average_response_time(self) -> float:
        """Get average response time from recent requests."""
        try:
            # Get response time data from Redis
            response_times_key = "response_times:last_hour"
            response_times = redis_client.lrange(response_times_key, 0, -1)

            if response_times:
                times = [float(t) for t in response_times]
                return sum(times) / len(times)
            return 0.0

        except Exception as e:
            logger.warning(f"Failed to calculate average response time: {e}")
            return 0.0

    async def _store_metrics_in_redis(self, metrics: SystemMetrics):
        """Store metrics in Redis for external monitoring."""
        try:
            metrics_key = f"system_metrics:{int(metrics.timestamp.timestamp())}"
            # Convert metrics to Redis-compatible format
            metrics_dict = asdict(metrics)
            metrics_dict["timestamp"] = (
                metrics.timestamp.isoformat()
            )  # Convert datetime to string
            redis_client.hset(metrics_key, metrics_dict)
            redis_client.expire(metrics_key, 86400)  # Keep for 24 hours
        except Exception as e:
            logger.warning(f"Failed to store metrics in Redis: {e}")

    async def check_thresholds(self, metrics: SystemMetrics) -> List[Alert]:
        """
        Check metrics against thresholds and generate alerts.

        Args:
            metrics: Current system metrics

        Returns:
            List of alerts generated
        """
        alerts = []

        # CPU threshold check
        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append(
                Alert(
                    level=(
                        AlertLevel.WARNING
                        if metrics.cpu_percent < 95
                        else AlertLevel.CRITICAL
                    ),
                    title="High CPU Usage",
                    message=f"CPU usage is {metrics.cpu_percent:.1f}%",
                    timestamp=metrics.timestamp,
                    component="system",
                    metrics={"cpu_percent": metrics.cpu_percent},
                )
            )

        # Memory threshold check
        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append(
                Alert(
                    level=(
                        AlertLevel.WARNING
                        if metrics.memory_percent < 95
                        else AlertLevel.CRITICAL
                    ),
                    title="High Memory Usage",
                    message=f"Memory usage is {metrics.memory_percent:.1f}%",
                    timestamp=metrics.timestamp,
                    component="system",
                    metrics={"memory_percent": metrics.memory_percent},
                )
            )

        # Disk threshold check
        if metrics.disk_percent > self.alert_thresholds["disk_percent"]:
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    title="High Disk Usage",
                    message=f"Disk usage is {metrics.disk_percent:.1f}%",
                    timestamp=metrics.timestamp,
                    component="system",
                    metrics={"disk_percent": metrics.disk_percent},
                )
            )

        # Database connection check
        if not metrics.database_connected:
            alerts.append(
                Alert(
                    level=AlertLevel.CRITICAL,
                    title="Database Connection Failed",
                    message="Cannot connect to the database",
                    timestamp=metrics.timestamp,
                    component="database",
                )
            )

        # Redis connection check
        if not metrics.redis_connected:
            alerts.append(
                Alert(
                    level=AlertLevel.ERROR,
                    title="Redis Connection Failed",
                    message="Cannot connect to Redis",
                    timestamp=metrics.timestamp,
                    component="redis",
                )
            )

        # Celery workers check
        if metrics.celery_workers == 0:
            alerts.append(
                Alert(
                    level=AlertLevel.ERROR,
                    title="No Celery Workers",
                    message="No active Celery workers found",
                    timestamp=metrics.timestamp,
                    component="celery",
                )
            )

        # Queue size check
        if metrics.queue_size > self.alert_thresholds["queue_size"]:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    title="High Queue Size",
                    message=f"Celery queue has {metrics.queue_size} pending tasks",
                    timestamp=metrics.timestamp,
                    component="celery",
                    metrics={"queue_size": metrics.queue_size},
                )
            )

        # Error rate check
        if metrics.error_rate > self.alert_thresholds["error_rate"]:
            alerts.append(
                Alert(
                    level=AlertLevel.ERROR,
                    title="High Error Rate",
                    message=f"Error rate is {metrics.error_rate:.1f}%",
                    timestamp=metrics.timestamp,
                    component="application",
                    metrics={"error_rate": metrics.error_rate},
                )
            )

        # Response time check
        if metrics.response_time_avg > self.alert_thresholds["response_time_avg"]:
            alerts.append(
                Alert(
                    level=AlertLevel.WARNING,
                    title="High Response Time",
                    message=f"Average response time is {metrics.response_time_avg:.0f}ms",
                    timestamp=metrics.timestamp,
                    component="application",
                    metrics={"response_time_avg": metrics.response_time_avg},
                )
            )

        # Store alerts
        for alert in alerts:
            self.alerts.append(alert)
            await self._send_alert(alert)

        return alerts

    async def _send_alert(self, alert: Alert):
        """
        Send alert notification.

        Args:
            alert: Alert to send
        """
        try:
            # Log the alert
            log_level = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.ERROR: logging.ERROR,
                AlertLevel.CRITICAL: logging.CRITICAL,
            }[alert.level]

            logger.log(
                log_level,
                f"ALERT [{alert.level.value.upper()}] {alert.title}: {alert.message}",
                extra={
                    "alert_level": alert.level.value,
                    "alert_title": alert.title,
                    "alert_component": alert.component,
                    "alert_metrics": alert.metrics,
                },
            )

            # Store alert in Redis for external monitoring
            alert_key = f"alert:{int(alert.timestamp.timestamp())}"
            alert_data = {
                "level": alert.level.value,
                "title": alert.title,
                "message": alert.message,
                "component": alert.component,
                "timestamp": alert.timestamp.isoformat(),
            }
            if alert.metrics:
                alert_data["metrics"] = str(alert.metrics)

            redis_client.hset(alert_key, alert_data)
            redis_client.expire(alert_key, 604800)  # Keep for 7 days

            # Add to alerts list in Redis
            redis_client.lpush("system_alerts", alert_key)
            redis_client.ltrim("system_alerts", 0, 999)  # Keep last 1000 alerts

        except Exception as e:
            logger.error(f"Failed to send alert: {e}", exc_info=True)

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall system health status.

        Returns:
            Dictionary with health status information
        """
        try:
            metrics = await self.collect_system_metrics()
            alerts = await self.check_thresholds(metrics)

            # Get application-specific metrics
            app_metrics = await self._get_application_metrics()

            # Determine overall health
            critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
            error_alerts = [a for a in alerts if a.level == AlertLevel.ERROR]
            warning_alerts = [a for a in alerts if a.level == AlertLevel.WARNING]

            if critical_alerts:
                overall_status = "critical"
            elif error_alerts:
                overall_status = "error"
            elif warning_alerts:
                overall_status = "warning"
            else:
                overall_status = "healthy"

            return {
                "status": overall_status,
                "timestamp": metrics.timestamp.isoformat(),
                "metrics": asdict(metrics),
                "alerts": {
                    "critical": len(critical_alerts),
                    "error": len(error_alerts),
                    "warning": len(warning_alerts),
                    "total": len(alerts),
                },
                "components": {
                    "database": "healthy" if metrics.database_connected else "error",
                    "redis": "healthy" if metrics.redis_connected else "error",
                    "celery": "healthy" if metrics.celery_workers > 0 else "error",
                },
                # Add application-specific metrics for admin dashboard
                "active_users_last_24h": app_metrics.get("active_users_24h", 0),
                "active_users_last_7d": app_metrics.get("active_users_7d", 0),
                "processing_queue_size": metrics.queue_size,
                "failed_recordings_count": app_metrics.get("failed_recordings", 0),
                "database_status": "healthy" if metrics.database_connected else "error",
                "avg_response_time": metrics.response_time_avg,
            }

        except Exception as e:
            logger.error(f"Failed to get health status: {e}", exc_info=True)
            return {
                "status": "error",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "active_users_last_24h": 0,
                "active_users_last_7d": 0,
                "processing_queue_size": 0,
                "failed_recordings_count": 0,
                "database_status": "error",
                "avg_response_time": 0,
            }

    async def _get_application_metrics(self) -> Dict[str, Any]:
        """
        Get application-specific metrics for the admin dashboard.

        Returns:
            Dictionary with application metrics
        """
        try:
            from app.db.database import SessionLocal

            db = SessionLocal()
            try:
                from datetime import datetime, timedelta, timezone

                from sqlalchemy import func

                from app.models.transcription import Transcription
                from app.models.user import User
                from app.models.voice_recording import RecordingStatus, VoiceRecording

                # Calculate time thresholds
                now = datetime.now(timezone.utc)
                last_24h = now - timedelta(hours=24)
                last_7d = now - timedelta(days=7)

                # Active users based on recent recordings (last 24h)
                active_24h = (
                    db.query(func.count(func.distinct(VoiceRecording.user_id)))
                    .filter(VoiceRecording.created_at >= last_24h)
                    .scalar()
                    or 0
                )

                # Active users based on recent recordings (last 7d)
                active_7d = (
                    db.query(func.count(func.distinct(VoiceRecording.user_id)))
                    .filter(VoiceRecording.created_at >= last_7d)
                    .scalar()
                    or 0
                )

                # Also check transcription activity
                transcription_active_24h = (
                    db.query(func.count(func.distinct(Transcription.user_id)))
                    .filter(Transcription.created_at >= last_24h)
                    .scalar()
                    or 0
                )

                transcription_active_7d = (
                    db.query(func.count(func.distinct(Transcription.user_id)))
                    .filter(Transcription.created_at >= last_7d)
                    .scalar()
                    or 0
                )

                # Combine recording and transcription activity
                active_24h = max(active_24h, transcription_active_24h)
                active_7d = max(active_7d, transcription_active_7d)

                # Failed recordings count
                failed_recordings = (
                    db.query(VoiceRecording)
                    .filter(VoiceRecording.status == RecordingStatus.FAILED)
                    .count()
                )

                # Total users for context
                total_users = db.query(User).count()

                return {
                    "active_users_24h": active_24h,
                    "active_users_7d": active_7d,
                    "failed_recordings": failed_recordings,
                    "total_users": total_users,
                }

            finally:
                db.close()

        except Exception as e:
            logger.warning(f"Failed to get application metrics: {e}")
            return {
                "active_users_24h": 0,
                "active_users_7d": 0,
                "failed_recordings": 0,
                "total_users": 0,
            }

    async def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts
        """
        try:
            alert_keys = redis_client.lrange("system_alerts", 0, limit - 1)
            alerts = []

            for key in alert_keys:
                alert_data = redis_client.hgetall(key)
                if alert_data:
                    alerts.append(alert_data)

            return alerts

        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}", exc_info=True)
            return []


# Global health checker instance
health_checker = HealthChecker()


# Monitoring middleware
class MonitoringMiddleware:
    """Middleware for tracking request metrics and errors."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        request_count_key = "request_count:last_hour"

        # Increment request counter
        try:
            redis_client.incr(request_count_key)
            redis_client.expire(request_count_key, 3600)  # 1 hour
        except Exception:
            pass

        # Track response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                response_time = (time.time() - start_time) * 1000  # Convert to ms
                status_code = message["status"]

                # Track response time
                try:
                    response_times_key = "response_times:last_hour"
                    redis_client.lpush(response_times_key, response_time)
                    redis_client.ltrim(response_times_key, 0, 999)  # Keep last 1000
                    redis_client.expire(response_times_key, 3600)  # 1 hour
                except Exception:
                    pass

                # Track errors
                if status_code >= 400:
                    try:
                        error_count_key = "error_count:last_hour"
                        redis_client.incr(error_count_key)
                        redis_client.expire(error_count_key, 3600)  # 1 hour
                    except Exception:
                        pass

            await send(message)

        await self.app(scope, receive, send_wrapper)


# Utility functions
async def run_health_check() -> Dict[str, Any]:
    """Run a complete health check and return status."""
    return await health_checker.get_health_status()


async def get_system_metrics() -> SystemMetrics:
    """Get current system metrics."""
    return await health_checker.collect_system_metrics()


async def check_critical_systems() -> bool:
    """
    Check if all critical systems are operational.

    Returns:
        True if all critical systems are healthy, False otherwise
    """
    try:
        metrics = await health_checker.collect_system_metrics()
        return (
            metrics.database_connected
            and metrics.redis_connected
            and metrics.cpu_percent < 95
            and metrics.memory_percent < 95
            and metrics.disk_percent < 95
        )
    except Exception as e:
        logger.error(f"Failed to check critical systems: {e}", exc_info=True)
        return False
