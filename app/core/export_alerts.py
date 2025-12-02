"""
Export Alerting Module

This module provides alerting functionality for export operations, consensus calculations,
and R2 usage. It checks metrics against thresholds and generates alerts when issues are detected.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.export_metrics import consensus_metrics_collector, r2_metrics_collector
from app.core.redis_client import redis_client
from app.models.audio_chunk import AudioChunk

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Alert information."""

    severity: AlertSeverity
    title: str
    message: str
    component: str
    timestamp: datetime
    metrics: Optional[Dict[str, Any]] = None
    action_required: Optional[str] = None


class ExportAlerting:
    """Alerting system for export operations."""

    # Alert thresholds
    CONSECUTIVE_FAILURES_THRESHOLD = 3
    EXPORT_BACKLOG_THRESHOLD = 500
    CONSENSUS_FAILURE_RATE_THRESHOLD = 10.0  # 10%
    R2_USAGE_WARNING_THRESHOLD = 80.0  # 80%
    R2_USAGE_CRITICAL_THRESHOLD = 95.0  # 95%

    def __init__(self, db: Session):
        self.db = db
        self.alerts: List[Alert] = []

    def check_all_alerts(self) -> List[Alert]:
        """
        Check all alert conditions and return list of active alerts.

        Returns:
            List of Alert objects for conditions that need attention
        """
        self.alerts = []

        # Check export batch failures
        self._check_export_batch_failures()

        # Check R2 usage
        self._check_r2_usage()

        # Check consensus failure rate
        self._check_consensus_failure_rate()

        # Check export backlog
        self._check_export_backlog()

        # Log and store alerts
        for alert in self.alerts:
            self._log_alert(alert)
            self._store_alert(alert)

        return self.alerts

    def _check_export_batch_failures(self):
        """Check for consecutive export batch failures."""
        try:
            consecutive_failures = int(
                redis_client.get("metrics:export:consecutive_failures") or 0
            )

            if consecutive_failures >= self.CONSECUTIVE_FAILURES_THRESHOLD:
                # Get last failure info
                last_failed_at = redis_client.get("metrics:export:last_batch_failed_at")
                last_error = redis_client.get("metrics:export:last_failure_error")

                if isinstance(last_failed_at, bytes):
                    last_failed_at = last_failed_at.decode()
                if isinstance(last_error, bytes):
                    last_error = last_error.decode()

                alert = Alert(
                    severity=AlertSeverity.CRITICAL,
                    title="Consecutive Export Batch Failures",
                    message=f"{consecutive_failures} consecutive export batch failures detected",
                    component="export_batch",
                    timestamp=datetime.now(timezone.utc),
                    metrics={
                        "consecutive_failures": consecutive_failures,
                        "last_failed_at": last_failed_at,
                        "last_error": last_error,
                    },
                    action_required="Investigate export batch creation process and resolve underlying issues",
                )
                self.alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking export batch failures: {e}")

    def _check_r2_usage(self):
        """Check R2 usage against free tier limits."""
        try:
            if settings.EXPORT_STORAGE_TYPE != "r2":
                return  # Skip if not using R2

            metrics = r2_metrics_collector.get_r2_metrics()

            # Check Class A operations
            if metrics.class_a_usage_percent >= self.R2_USAGE_CRITICAL_THRESHOLD:
                alert = Alert(
                    severity=AlertSeverity.CRITICAL,
                    title="R2 Class A Operations Critical",
                    message=f"R2 Class A operations at {metrics.class_a_usage_percent:.1f}% of free tier limit",
                    component="r2_storage",
                    timestamp=datetime.now(timezone.utc),
                    metrics={
                        "class_a_operations": metrics.class_a_operations_this_month,
                        "class_a_limit": metrics.class_a_limit,
                        "usage_percent": metrics.class_a_usage_percent,
                    },
                    action_required="Stop creating new export batches or upgrade to paid R2 plan",
                )
                self.alerts.append(alert)
            elif metrics.class_a_usage_percent >= self.R2_USAGE_WARNING_THRESHOLD:
                alert = Alert(
                    severity=AlertSeverity.WARNING,
                    title="R2 Class A Operations Warning",
                    message=f"R2 Class A operations at {metrics.class_a_usage_percent:.1f}% of free tier limit",
                    component="r2_storage",
                    timestamp=datetime.now(timezone.utc),
                    metrics={
                        "class_a_operations": metrics.class_a_operations_this_month,
                        "class_a_limit": metrics.class_a_limit,
                        "usage_percent": metrics.class_a_usage_percent,
                    },
                    action_required="Monitor usage and plan for potential limit increase",
                )
                self.alerts.append(alert)

            # Check Class B operations
            if metrics.class_b_usage_percent >= self.R2_USAGE_CRITICAL_THRESHOLD:
                alert = Alert(
                    severity=AlertSeverity.CRITICAL,
                    title="R2 Class B Operations Critical",
                    message=f"R2 Class B operations at {metrics.class_b_usage_percent:.1f}% of free tier limit",
                    component="r2_storage",
                    timestamp=datetime.now(timezone.utc),
                    metrics={
                        "class_b_operations": metrics.class_b_operations_this_month,
                        "class_b_limit": metrics.class_b_limit,
                        "usage_percent": metrics.class_b_usage_percent,
                    },
                    action_required="Limit downloads or upgrade to paid R2 plan",
                )
                self.alerts.append(alert)
            elif metrics.class_b_usage_percent >= self.R2_USAGE_WARNING_THRESHOLD:
                alert = Alert(
                    severity=AlertSeverity.WARNING,
                    title="R2 Class B Operations Warning",
                    message=f"R2 Class B operations at {metrics.class_b_usage_percent:.1f}% of free tier limit",
                    component="r2_storage",
                    timestamp=datetime.now(timezone.utc),
                    metrics={
                        "class_b_operations": metrics.class_b_operations_this_month,
                        "class_b_limit": metrics.class_b_limit,
                        "usage_percent": metrics.class_b_usage_percent,
                    },
                    action_required="Monitor download patterns and consider usage optimization",
                )
                self.alerts.append(alert)

            # Check storage usage
            if metrics.storage_usage_percent >= self.R2_USAGE_CRITICAL_THRESHOLD:
                alert = Alert(
                    severity=AlertSeverity.CRITICAL,
                    title="R2 Storage Critical",
                    message=f"R2 storage at {metrics.storage_usage_percent:.1f}% of free tier limit",
                    component="r2_storage",
                    timestamp=datetime.now(timezone.utc),
                    metrics={
                        "storage_used_gb": metrics.storage_used_gb,
                        "storage_limit_gb": metrics.storage_limit_gb,
                        "usage_percent": metrics.storage_usage_percent,
                    },
                    action_required="Delete old export batches or upgrade to paid R2 plan",
                )
                self.alerts.append(alert)
            elif metrics.storage_usage_percent >= self.R2_USAGE_WARNING_THRESHOLD:
                alert = Alert(
                    severity=AlertSeverity.WARNING,
                    title="R2 Storage Warning",
                    message=f"R2 storage at {metrics.storage_usage_percent:.1f}% of free tier limit",
                    component="r2_storage",
                    timestamp=datetime.now(timezone.utc),
                    metrics={
                        "storage_used_gb": metrics.storage_used_gb,
                        "storage_limit_gb": metrics.storage_limit_gb,
                        "usage_percent": metrics.storage_usage_percent,
                    },
                    action_required="Plan for storage cleanup or capacity increase",
                )
                self.alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking R2 usage: {e}")

    def _check_consensus_failure_rate(self):
        """Check consensus calculation failure rate."""
        try:
            metrics = consensus_metrics_collector.get_consensus_metrics()

            # Calculate failure rate
            if metrics.total_calculations > 0:
                failure_rate = metrics.total_failed / metrics.total_calculations * 100

                if failure_rate > self.CONSENSUS_FAILURE_RATE_THRESHOLD:
                    alert = Alert(
                        severity=AlertSeverity.ERROR,
                        title="High Consensus Failure Rate",
                        message=f"Consensus failure rate at {failure_rate:.1f}% (threshold: {self.CONSENSUS_FAILURE_RATE_THRESHOLD}%)",
                        component="consensus",
                        timestamp=datetime.now(timezone.utc),
                        metrics={
                            "total_calculations": metrics.total_calculations,
                            "total_failed": metrics.total_failed,
                            "failure_rate": round(failure_rate, 2),
                        },
                        action_required="Investigate consensus calculation failures and review chunk quality",
                    )
                    self.alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking consensus failure rate: {e}")

    def _check_export_backlog(self):
        """Check export backlog (chunks ready for export)."""
        try:
            # Count chunks ready for export
            ready_chunks_count = (
                self.db.query(func.count(AudioChunk.id))
                .filter(AudioChunk.ready_for_export == True)
                .scalar()
                or 0
            )

            if ready_chunks_count > self.EXPORT_BACKLOG_THRESHOLD:
                alert = Alert(
                    severity=AlertSeverity.WARNING,
                    title="High Export Backlog",
                    message=f"{ready_chunks_count} chunks ready for export (threshold: {self.EXPORT_BACKLOG_THRESHOLD})",
                    component="export_batch",
                    timestamp=datetime.now(timezone.utc),
                    metrics={
                        "ready_chunks_count": ready_chunks_count,
                        "threshold": self.EXPORT_BACKLOG_THRESHOLD,
                    },
                    action_required="Trigger manual export batch creation or investigate export scheduling",
                )
                self.alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking export backlog: {e}")

    def _log_alert(self, alert: Alert):
        """Log alert with appropriate severity."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL,
        }[alert.severity]

        logger.log(
            log_level,
            f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}",
            extra={
                "alert_severity": alert.severity.value,
                "alert_title": alert.title,
                "alert_component": alert.component,
                "alert_metrics": alert.metrics,
                "action_required": alert.action_required,
            },
        )

    def _store_alert(self, alert: Alert):
        """Store alert in Redis for external monitoring."""
        try:
            alert_key = f"alert:export:{int(alert.timestamp.timestamp())}"
            alert_data = {
                "severity": alert.severity.value,
                "title": alert.title,
                "message": alert.message,
                "component": alert.component,
                "timestamp": alert.timestamp.isoformat(),
                "action_required": alert.action_required or "",
            }

            if alert.metrics:
                alert_data["metrics"] = str(alert.metrics)

            redis_client.hset(alert_key, alert_data)
            redis_client.expire(alert_key, 604800)  # Keep for 7 days

            # Add to alerts list
            redis_client.lpush("export_alerts", alert_key)
            redis_client.ltrim("export_alerts", 0, 999)  # Keep last 1000 alerts

        except Exception as e:
            logger.error(f"Failed to store alert in Redis: {e}")

    def get_recent_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of recent alerts
        """
        try:
            alert_keys = redis_client.lrange("export_alerts", 0, limit - 1)
            alerts = []

            for key in alert_keys:
                if isinstance(key, bytes):
                    key = key.decode()
                alert_data = redis_client.hgetall(key)
                if alert_data:
                    # Convert bytes to strings
                    alert_dict = {}
                    for k, v in alert_data.items():
                        k_str = k.decode() if isinstance(k, bytes) else k
                        v_str = v.decode() if isinstance(v, bytes) else v
                        alert_dict[k_str] = v_str
                    alerts.append(alert_dict)

            return alerts

        except Exception as e:
            logger.error(f"Failed to get recent alerts: {e}")
            return []


def check_export_alerts(db: Session) -> List[Alert]:
    """
    Convenience function to check all export alerts.

    Args:
        db: Database session

    Returns:
        List of active alerts
    """
    alerting = ExportAlerting(db)
    return alerting.check_all_alerts()
