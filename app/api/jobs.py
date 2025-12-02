"""
Job Management API

This module provides REST API endpoints for monitoring and managing
background jobs, including status tracking, retry mechanisms, and worker monitoring.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user, require_admin
from app.models.user import User
from app.services.job_monitoring_service import (
    JobPriority,
    JobStatus,
    job_monitoring_service,
)
from app.services.notification_service import notification_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


class JobInfoResponse(BaseModel):
    """Response model for job information."""

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


class JobStatisticsResponse(BaseModel):
    """Response model for job statistics."""

    total_jobs: int
    pending_jobs: int
    running_jobs: int
    successful_jobs: int
    failed_jobs: int
    retry_jobs: int
    average_execution_time: float
    success_rate: float
    failure_rate: float


class WorkerStatusResponse(BaseModel):
    """Response model for worker status."""

    workers: Dict[str, Any]
    total_workers: int
    online_workers: int
    total_active_tasks: int
    total_scheduled_tasks: int


class JobActionRequest(BaseModel):
    """Request model for job actions."""

    action: str = Field(..., description="Action to perform: cancel, retry, terminate")
    countdown: Optional[int] = Field(
        60, description="Delay in seconds for retry action"
    )


class QueuePurgeRequest(BaseModel):
    """Request model for queue purge action."""

    queue_name: str = Field(..., description="Name of the queue to purge")
    confirm: bool = Field(False, description="Confirmation flag for destructive action")


@router.get("/info/{task_id}", response_model=JobInfoResponse)
async def get_job_info(
    task_id: str, current_user: User = Depends(get_current_user)
) -> JobInfoResponse:
    """
    Get detailed information about a specific job.

    Args:
        task_id: Celery task ID
        current_user: Current authenticated user

    Returns:
        Detailed job information
    """
    job_info = job_monitoring_service.get_job_info(task_id)

    if not job_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Job {task_id} not found"
        )

    return JobInfoResponse(**job_info.__dict__)


@router.get("/active", response_model=List[JobInfoResponse])
async def get_active_jobs(
    queue: Optional[str] = Query(None, description="Filter by queue name"),
    current_user: User = Depends(get_current_user),
) -> List[JobInfoResponse]:
    """
    Get information about all active (running) jobs.

    Args:
        queue: Optional queue name to filter by
        current_user: Current authenticated user

    Returns:
        List of active job information
    """
    jobs = job_monitoring_service.get_active_jobs(queue=queue)
    return [JobInfoResponse(**job.__dict__) for job in jobs]


@router.get("/scheduled")
async def get_scheduled_jobs(
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get information about scheduled (pending) jobs.

    Args:
        current_user: Current authenticated user

    Returns:
        List of scheduled job information
    """
    return job_monitoring_service.get_scheduled_jobs()


@router.get("/statistics", response_model=JobStatisticsResponse)
async def get_job_statistics(
    hours: int = Query(
        24, ge=1, le=168, description="Hours to look back for statistics"
    ),
    current_user: User = Depends(get_current_user),
) -> JobStatisticsResponse:
    """
    Get job execution statistics for the specified time period.

    Args:
        hours: Number of hours to look back (1-168)
        current_user: Current authenticated user

    Returns:
        Job execution statistics
    """
    stats = job_monitoring_service.get_job_statistics(hours=hours)
    return JobStatisticsResponse(**stats.__dict__)


@router.get("/workers", response_model=WorkerStatusResponse)
async def get_worker_status(
    current_user: User = Depends(require_admin),
) -> WorkerStatusResponse:
    """
    Get status information about all Celery workers.

    Requires admin privileges.

    Args:
        current_user: Current authenticated admin user

    Returns:
        Worker status information
    """
    worker_status = job_monitoring_service.get_worker_status()
    return WorkerStatusResponse(**worker_status)


@router.get("/queues")
async def get_queue_lengths(
    current_user: User = Depends(require_admin),
) -> Dict[str, int]:
    """
    Get the number of pending tasks in each queue.

    Requires admin privileges.

    Args:
        current_user: Current authenticated admin user

    Returns:
        Dictionary mapping queue names to task counts
    """
    return job_monitoring_service.get_queue_lengths()


