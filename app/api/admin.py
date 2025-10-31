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
from app.core.performance import performance_optimizer
from app.core.rate_limiting import rate_limit_manager
from app.core.cache import cache_manager

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


# Performance monitoring endpoints
@router.get("/performance/dashboard")
async def get_performance_dashboard(
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get comprehensive performance dashboard data."""
    try:
        dashboard_data = performance_optimizer.get_performance_dashboard()
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance dashboard: {str(e)}"
        )


@router.get("/performance/endpoints")
async def get_endpoint_performance(
    endpoint: Optional[str] = Query(None, description="Filter by specific endpoint"),
    days: int = Query(1, ge=1, le=7, description="Number of days to analyze"),
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get performance metrics for API endpoints."""
    try:
        from app.core.performance import performance_metrics
        
        if endpoint:
            metrics = performance_metrics.get_endpoint_metrics(endpoint, "GET", days)
            return {"endpoint_metrics": [metrics]}
        else:
            # Get metrics for common endpoints
            common_endpoints = [
                "/api/transcriptions/tasks",
                "/api/transcriptions/submit",
                "/api/recordings/upload",
                "/api/chunks/{chunk_id}/audio",
                "/api/auth/login"
            ]
            
            all_metrics = []
            for ep in common_endpoints:
                metrics = performance_metrics.get_endpoint_metrics(ep, "GET", days)
                all_metrics.append(metrics)
            
            return {"endpoint_metrics": all_metrics}
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get endpoint performance: {str(e)}"
        )


@router.get("/performance/cache")
async def get_cache_performance(
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get cache performance metrics and optimization recommendations."""
    try:
        cache_stats = performance_optimizer.optimize_cache_settings()
        
        # Add cache size information
        cache_info = {
            "redis_connected": cache_manager.redis.ping(),
            "cache_keys_count": len(cache_manager.redis.client.keys("*")) if cache_manager.redis.ping() else 0
        }
        
        return {
            "cache_optimization": cache_stats,
            "cache_info": cache_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache performance: {str(e)}"
        )


@router.get("/performance/database")
async def get_database_performance(
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get database performance metrics."""
    try:
        from app.db.database import get_connection_pool_status
        from app.core.performance import query_optimizer
        
        pool_status = get_connection_pool_status()
        query_report = query_optimizer.get_query_performance_report()
        
        return {
            "connection_pool": pool_status,
            "query_performance": query_report
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database performance: {str(e)}"
        )


@router.get("/performance/rate-limits")
async def get_rate_limit_stats(
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get rate limiting statistics."""
    try:
        stats = rate_limit_manager.get_rate_limit_statistics()
        return {"rate_limit_stats": stats}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit stats: {str(e)}"
        )


@router.post("/performance/cache/clear")
async def clear_cache(
    cache_type: str = Query("all", description="Type of cache to clear (all, api, db, stats)"),
    current_user: User = Depends(require_admin)
):
    """Clear cache (admin only)."""
    try:
        if cache_type == "all":
            cache_manager.redis.client.flushdb()
            message = "All caches cleared"
        elif cache_type == "api":
            from app.core.cache import api_cache
            api_cache.cache.delete_pattern("api_response:*")
            message = "API response cache cleared"
        elif cache_type == "db":
            from app.core.cache import db_cache
            db_cache.cache.delete_pattern("db_query:*")
            message = "Database query cache cleared"
        elif cache_type == "stats":
            from app.core.cache import stats_cache
            stats_cache.invalidate_statistics()
            message = "Statistics cache cleared"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cache type"
            )
        
        return {"message": message}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@router.post("/performance/rate-limits/{user_id}/reset")
async def reset_user_rate_limit(
    user_id: int,
    current_user: User = Depends(require_admin)
):
    """Reset rate limits for a specific user (admin only)."""
    try:
        success = rate_limit_manager.reset_user_rate_limit(user_id)
        
        if success:
            return {"message": f"Rate limits reset for user {user_id}"}
        else:
            return {"message": f"No rate limits found for user {user_id}"}
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset rate limits: {str(e)}"
        )


@router.get("/performance/cdn")
async def get_cdn_status(
    current_user: User = Depends(require_admin_or_sworik)
):
    """Get CDN status and configuration."""
    try:
        from app.core.cdn import cdn_manager
        
        cdn_status = {
            "enabled": cdn_manager.config.is_cdn_enabled(),
            "base_url": cdn_manager.config.CDN_BASE_URL,
            "provider": cdn_manager.config.CDN_PROVIDER,
            "audio_cache_ttl": cdn_manager.config.AUDIO_CACHE_TTL,
            "static_cache_ttl": cdn_manager.config.STATIC_CACHE_TTL
        }
        
        return {"cdn_status": cdn_status}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CDN status: {str(e)}"
        )