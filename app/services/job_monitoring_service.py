"""
Job Monitoring Service

This service provides comprehensive monitoring and tracking for Celery background jobs,
including status tracking, retry mechanisms, and notification systems.
"""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from celery import current_app
from celery.result import AsyncResult
from celery.states import FAILURE, PENDING, RETRY, REVOKED, SUCCESS
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.redis_client import redis_client
from app.db.database import SessionLocal

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    RETRY = "RETRY"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"


class JobPriority(str, Enum):
    """Job priority levels."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class JobInfo:
    """Information about a background job."""

    task_id: str
    task_name: str
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    queue: str = "default"
    priority: JobPriority = JobPriority.NORMAL
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class JobStatistics:
    """Statistics about job execution."""

    total_jobs: int
    pending_jobs: int
    running_jobs: int
    successful_jobs: int
    failed_jobs: int
    retry_jobs: int
    average_execution_time: float
    success_rate: float
    failure_rate: float


class JobMonitoringService:
    """Service for monitoring and managing background jobs."""

    def __init__(self, redis_client_instance=None):
        """
        Initialize the job monitoring service.

        Args:
            redis_client_instance: Optional Redis client for caching
        """
        self.redis_client = redis_client_instance or redis_client
        self.celery_app = celery_app

    def get_job_info(self, task_id: str) -> Optional[JobInfo]:
        """
        Get detailed information about a specific job.

        Args:
            task_id: Celery task ID

        Returns:
            JobInfo object or None if job not found
        """
        try:
            result = AsyncResult(task_id, app=self.celery_app)

            # Get basic job information
            job_info = JobInfo(
                task_id=task_id,
                task_name=result.name or "unknown",
                status=JobStatus(result.status),
                created_at=datetime.now(
                    timezone.utc
                ),  # Celery doesn't track creation time
                retry_count=getattr(result, "retries", 0),
            )

            # Get additional information based on status
            if result.status == SUCCESS:
                job_info.result = result.result
                job_info.completed_at = datetime.now(timezone.utc)
            elif result.status == FAILURE:
                job_info.error = str(result.info)
                job_info.completed_at = datetime.now(timezone.utc)
            elif result.status in [PENDING, "PROGRESS"]:
                if hasattr(result, "info") and isinstance(result.info, dict):
                    job_info.progress = result.info

            # Try to get additional metadata from result backend
            if hasattr(result, "info") and isinstance(result.info, dict):
                job_info.metadata = result.info.get("metadata", {})

            return job_info

        except Exception as e:
            logger.error(f"Failed to get job info for task {task_id}: {e}")
            return None

    def get_active_jobs(self, queue: Optional[str] = None) -> List[JobInfo]:
        """
        Get information about all active jobs.

        Args:
            queue: Optional queue name to filter by

        Returns:
            List of JobInfo objects for active jobs
        """
        try:
            # Get active tasks from Celery
            inspect = self.celery_app.control.inspect()
            active_tasks = inspect.active()

            if not active_tasks:
                return []

            jobs = []
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    # Filter by queue if specified
                    if (
                        queue
                        and task.get("delivery_info", {}).get("routing_key") != queue
                    ):
                        continue

                    job_info = JobInfo(
                        task_id=task["id"],
                        task_name=task["name"],
                        status=JobStatus.STARTED,
                        created_at=datetime.fromtimestamp(
                            task["time_start"], timezone.utc
                        ),
                        started_at=datetime.fromtimestamp(
                            task["time_start"], timezone.utc
                        ),
                        queue=task.get("delivery_info", {}).get(
                            "routing_key", "default"
                        ),
                        metadata={
                            "worker": worker,
                            "args": task.get("args", []),
                            "kwargs": task.get("kwargs", {}),
                        },
                    )
                    jobs.append(job_info)

            return jobs

        except Exception as e:
            logger.error(f"Failed to get active jobs: {e}")
            return []

    def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """
        Get information about scheduled (pending) jobs.

        Returns:
            List of scheduled job information
        """
        try:
            inspect = self.celery_app.control.inspect()
            scheduled_tasks = inspect.scheduled()

            if not scheduled_tasks:
                return []

            jobs = []
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    jobs.append(
                        {
                            "task_id": task["request"]["id"],
                            "task_name": task["request"]["task"],
                            "eta": task["eta"],
                            "priority": task["request"].get("priority", 0),
                            "worker": worker,
                            "args": task["request"].get("args", []),
                            "kwargs": task["request"].get("kwargs", {}),
                        }
                    )

            return jobs

        except Exception as e:
            logger.error(f"Failed to get scheduled jobs: {e}")
            return []

    def get_job_statistics(self, hours: int = 24) -> JobStatistics:
        """
        Get job execution statistics for the specified time period.

        Args:
            hours: Number of hours to look back for statistics

        Returns:
            JobStatistics object
        """
        try:
            # This is a simplified implementation
            # In a production system, you'd want to store job history in a database

            inspect = self.celery_app.control.inspect()
            stats = inspect.stats()

            if not stats:
                return JobStatistics(
                    total_jobs=0,
                    pending_jobs=0,
                    running_jobs=0,
                    successful_jobs=0,
                    failed_jobs=0,
                    retry_jobs=0,
                    average_execution_time=0.0,
                    success_rate=0.0,
                    failure_rate=0.0,
                )

            # Aggregate statistics from all workers
            total_stats = {"total": 0, "pool": {"max-concurrency": 0}, "rusage": {}}

            for worker, worker_stats in stats.items():
                total_stats["total"] += worker_stats.get("total", {}).get(
                    "tasks.total", 0
                )
                total_stats["pool"]["max-concurrency"] += worker_stats.get(
                    "pool", {}
                ).get("max-concurrency", 0)

            # Get active and scheduled jobs
            active_jobs = self.get_active_jobs()
            scheduled_jobs = self.get_scheduled_jobs()

            return JobStatistics(
                total_jobs=total_stats["total"],
                pending_jobs=len(scheduled_jobs),
                running_jobs=len(active_jobs),
                successful_jobs=0,  # Would need job history database
                failed_jobs=0,  # Would need job history database
                retry_jobs=0,  # Would need job history database
                average_execution_time=0.0,  # Would need job history database
                success_rate=0.0,  # Would need job history database
                failure_rate=0.0,  # Would need job history database
            )

        except Exception as e:
            logger.error(f"Failed to get job statistics: {e}")
            return JobStatistics(
                total_jobs=0,
                pending_jobs=0,
                running_jobs=0,
                successful_jobs=0,
                failed_jobs=0,
                retry_jobs=0,
                average_execution_time=0.0,
                success_rate=0.0,
                failure_rate=0.0,
            )

    def cancel_job(self, task_id: str, terminate: bool = False) -> bool:
        """
        Cancel a running or pending job.

        Args:
            task_id: Celery task ID to cancel
            terminate: Whether to terminate the task forcefully

        Returns:
            True if job was cancelled successfully
        """
        try:
            if terminate:
                self.celery_app.control.revoke(task_id, terminate=True)
            else:
                self.celery_app.control.revoke(task_id)

            logger.info(f"Job {task_id} cancelled (terminate={terminate})")
            return True

        except Exception as e:
            logger.error(f"Failed to cancel job {task_id}: {e}")
            return False

    def retry_job(self, task_id: str, countdown: int = 60) -> Optional[str]:
        """
        Retry a failed job.

        Args:
            task_id: Original task ID
            countdown: Delay before retry in seconds

        Returns:
            New task ID if retry was successful, None otherwise
        """
        try:
            # Get original task result
            result = AsyncResult(task_id, app=self.celery_app)

            if result.status != FAILURE:
                logger.warning(
                    f"Cannot retry job {task_id} with status {result.status}"
                )
                return None

            # Get original task information
            task_name = result.name
            if not task_name:
                logger.error(f"Cannot determine task name for {task_id}")
                return None

            # Get original arguments (this is limited by what Celery stores)
            # In practice, you'd want to store original arguments separately
            logger.warning(
                f"Retrying job {task_id} - original arguments may not be available"
            )

            # For now, we can't easily retry with original arguments
            # This would require storing job metadata separately
            return None

        except Exception as e:
            logger.error(f"Failed to retry job {task_id}: {e}")
            return None

    def get_worker_status(self) -> Dict[str, Any]:
        """
        Get status information about all Celery workers.

        Returns:
            Dictionary with worker status information
        """
        try:
            inspect = self.celery_app.control.inspect()

            # Get various worker information
            stats = inspect.stats() or {}
            active = inspect.active() or {}
            scheduled = inspect.scheduled() or {}
            reserved = inspect.reserved() or {}

            workers = {}

            # Combine information from all sources
            all_workers = set()
            all_workers.update(stats.keys())
            all_workers.update(active.keys())
            all_workers.update(scheduled.keys())
            all_workers.update(reserved.keys())

            for worker in all_workers:
                worker_info = {
                    "name": worker,
                    "status": "online" if worker in stats else "offline",
                    "active_tasks": len(active.get(worker, [])),
                    "scheduled_tasks": len(scheduled.get(worker, [])),
                    "reserved_tasks": len(reserved.get(worker, [])),
                    "stats": stats.get(worker, {}),
                    "queues": [],
                }

                # Extract queue information from stats
                if worker in stats:
                    worker_stats = stats[worker]
                    if "pool" in worker_stats:
                        worker_info["pool_size"] = worker_stats["pool"].get(
                            "max-concurrency", 0
                        )
                        worker_info["pool_processes"] = worker_stats["pool"].get(
                            "processes", []
                        )

                    if "total" in worker_stats:
                        worker_info["total_tasks"] = worker_stats["total"]

                workers[worker] = worker_info

            return {
                "workers": workers,
                "total_workers": len(workers),
                "online_workers": len(
                    [w for w in workers.values() if w["status"] == "online"]
                ),
                "total_active_tasks": sum(w["active_tasks"] for w in workers.values()),
                "total_scheduled_tasks": sum(
                    w["scheduled_tasks"] for w in workers.values()
                ),
            }

        except Exception as e:
            logger.error(f"Failed to get worker status: {e}")
            return {
                "workers": {},
                "total_workers": 0,
                "online_workers": 0,
                "total_active_tasks": 0,
                "total_scheduled_tasks": 0,
                "error": str(e),
            }

    def get_queue_lengths(self) -> Dict[str, int]:
        """
        Get the number of pending tasks in each queue.

        Returns:
            Dictionary mapping queue names to task counts
        """
        try:
            # This requires Redis inspection
            if not self.redis_client:
                logger.warning("Redis client not available for queue length inspection")
                return {}

            # Get queue names from Celery configuration
            queues = self.celery_app.conf.task_routes.values()
            queue_names = set()
            for route in queues:
                if isinstance(route, dict) and "queue" in route:
                    queue_names.add(route["queue"])

            # Add default queues
            queue_names.update(
                [
                    "default",
                    "audio_processing",
                    "consensus",
                    "batch_processing",
                    "maintenance",
                ]
            )

            queue_lengths = {}
            for queue_name in queue_names:
                try:
                    # Redis list length for Celery queue
                    length = self.redis_client.llen(queue_name)
                    queue_lengths[queue_name] = length
                except Exception as e:
                    logger.error(f"Failed to get length for queue {queue_name}: {e}")
                    queue_lengths[queue_name] = -1  # Indicate error

            return queue_lengths

        except Exception as e:
            logger.error(f"Failed to get queue lengths: {e}")
            return {}

    def purge_queue(self, queue_name: str) -> int:
        """
        Purge all tasks from a specific queue.

        Args:
            queue_name: Name of the queue to purge

        Returns:
            Number of tasks purged
        """
        try:
            purged = self.celery_app.control.purge()
            logger.info(f"Purged queue {queue_name}: {purged} tasks removed")
            return purged or 0

        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {e}")
            return 0

    def send_notification(
        self, message: str, level: str = "info", metadata: Optional[Dict] = None
    ):
        """
        Send a notification about job status or system events.

        Args:
            message: Notification message
            level: Notification level (info, warning, error, critical)
            metadata: Additional metadata for the notification
        """
        # This is a placeholder for notification system
        # In production, you might integrate with:
        # - Email notifications
        # - Slack/Discord webhooks
        # - Push notifications
        # - Database logging
        # - External monitoring systems

        notification = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": message,
            "level": level,
            "metadata": metadata or {},
        }

        logger.info(f"Notification [{level.upper()}]: {message}")

        # Store in Redis for recent notifications (optional)
        if self.redis_client:
            try:
                key = "job_notifications"
                self.redis_client.lpush(key, json.dumps(notification))
                self.redis_client.ltrim(key, 0, 99)  # Keep last 100 notifications
                self.redis_client.expire(key, 86400)  # Expire after 24 hours
            except Exception as e:
                logger.error(f"Failed to store notification in Redis: {e}")


# Global instance
job_monitoring_service = JobMonitoringService()
