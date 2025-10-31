from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.database import get_db
from app.core.dependencies import require_admin, require_admin_or_sworik, get_current_active_user
from app.models.user import User, UserRole
from app.models.quality_review import ReviewDecision
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService
from app.schemas.admin import (
    PlatformStatsResponse, UserStatsResponse, UserManagementResponse,
    RoleUpdateRequest, QualityReviewItemResponse, FlaggedTranscriptionResponse,
    UsageAnalyticsResponse, QualityReviewUpdateRequest
)
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats/platform", response_model=PlatformStatsResponse)
async def get_platform_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get comprehensive platform statistics."""
    admin_service = AdminService(db)
    return admin_service.get_platform_statistics()


@router.get("/stats/users", response_model=List[UserStatsResponse])
async def get_user_statistics(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get detailed user statistics."""
    admin_service = AdminService(db)
    return admin_service.get_user_statistics(limit=limit)


@router.get("/users", response_model=List[UserManagementResponse])
async def get_users_for_management(
    role: Optional[UserRole] = Query(None, description="Filter users by role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get users for management interface (admin only)."""
    admin_service = AdminService(db)
    return admin_service.get_users_for_management(role_filter=role)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user role (admin only)."""
    admin_service = AdminService(db)
    updated_user = admin_service.update_user_role(user_id, role_update.role)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    auth_service = AuthService(db)
    success = auth_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


@router.get("/quality-reviews", response_model=List[QualityReviewItemResponse])
async def get_quality_reviews(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get quality review items."""
    admin_service = AdminService(db)
    return admin_service.get_quality_review_items(limit=limit)


@router.get("/quality-reviews/flagged", response_model=List[FlaggedTranscriptionResponse])
async def get_flagged_transcriptions(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get transcriptions flagged for review."""
    admin_service = AdminService(db)
    return admin_service.get_flagged_transcriptions(limit=limit)


@router.post("/quality-reviews/{transcription_id}")
async def create_quality_review(
    transcription_id: int,
    review_data: QualityReviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a quality review for a transcription (admin only)."""
    admin_service = AdminService(db)
    
    try:
        review = admin_service.create_quality_review(
            transcription_id=transcription_id,
            reviewer_id=current_user.id,
            decision=review_data.decision,
            rating=review_data.rating,
            comment=review_data.comment
        )
        return {"message": "Quality review created successfully", "review_id": review.id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create quality review: {str(e)}"
        )


@router.get("/system/health")
async def get_system_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get comprehensive system health metrics."""
    from app.core.monitoring import run_health_check
    from app.core.logging_config import get_logger
    
    logger = get_logger(__name__)
    
    try:
        health_status = await run_health_check()
        logger.info(f"Admin health check requested by user {current_user.id}")
        return health_status
    except Exception as e:
        logger.error(f"Admin health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health status"
        )


@router.get("/system/metrics")
async def get_system_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get detailed system metrics."""
    from app.core.monitoring import get_system_metrics
    from app.core.logging_config import get_logger
    
    logger = get_logger(__name__)
    
    try:
        metrics = await get_system_metrics()
        logger.info(f"System metrics requested by user {current_user.id}")
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "disk_percent": metrics.disk_percent,
            "active_connections": metrics.active_connections,
            "redis_connected": metrics.redis_connected,
            "database_connected": metrics.database_connected,
            "celery_workers": metrics.celery_workers,
            "queue_size": metrics.queue_size,
            "error_rate": metrics.error_rate,
            "response_time_avg": metrics.response_time_avg
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )


@router.get("/system/alerts")
async def get_recent_alerts(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get recent system alerts."""
    from app.core.monitoring import health_checker
    from app.core.logging_config import get_logger
    
    logger = get_logger(__name__)
    
    try:
        alerts = await health_checker.get_recent_alerts(limit=limit)
        logger.info(f"System alerts requested by user {current_user.id}")
        return {
            "alerts": alerts,
            "total_count": len(alerts)
        }
    except Exception as e:
        logger.error(f"Failed to get system alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system alerts"
        )


@router.get("/analytics/usage", response_model=UsageAnalyticsResponse)
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get usage analytics for the specified period."""
    admin_service = AdminService(db)
    return admin_service.get_usage_analytics(days=days)


@router.get("/system/storage")
async def get_storage_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get storage usage information."""
    # This would typically integrate with your storage system (S3, MinIO, etc.)
    # For now, return a placeholder response
    return {
        "total_storage_gb": 0.0,
        "used_storage_gb": 0.0,
        "available_storage_gb": 0.0,
        "storage_by_type": {
            "recordings": 0.0,
            "chunks": 0.0,
            "other": 0.0
        }
    }


@router.get("/system/logs")
async def get_system_logs(
    level: str = Query("INFO", description="Log level filter"),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get system logs (admin only)."""
    # This would typically integrate with your logging system
    # For now, return a placeholder response
    return {
        "logs": [],
        "total_count": 0,
        "message": "Log integration not implemented yet"
    }