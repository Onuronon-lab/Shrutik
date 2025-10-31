"""
User-friendly error messages and fallback mechanisms.

This module provides user-friendly error messages for different types of errors
and implements fallback mechanisms for critical system failures.
"""

from typing import Dict, Any, Optional
from app.core.exceptions import (
    AudioProcessingError, TranscriptionError, ConsensusError,
    AuthenticationError, AuthorizationError, DatabaseError,
    FileStorageError, ValidationError, ExternalServiceError, RateLimitError
)


# User-friendly error messages
ERROR_MESSAGES = {
    # Audio Processing Errors
    "AUDIO_LOAD_FAILED": {
        "title": "Audio File Error",
        "message": "We couldn't process your audio file. Please make sure it's a valid audio file and try uploading again.",
        "suggestions": [
            "Check that your file is in a supported format (WAV, MP3, M4A, FLAC, WebM)",
            "Ensure the file isn't corrupted",
            "Try converting to WAV format if the issue persists"
        ]
    },
    "AUDIO_TOO_SHORT": {
        "title": "Recording Too Short",
        "message": "Your recording is too short. Please record for at least 1 second.",
        "suggestions": [
            "Make sure you're speaking clearly into the microphone",
            "Check that your microphone is working properly",
            "Try recording the script again"
        ]
    },
    "AUDIO_TOO_LONG": {
        "title": "Recording Too Long",
        "message": "Your recording is too long. Please keep recordings under 30 minutes.",
        "suggestions": [
            "Break longer content into smaller segments",
            "Focus on the provided script text only",
            "Remove any long pauses or silence"
        ]
    },
    "AUDIO_QUALITY_LOW": {
        "title": "Audio Quality Issue",
        "message": "The audio quality is too low for processing. Please try recording again.",
        "suggestions": [
            "Record in a quiet environment",
            "Speak clearly and at a normal volume",
            "Check your microphone settings",
            "Move closer to the microphone"
        ]
    },
    "CHUNKING_FAILED": {
        "title": "Processing Error",
        "message": "We couldn't break your recording into segments. Our team has been notified.",
        "suggestions": [
            "Try uploading again in a few minutes",
            "If the problem persists, contact support"
        ]
    },
    
    # File Storage Errors
    "FILE_TOO_LARGE": {
        "title": "File Too Large",
        "message": "Your file is too large to upload. Please reduce the file size and try again.",
        "suggestions": [
            "Compress your audio file",
            "Use a lower quality setting when recording",
            "Break longer recordings into smaller parts"
        ]
    },
    "UNSUPPORTED_FORMAT": {
        "title": "Unsupported File Format",
        "message": "This file format isn't supported. Please use WAV, MP3, M4A, FLAC, or WebM format.",
        "suggestions": [
            "Convert your file to a supported format",
            "WAV format usually works best",
            "Check that the file extension matches the actual format"
        ]
    },
    "STORAGE_FULL": {
        "title": "Storage Issue",
        "message": "We're temporarily unable to store new files. Please try again in a few minutes.",
        "suggestions": [
            "Wait a few minutes and try again",
            "Contact support if the issue persists"
        ]
    },
    
    # Authentication/Authorization Errors
    "INVALID_TOKEN": {
        "title": "Session Expired",
        "message": "Your session has expired. Please log in again.",
        "suggestions": [
            "Click the login button to sign in again",
            "Make sure cookies are enabled in your browser"
        ]
    },
    "INSUFFICIENT_PERMISSIONS": {
        "title": "Access Denied",
        "message": "You don't have permission to perform this action.",
        "suggestions": [
            "Contact an administrator if you need access",
            "Make sure you're logged into the correct account"
        ]
    },
    
    # Database Errors
    "DATABASE_CONNECTION": {
        "title": "Connection Issue",
        "message": "We're having trouble connecting to our servers. Please try again in a moment.",
        "suggestions": [
            "Check your internet connection",
            "Try refreshing the page",
            "Wait a moment and try again"
        ]
    },
    "DATA_NOT_FOUND": {
        "title": "Not Found",
        "message": "The requested item couldn't be found.",
        "suggestions": [
            "Check that the link is correct",
            "The item may have been deleted",
            "Try searching for it again"
        ]
    },
    
    # Validation Errors
    "INVALID_SESSION": {
        "title": "Invalid Session",
        "message": "Your recording session has expired or is invalid. Please start a new recording session.",
        "suggestions": [
            "Go back and select a script to record",
            "Recording sessions expire after 2 hours",
            "Make sure you're using the latest recording interface"
        ]
    },
    "MISSING_REQUIRED_FIELD": {
        "title": "Missing Information",
        "message": "Some required information is missing. Please check your input and try again.",
        "suggestions": [
            "Fill in all required fields",
            "Check for any error messages on the form"
        ]
    },
    
    # Rate Limiting
    "RATE_LIMIT_EXCEEDED": {
        "title": "Too Many Requests",
        "message": "You're making requests too quickly. Please wait a moment and try again.",
        "suggestions": [
            "Wait 30 seconds before trying again",
            "Avoid clicking buttons multiple times",
            "If you need to make many requests, contact support"
        ]
    },
    
    # External Service Errors
    "EXTERNAL_SERVICE_DOWN": {
        "title": "Service Temporarily Unavailable",
        "message": "One of our services is temporarily unavailable. Please try again later.",
        "suggestions": [
            "Try again in a few minutes",
            "Check our status page for updates",
            "Contact support if the issue persists"
        ]
    },
    
    # Generic Fallbacks
    "UNKNOWN_ERROR": {
        "title": "Unexpected Error",
        "message": "Something unexpected happened. Our team has been notified and will investigate.",
        "suggestions": [
            "Try refreshing the page",
            "If the problem persists, contact support",
            "Include details about what you were doing when this happened"
        ]
    }
}


