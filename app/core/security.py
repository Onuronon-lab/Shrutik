from datetime import datetime, timedelta, timezone
from typing import Optional, Union

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.models.user import UserRole

try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    pwd_context.hash("test"[:72])
except Exception:
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if len(plain_password.encode("utf-8")) > 72:
            plain_password = plain_password[:72]
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    if len(password.encode("utf-8")) > 72:
        password = password.encode("utf-8")[:72].decode("utf-8", errors="ignore")
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_task_token(
    email: str, scope: str, expires_minutes: int, data: dict = None
) -> str:
    """Create a token that can optionally carry extra data (like name/password)."""
    to_encode = {
        "sub": email,
        "scope": scope,
        "exp": datetime.utcnow() + timedelta(minutes=expires_minutes),
    }
    if data:
        to_encode.update({"extra_data": data})  # Pack name/password here
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


def verify_task_token_with_data(token: str, expected_scope: str) -> dict:
    """Verify the token and return the full dictionary of data."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("scope") != expected_scope:
            return None

        # Return everything needed to create the user
        return {
            "email": payload.get("sub"),
            "name": payload.get("extra_data", {}).get("name"),
            "password": payload.get("extra_data", {}).get("password"),
        }
    except jwt.JWTError:
        return None


class PermissionChecker:
    ROLE_PERMISSIONS = {
        UserRole.CONTRIBUTOR: {"record_voice", "transcribe_audio", "view_own_data"},
        UserRole.ADMIN: {
            "record_voice",
            "transcribe_audio",
            "view_own_data",
            "manage_users",
            "manage_scripts",
            "view_all_data",
            "quality_review",
            "view_statistics",
            "export_data",
        },
        UserRole.SWORIK_DEVELOPER: {
            "record_voice",
            "transcribe_audio",
            "view_own_data",
            "view_all_data",
            "quality_review",
            "view_statistics",
            "export_data",
            "access_raw_data",
        },
    }

    @classmethod
    def has_permission(cls, user_role: UserRole, permission: str) -> bool:
        return permission in cls.ROLE_PERMISSIONS.get(user_role, set())

    @classmethod
    def require_permission(cls, user_role: UserRole, permission: str) -> None:
        if not cls.has_permission(user_role, permission):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

    @classmethod
    def require_role(
        cls, user_role: UserRole, required_roles: Union[UserRole, list[UserRole]]
    ) -> None:
        roles = (
            [required_roles] if isinstance(required_roles, UserRole) else required_roles
        )
        if user_role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient role")


def verify_task_token(token: str, expected_scope: str) -> Optional[str]:
    """Verify the token scope and return the email (sub)."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("scope") != expected_scope:
            return None
        return payload.get("sub")
    except (jwt.JWTError, AttributeError):
        return None
