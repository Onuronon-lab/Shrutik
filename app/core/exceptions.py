"""
Custom exception classes and error handling utilities for the Voice Data Collection Platform.

This module defines custom exceptions, error handlers, and utilities for
comprehensive error handling throughout the application.
"""

import logging
import traceback
from typing import Any, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# Custom Exception Classes
class VoiceCollectionError(Exception):
    """Base exception class for Voice Collection Platform errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class AudioProcessingError(VoiceCollectionError):
    """Exception raised during audio processing operations."""


class TranscriptionError(VoiceCollectionError):
    """Exception raised during transcription operations."""


class ConsensusError(VoiceCollectionError):
    """Exception raised during consensus calculation operations."""


class AuthenticationError(VoiceCollectionError):
    """Exception raised during authentication operations."""


class AuthorizationError(VoiceCollectionError):
    """Exception raised during authorization operations."""


class DatabaseError(VoiceCollectionError):
    """Exception raised during database operations."""


class FileStorageError(VoiceCollectionError):
    """Exception raised during file storage operations."""


class ValidationError(VoiceCollectionError):
    """Exception raised during data validation operations."""


class ExternalServiceError(VoiceCollectionError):
    """Exception raised when external services fail."""


class RateLimitError(VoiceCollectionError):
    """Exception raised when rate limits are exceeded."""


# Error Response Models
class ErrorResponse:
    """Standard error response format."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.request_id = request_id

    def to_dict(self) -> Dict[str, Any]:
        """Convert error response to dictionary."""
        response = {
            "error": {
                "message": self.message,
                "code": self.error_code,
                "status_code": self.status_code,
            }
        }

        if self.details:
            response["error"]["details"] = self.details

        if self.request_id:
            response["error"]["request_id"] = self.request_id

        return response