def get_user_friendly_error(
    error_code: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Get user-friendly error message for an error code.
    
    Args:
        error_code: Error code to look up
        details: Additional error details for customization
        
    Returns:
        Dictionary with title, message, and suggestions
    """
    error_info = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES["UNKNOWN_ERROR"])
    
    # Create a copy to avoid modifying the original
    result = error_info.copy()
    
    # Customize message based on details if available
    if details and error_code == "FILE_TOO_LARGE":
        max_size_mb = details.get("max_size_mb", 100)
        result["message"] = f"Your file is too large to upload. The maximum size is {max_size_mb}MB."
    
    elif details and error_code == "UNSUPPORTED_FORMAT":
        provided_format = details.get("provided_format", "unknown")
        result["message"] = f"The format '{provided_format}' isn't supported. Please use WAV, MP3, M4A, FLAC, or WebM format."
    
    elif details and error_code == "AUDIO_TOO_SHORT":
        min_duration = details.get("min_duration", 1)
        result["message"] = f"Your recording is too short. Please record for at least {min_duration} seconds."
    
    elif details and error_code == "AUDIO_TOO_LONG":
        max_duration = details.get("max_duration", 1800)
        max_minutes = max_duration // 60
        result["message"] = f"Your recording is too long. Please keep recordings under {max_minutes} minutes."
    
    return result


def get_fallback_response(operation: str) -> Dict[str, Any]:
    """
    Get fallback response when primary operation fails.
    
    Args:
        operation: The operation that failed
        
    Returns:
        Fallback response with alternative actions
    """
    fallbacks = {
        "audio_upload": {
            "message": "Upload failed, but you can try these alternatives:",
            "alternatives": [
                {
                    "action": "retry",
                    "description": "Try uploading again",
                    "immediate": True
                },
                {
                    "action": "compress",
                    "description": "Compress your audio file and try again",
                    "immediate": False
                },
                {
                    "action": "different_format",
                    "description": "Convert to WAV format and try again",
                    "immediate": False
                },
                {
                    "action": "contact_support",
                    "description": "Contact support for help",
                    "immediate": False
                }
            ]
        },
        "audio_processing": {
            "message": "Processing failed, but your file was saved. We'll try again automatically.",
            "alternatives": [
                {
                    "action": "auto_retry",
                    "description": "Automatic retry in progress",
                    "immediate": True
                },
                {
                    "action": "manual_retry",
                    "description": "Manually trigger processing again",
                    "immediate": True
                },
                {
                    "action": "reupload",
                    "description": "Upload a new recording",
                    "immediate": False
                }
            ]
        },
        "transcription": {
            "message": "Transcription failed, but you can try alternatives:",
            "alternatives": [
                {
                    "action": "skip_chunk",
                    "description": "Skip this audio chunk",
                    "immediate": True
                },
                {
                    "action": "retry_later",
                    "description": "Try transcribing this chunk later",
                    "immediate": False
                },
                {
                    "action": "report_issue",
                    "description": "Report audio quality issue",
                    "immediate": True
                }
            ]
        },
        "consensus": {
            "message": "Consensus calculation failed, but transcriptions were saved:",
            "alternatives": [
                {
                    "action": "manual_review",
                    "description": "Manual review will be performed",
                    "immediate": False
                },
                {
                    "action": "retry_consensus",
                    "description": "Retry consensus calculation",
                    "immediate": True
                }
            ]
        }
    }
    
    return fallbacks.get(operation, {
        "message": "Operation failed, but you can try again or contact support.",
        "alternatives": [
            {
                "action": "retry",
                "description": "Try again",
                "immediate": True
            },
            {
                "action": "contact_support",
                "description": "Contact support for help",
                "immediate": False
            }
        ]
    })


def create_error_response_with_fallback(
    error_code: str,
    operation: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create comprehensive error response with user-friendly message and fallback options.
    
    Args:
        error_code: Error code for the specific error
        operation: The operation that failed
        details: Additional error details
        
    Returns:
        Complete error response with message and fallback options
    """
    error_info = get_user_friendly_error(error_code, details)
    fallback_info = get_fallback_response(operation)
    
    return {
        "error": {
            "code": error_code,
            "title": error_info["title"],
            "message": error_info["message"],
            "suggestions": error_info["suggestions"]
        },
        "fallback": fallback_info,
        "support": {
            "contact_email": "support@voicecollection.com",
            "help_url": "/help",
            "status_page": "/status"
        }
    }