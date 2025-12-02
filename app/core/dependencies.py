from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import PermissionChecker, verify_token
from app.db.database import get_db
from app.models.user import User, UserRole
from app.services.auth_service import AuthService

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials

    payload = verify_token(token)
    email: str = payload.get("sub")
    user_id: int = payload.get("user_id")

    if email is None or user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_service = AuthService(db)
    user = auth_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user (can be extended to check if user is active/disabled)."""
    return current_user


def require_role(*roles: UserRole):
    """Dependency factory to require specific roles."""

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        PermissionChecker.require_role(current_user.role, list(roles))
        return current_user

    return role_checker


def require_permission(permission: str):
    """Dependency factory to require specific permissions."""

    def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        PermissionChecker.require_permission(current_user.role, permission)
        return current_user

    return permission_checker


require_admin = require_role(UserRole.ADMIN)
require_sworik_developer = require_role(UserRole.SWORIK_DEVELOPER)
require_admin_or_sworik = require_role(UserRole.ADMIN, UserRole.SWORIK_DEVELOPER)

require_export_permission = require_permission("export_data")
require_manage_users_permission = require_permission("manage_users")
require_quality_review_permission = require_permission("quality_review")
