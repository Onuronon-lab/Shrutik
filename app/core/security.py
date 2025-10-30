from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.user import UserRole

try:
    # Try bcrypt first with a simple test
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    pwd_context.hash("test"[:72])  # Ensure test password is within bcrypt limits
except Exception as e:
    print(f"bcrypt failed: {e}")
    try:
        # Fallback to argon2
        pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
        pwd_context.hash("test")
    except Exception as e2:
        print(f"argon2 failed: {e2}")
        # Final fallback to pbkdf2 (always available)
        pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionChecker:
    """Role-based permission checker."""
    
    ROLE_PERMISSIONS = {
        UserRole.CONTRIBUTOR: {
            "record_voice",
            "transcribe_audio",
            "view_own_data",
        },
        UserRole.ADMIN: {
            "record_voice",
            "transcribe_audio",
            "view_own_data",
            "manage_users",
            "manage_scripts",
            "view_all_data",
            "quality_review",
            "view_statistics",
        },
        UserRole.SWORIK_DEVELOPER: {
            "record_voice",
            "transcribe_audio",
            "view_own_data",
            "manage_users",
            "manage_scripts",
            "view_all_data",
            "quality_review",
            "view_statistics",
            "export_data",
            "access_raw_data",
        }
    }
    
    @classmethod
    def has_permission(cls, user_role: UserRole, permission: str) -> bool:
        """Check if a user role has a specific permission."""
        return permission in cls.ROLE_PERMISSIONS.get(user_role, set())
    
    @classmethod
    def require_permission(cls, user_role: UserRole, permission: str) -> None:
        """Raise exception if user doesn't have required permission."""
        if not cls.has_permission(user_role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
    
    @classmethod
    def require_role(cls, user_role: UserRole, required_roles: Union[UserRole, list[UserRole]]) -> None:
        """Raise exception if user doesn't have required role."""
        if isinstance(required_roles, UserRole):
            required_roles = [required_roles]
        
        if user_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient role. Required one of: {[role.value for role in required_roles]}"
            )