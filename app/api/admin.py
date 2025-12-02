from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin, require_admin_or_sworik
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.admin import (
    FlaggedTranscriptionResponse,
    PlatformStatsResponse,
    QualityReviewItemResponse,
    QualityReviewUpdateRequest,
    RoleUpdateRequest,
    UsageAnalyticsResponse,
    UserManagementResponse,
    UserStatsResponse,
)
from app.schemas.auth import UserResponse
from app.services.admin_service import AdminService
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats/platform", response_model=PlatformStatsResponse)
async def get_platform_statistics(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_sworik)
):
    """Get comprehensive platform statistics."""
    admin_service = AdminService(db)
    return admin_service.get_platform_statistics()


@router.get("/stats/users", response_model=List[UserStatsResponse])
async def get_user_statistics(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get detailed user statistics."""
    admin_service = AdminService(db)
    return admin_service.get_user_statistics(limit=limit)


@router.get("/users", response_model=List[UserManagementResponse])
async def get_users_for_management(
    role: Optional[UserRole] = Query(None, description="Filter users by role"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get users for management interface (admin only)."""
    admin_service = AdminService(db)
    return admin_service.get_users_for_management(role_filter=role)


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_update: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update user role (admin only)."""
    admin_service = AdminService(db)
    updated_user = admin_service.update_user_role(user_id, role_update.role)

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return updated_user


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete user (admin only)."""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    auth_service = AuthService(db)
    success = auth_service.delete_user(user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return {"message": "User deleted successfully"}


@router.get("/quality-reviews", response_model=List[QualityReviewItemResponse])
async def get_quality_reviews(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get quality review items."""
    admin_service = AdminService(db)
    return admin_service.get_quality_review_items(limit=limit)


@router.get(
    "/quality-reviews/flagged", response_model=List[FlaggedTranscriptionResponse]
)
async def get_flagged_transcriptions(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get transcriptions flagged for review."""
    admin_service = AdminService(db)
    return admin_service.get_flagged_transcriptions(limit=limit)


@router.post("/quality-reviews/{transcription_id}")
async def create_quality_review(
    transcription_id: int,
    review_data: QualityReviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a quality review for a transcription (admin only)."""
    admin_service = AdminService(db)

    try:
        review = admin_service.create_quality_review(
            transcription_id=transcription_id,
            reviewer_id=current_user.id,
            decision=review_data.decision,
            rating=review_data.rating,
            comment=review_data.comment,
        )
        return {
            "message": "Quality review created successfully",
            "review_id": review.id,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create quality review: {str(e)}",
        )


@router.get("/analytics/usage", response_model=UsageAnalyticsResponse)
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get usage analytics for the specified period."""
    admin_service = AdminService(db)
    return admin_service.get_usage_analytics(days=days)


@router.get("/system/health")
async def get_admin_system_health(
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get system health information for admin dashboard."""
    from app.core.logging_config import get_logger
    from app.core.monitoring import run_health_check

    logger = get_logger(__name__)

    try:
        health_status = await run_health_check()
        logger.info(f"Admin system health check requested by user {current_user.id}")
        return health_status
    except Exception as e:
        logger.error(f"Admin system health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health status",
        )
