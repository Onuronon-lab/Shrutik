import logging
import time
from typing import Optional

from fastapi import Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import verify_token
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


class AuthContextMiddleware(BaseHTTPMiddleware):
    """Middleware to inject user context into requests."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        user_context = None
        authorization = request.headers.get("Authorization")

        if authorization:
            scheme, token = get_authorization_scheme_param(authorization)
            if scheme.lower() == "bearer" and token:
                try:
                    payload = verify_token(token)
                    user_context = {
                        "user_id": payload.get("user_id"),
                        "email": payload.get("sub"),
                        "role": payload.get("role"),
                    }
                except Exception:
                    # Token is invalid, but we don't raise error here
                    # Let the endpoint handle authentication
                    pass

        request.state.user_context = user_context

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} - "
            f"Status: {response.status_code} - "
            f"Time: {process_time:.3f}s - "
            f"User: {user_context.get('email') if user_context else 'Anonymous'}"
        )

        return response


def get_user_context(request: Request) -> Optional[dict]:
    """Get user context from request state."""
    return getattr(request.state, "user_context", None)


def get_current_user_id(request: Request) -> Optional[int]:
    """Get current user ID from request context."""
    context = get_user_context(request)
    return context.get("user_id") if context else None


def get_current_user_role(request: Request) -> Optional[UserRole]:
    """Get current user role from request context."""
    context = get_user_context(request)
    if context and context.get("role"):
        try:
            return UserRole(context["role"])
        except ValueError:
            return None
    return None
