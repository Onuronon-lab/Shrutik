from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

# New imports for Verification and Email
from app.core import security
from app.core.dependencies import get_current_active_user, require_admin
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import Token, UserCreate, UserCreateAdmin, UserLogin, UserResponse
from app.services.auth_service import AuthService
from app.services.mail import send_auth_email

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Stage a new user and send verification email with embedded data."""

    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    token_payload = {
        "email": user_data.email,
        "name": user_data.name,
        "password": user_data.password,
    }

    token = security.create_task_token(
        email=user_data.email,
        scope="complete_registration",  # New scope for this workflow
        expires_minutes=1440,
        # If your create_task_token supports extra data, add it here:
        data={"name": user_data.name, "password": user_data.password},
    )

    background_tasks.add_task(send_auth_email, user_data.email, token, "verify")

    return {"message": "Please check your email to complete account creation."}


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login user and return access token."""
    auth_service = AuthService(db)

    user, access_token = auth_service.login(login_data)

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Confirm email and FINALLY create the user record."""
    # Extract the data using the NEW helper and the NEW scope
    reg_data = security.verify_task_token_with_data(
        token, expected_scope="complete_registration"
    )

    if not reg_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification link.",
        )

    # Prevent duplicate creation if they click the link twice
    email = reg_data["email"]
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return {"message": "Account already created. You can login now."}

    # Use AuthService to create the user in the database
    auth_service = AuthService(db)
    user = auth_service.create_user(
        UserCreate(email=email, name=reg_data["name"], password=reg_data["password"])
    )

    # Mark as verified immediately
    user.is_verified = True
    db.commit()

    return {"message": "Account created successfully! You can now login."}


@router.post("/password-reset/request")
async def request_password_reset(
    email: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
) -> dict:
    """Request a password reset link."""
    user = db.query(User).filter(User.email == email).first()
    if user:
        token = security.create_task_token(
            email=user.email, scope="password_reset", expires_minutes=30
        )
        background_tasks.add_task(send_auth_email, user.email, token, "reset")

    # Always return 200 for security to prevent email enumeration
    return {"message": "If the email is registered, a reset link has been sent."}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    token: str, new_password: str, db: Session = Depends(get_db)
) -> dict:
    """Reset password using the token from the email link."""
    email = security.verify_task_token(token, expected_scope="password_reset")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Use AuthService to handle hashing and saving
    auth_service = AuthService(db)
    auth_service.update_password(user, new_password)

    return {"message": "Password updated successfully."}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


@router.get("/me/stats")
async def get_current_user_stats(
    current_user: User = Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """Get current user's contribution statistics."""
    from sqlalchemy import func

    from app.models.quality_review import QualityReview
    from app.models.transcription import Transcription
    from app.models.voice_recording import VoiceRecording

    recordings_count = (
        db.query(VoiceRecording)
        .filter(VoiceRecording.user_id == current_user.id)
        .count()
    )

    transcriptions_count = (
        db.query(Transcription).filter(Transcription.user_id == current_user.id).count()
    )

    avg_quality = (
        db.query(func.avg(Transcription.quality))
        .filter(
            Transcription.user_id == current_user.id, Transcription.quality.isnot(None)
        )
        .scalar()
    )

    reviews_count = (
        db.query(QualityReview)
        .filter(QualityReview.reviewer_id == current_user.id)
        .count()
    )

    return {
        "recordings_count": recordings_count,
        "transcriptions_count": transcriptions_count,
        "quality_reviews_count": reviews_count,
        "avg_transcription_quality": float(avg_quality) if avg_quality else None,
    }


@router.put("/users/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update user role (admin only)."""
    auth_service = AuthService(db)
    updated_user = auth_service.update_user_role(user_id, new_role)
    return updated_user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    db: Session = Depends(get_db), current_user: User = Depends(require_admin)
):
    """List all users (admin only)."""
    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_with_role(
    user_data: UserCreateAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new user with specified role (admin only)."""
    auth_service = AuthService(db)
    user = auth_service.create_user_with_role(user_data)
    return user