# Error Handler Functions
async def custom_exception_handler(
    request: Request, exc: VoiceCollectionError
) -> JSONResponse:
    """
    Handle custom Voice Collection Platform exceptions.

    Args:
        request: FastAPI request object
        exc: Custom exception instance

    Returns:
        JSON response with error details
    """
    # Log the error with context
    logger.error(
        f"Custom exception occurred: {exc.error_code}",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
        },
        exc_info=True,
    )

    # Determine status code based on exception type
    status_code_map = {
        AudioProcessingError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        TranscriptionError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        ConsensusError: status.HTTP_422_UNPROCESSABLE_ENTITY,
        AuthenticationError: status.HTTP_401_UNAUTHORIZED,
        AuthorizationError: status.HTTP_403_FORBIDDEN,
        DatabaseError: status.HTTP_500_INTERNAL_SERVER_ERROR,
        FileStorageError: status.HTTP_507_INSUFFICIENT_STORAGE,
        ValidationError: status.HTTP_400_BAD_REQUEST,
        ExternalServiceError: status.HTTP_502_BAD_GATEWAY,
        RateLimitError: status.HTTP_429_TOO_MANY_REQUESTS,
    }

    status_code = status_code_map.get(type(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Create error response
    error_response = ErrorResponse(
        message=exc.message,
        error_code=exc.error_code,
        status_code=status_code,
        details=exc.details,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=status_code, content=error_response.to_dict())


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle FastAPI HTTP exceptions.

    Args:
        request: FastAPI request object
        exc: HTTP exception instance

    Returns:
        JSON response with error details
    """
    # Log the error
    logger.warning(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
        },
    )

    # Check if detail is already a structured error (dict with error_key)
    if isinstance(exc.detail, dict):
        # Return the structured error directly
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    # Create standardized error response for simple string details
    error_response = ErrorResponse(
        message=str(exc.detail),
        error_code="HTTP_ERROR",
        status_code=exc.status_code,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(status_code=exc.status_code, content=error_response.to_dict())


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Args:
        request: FastAPI request object
        exc: Validation error instance

    Returns:
        JSON response with validation error details
    """
    # Log validation error
    logger.warning(
        f"Validation error: {len(exc.errors())} errors",
        extra={
            "errors": exc.errors(),
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
        },
    )

    # Format validation errors for user-friendly response
    formatted_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append(
            {"field": field_path, "message": error["msg"], "type": error["type"]}
        )

    error_response = ErrorResponse(
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"validation_errors": formatted_errors},
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.to_dict(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Args:
        request: FastAPI request object
        exc: Exception instance

    Returns:
        JSON response with generic error message
    """
    # Log the unexpected error with full traceback
    logger.error(
        f"Unexpected error: {type(exc).__name__}: {str(exc)}",
        extra={
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None,
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )

    # Return generic error message to avoid exposing internal details
    error_response = ErrorResponse(
        message="An unexpected error occurred. Please try again later.",
        error_code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=getattr(request.state, "request_id", None),
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict(),
    )


# Utility Functions
def log_and_raise_error(
    logger_instance: logging.Logger,
    error_class: type,
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    **log_extra,
) -> None:
    """
    Log an error and raise a custom exception.

    Args:
        logger_instance: Logger to use for logging
        error_class: Exception class to raise
        message: Error message
        error_code: Optional error code
        details: Optional error details
        **log_extra: Additional fields for logging
    """
    # Log the error
    logger_instance.error(message, extra=log_extra, exc_info=True)

    # Raise the exception
    raise error_class(message=message, error_code=error_code, details=details)


def safe_execute(
    func,
    *args,
    logger_instance: Optional[logging.Logger] = None,
    error_message: str = "Operation failed",
    error_class: type = VoiceCollectionError,
    fallback_value: Any = None,
    **kwargs,
) -> Any:
    """
    Safely execute a function with error handling.

    Args:
        func: Function to execute
        *args: Function arguments
        logger_instance: Logger for error logging
        error_message: Message to log on error
        error_class: Exception class to raise on error
        fallback_value: Value to return if function fails and no exception should be raised
        **kwargs: Function keyword arguments

    Returns:
        Function result or fallback value

    Raises:
        error_class: If function fails and no fallback value is provided
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if logger_instance:
            logger_instance.error(f"{error_message}: {str(e)}", exc_info=True)

        if fallback_value is not None:
            return fallback_value

        raise error_class(message=f"{error_message}: {str(e)}")


def create_user_friendly_message(error: Exception) -> str:
    """
    Create user-friendly error messages from exceptions.

    Args:
        error: Exception instance

    Returns:
        User-friendly error message
    """
    error_messages = {
        AudioProcessingError: "There was an issue processing your audio file. Please try uploading again or contact support if the problem persists.",
        TranscriptionError: "There was an issue with your transcription. Please try again or skip this audio chunk.",
        ConsensusError: "There was an issue calculating transcription consensus. Our team has been notified.",
        AuthenticationError: "Authentication failed. Please log in again.",
        AuthorizationError: "You don't have permission to perform this action.",
        DatabaseError: "There was a temporary database issue. Please try again in a few moments.",
        FileStorageError: "There was an issue storing your file. Please try again or contact support.",
        ValidationError: "The provided data is invalid. Please check your input and try again.",
        ExternalServiceError: "An external service is temporarily unavailable. Please try again later.",
        RateLimitError: "You're making requests too quickly. Please wait a moment and try again.",
    }

    return error_messages.get(
        type(error), "An unexpected error occurred. Please try again later."
    )


# Context Managers for Error Handling
class ErrorContext:
    """
    Context manager for handling errors in specific operations.

    Usage:
        with ErrorContext("audio processing", AudioProcessingError, logger):
            # Audio processing code here
            pass
    """

    def __init__(
        self,
        operation_name: str,
        error_class: type = VoiceCollectionError,
        logger_instance: Optional[logging.Logger] = None,
        **log_extra,
    ):
        self.operation_name = operation_name
        self.error_class = error_class
        self.logger = logger_instance or logger
        self.log_extra = log_extra

    def __enter__(self):
        self.logger.info(f"Starting {self.operation_name}", extra=self.log_extra)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(
                f"Completed {self.operation_name} successfully", extra=self.log_extra
            )
        else:
            self.logger.error(
                f"Failed {self.operation_name}: {str(exc_val)}",
                extra=self.log_extra,
                exc_info=True,
            )

            # Re-raise as custom exception if it's not already one
            if not isinstance(exc_val, VoiceCollectionError):
                raise self.error_class(
                    message=f"{self.operation_name} failed: {str(exc_val)}"
                ) from exc_val

        return False  # Don't suppress exceptions
