from datetime import timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserCreateAdmin, UserLogin


class AuthService:
    """Authentication service for user management."""

    def __init__(self, db: Session):
        self.db = db

    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user. For this workflow, they are verified by default."""
        existing_user = self.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            role=UserRole.CONTRIBUTOR,
            is_verified=True,  # CHANGED: They just verified via the token link!
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def create_user_with_role(self, user_data: UserCreateAdmin) -> User:
        """Create a new user with specified role (admin-only operation)."""
        existing_user = (
            self.db.query(User).filter(User.email == user_data.email).first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            name=user_data.name,
            email=user_data.email,
            password_hash=hashed_password,
            role=user_data.role,  # Use specified role (admin operation)
            is_verified=True,
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, login_data: UserLogin) -> Optional[User]:
        """Authenticate user with email and password."""
        user = self.db.query(User).filter(User.email == login_data.email).first()
        if not user:
            return None

        if not verify_password(login_data.password, user.password_hash):
            return None

        return user

    def login(self, login_data: UserLogin) -> tuple[User, str]:
        """Login user and return user object with access token."""
        user = self.authenticate_user(login_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # --- Verification Check ---
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email address not verified. Please check your inbox.",
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role.value},
            expires_delta=access_token_expires,
        )

        return user, access_token

    def update_password(self, user: User, new_password: str) -> User:
        """Update user password (used for password reset flow)."""
        user.password_hash = get_password_hash(new_password)
        # Often a password reset should also ensure the user is verified
        user.is_verified = True

        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def update_user_role(self, user_id: int, new_role: UserRole) -> User:
        """Update user role (admin only operation)."""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        user.role = new_role
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(self, user_id: int) -> bool:
        """Delete user and all associated data."""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        # Note: In a production system, you might want to soft delete
        # or handle cascading deletes more carefully
        self.db.delete(user)
        self.db.commit()
        return True
