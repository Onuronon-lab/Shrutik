from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.auth import UserCreate, UserCreateAdmin, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_active_user, require_admin
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    auth_service = AuthService(db)
    user = auth_service.create_user(user_data)
    return user


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """Login user and return access token."""
    auth_service = AuthService(db)
    user, access_token = auth_service.login(login_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information."""
    return current_user


@router.get("/me/stats")
async def get_current_user_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get current user's contribution statistics."""
    from sqlalchemy import func
    from app.models.voice_recording import VoiceRecording
    from app.models.transcription import Transcription
    from app.models.quality_review import QualityReview
    
    recordings_count = db.query(VoiceRecording).filter(
        VoiceRecording.user_id == current_user.id
    ).count()

    transcriptions_count = db.query(Transcription).filter(
        Transcription.user_id == current_user.id
    ).count()

    avg_quality = db.query(func.avg(Transcription.quality)).filter(
        Transcription.user_id == current_user.id,
        Transcription.quality.isnot(None)
    ).scalar()

    reviews_count = db.query(QualityReview).filter(
        QualityReview.reviewer_id == current_user.id
    ).count()
    
    return {
        "recordings_count": recordings_count,
        "transcriptions_count": transcriptions_count,
        "quality_reviews_count": reviews_count,
        "avg_transcription_quality": float(avg_quality) if avg_quality else None
    }


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update user role (admin only)."""
    auth_service = AuthService(db)
    updated_user = auth_service.update_user_role(user_id, new_role)
    return updated_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all users (admin only)."""
    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_with_role(
    user_data: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new user with specified role (admin only)."""
    auth_service = AuthService(db)
    user = auth_service.create_user_with_role(user_data)
    return user