@router.post("/action/{task_id}")
async def perform_job_action(
    task_id: str,
    action_request: JobActionRequest,
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Perform an action on a specific job.

    Requires admin privileges.

    Args:
        task_id: Celery task ID
        action_request: Action to perform
        current_user: Current authenticated admin user

    Returns:
        Action result
    """
    action = action_request.action.lower()

    if action == "cancel":
        success = job_monitoring_service.cancel_job(task_id, terminate=False)
        return {
            "action": "cancel",
            "task_id": task_id,
            "success": success,
            "message": "Job cancelled" if success else "Failed to cancel job",
        }

    elif action == "terminate":
        success = job_monitoring_service.cancel_job(task_id, terminate=True)
        return {
            "action": "terminate",
            "task_id": task_id,
            "success": success,
            "message": "Job terminated" if success else "Failed to terminate job",
        }

    elif action == "retry":
        new_task_id = job_monitoring_service.retry_job(
            task_id, countdown=action_request.countdown
        )
        return {
            "action": "retry",
            "original_task_id": task_id,
            "new_task_id": new_task_id,
            "success": new_task_id is not None,
            "message": (
                f"Job retried with ID {new_task_id}"
                if new_task_id
                else "Failed to retry job"
            ),
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown action: {action}. Supported actions: cancel, terminate, retry",
        )


@router.post("/queue/purge")
async def purge_queue(
    purge_request: QueuePurgeRequest, current_user: User = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Purge all tasks from a specific queue.

    This is a destructive operation that requires confirmation.
    Requires admin privileges.

    Args:
        purge_request: Queue purge request
        current_user: Current authenticated admin user

    Returns:
        Purge operation result
    """
    if not purge_request.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Queue purge requires confirmation. Set 'confirm' to true.",
        )

    purged_count = job_monitoring_service.purge_queue(purge_request.queue_name)

    return {
        "action": "purge_queue",
        "queue_name": purge_request.queue_name,
        "tasks_purged": purged_count,
        "success": purged_count >= 0,
        "message": f"Purged {purged_count} tasks from queue {purge_request.queue_name}",
    }


@router.get("/notifications")
async def get_user_notifications(
    limit: int = Query(
        50, ge=1, le=100, description="Maximum number of notifications to return"
    ),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    current_user: User = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """
    Get job notifications for the current user.

    Args:
        limit: Maximum number of notifications to return
        unread_only: Whether to return only unread notifications
        current_user: Current authenticated user

    Returns:
        List of user notifications
    """
    return notification_service.get_user_notifications(
        user_id=current_user.id, limit=limit, unread_only=unread_only
    )


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str, current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Mark a notification as read.

    Args:
        notification_id: Notification ID to mark as read
        current_user: Current authenticated user

    Returns:
        Operation result
    """
    success = notification_service.mark_notification_read(
        notification_id, current_user.id
    )

    return {
        "notification_id": notification_id,
        "success": success,
        "message": (
            "Notification marked as read"
            if success
            else "Failed to mark notification as read"
        ),
    }


@router.get("/notifications/system")
async def get_system_notifications(
    limit: int = Query(
        100, ge=1, le=200, description="Maximum number of notifications to return"
    ),
    current_user: User = Depends(require_admin),
) -> List[Dict[str, Any]]:
    """
    Get system-wide notifications.

    Requires admin privileges.

    Args:
        limit: Maximum number of notifications to return
        current_user: Current authenticated admin user

    Returns:
        List of system notifications
    """
    return notification_service.get_system_notifications(limit=limit)


@router.post("/system/restart-workers")
async def restart_workers(
    current_user: User = Depends(require_admin),
) -> Dict[str, Any]:
    """
    Restart all Celery workers.

    This is a system-level operation that requires admin privileges.

    Args:
        current_user: Current authenticated admin user

    Returns:
        Restart operation result
    """
    try:
        # Send restart signal to all workers
        from app.core.celery_app import celery_app

        celery_app.control.broadcast("pool_restart", arguments={"reload": True})

        return {
            "action": "restart_workers",
            "success": True,
            "message": "Worker restart signal sent",
        }
    except Exception as e:
        return {
            "action": "restart_workers",
            "success": False,
            "message": f"Failed to restart workers: {str(e)}",
        }


@router.post("/system/enable-events")
async def enable_events(current_user: User = Depends(require_admin)) -> Dict[str, Any]:
    """
    Enable Celery event monitoring.

    Args:
        current_user: Current authenticated admin user

    Returns:
        Operation result
    """
    try:
        from app.core.celery_app import celery_app

        celery_app.control.enable_events()

        return {
            "action": "enable_events",
            "success": True,
            "message": "Celery events enabled",
        }
    except Exception as e:
        return {
            "action": "enable_events",
            "success": False,
            "message": f"Failed to enable events: {str(e)}",
        }


@router.post("/system/disable-events")
async def disable_events(current_user: User = Depends(require_admin)) -> Dict[str, Any]:
    """
    Disable Celery event monitoring.

    Args:
        current_user: Current authenticated admin user

    Returns:
        Operation result
    """
    try:
        from app.core.celery_app import celery_app

        celery_app.control.disable_events()

        return {
            "action": "disable_events",
            "success": True,
            "message": "Celery events disabled",
        }
    except Exception as e:
        return {
            "action": "disable_events",
            "success": False,
            "message": f"Failed to disable events: {str(e)}",
        }
