"""
Comprehensive logging configuration for the Voice Data Collection Platform.

This module provides structured logging with appropriate log levels, formatters,
and handlers for different environments (development, production).
"""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict

from app.core.config import settings


def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration dictionary for the application.

    Returns structured logging configuration with different handlers
    for console and file output, appropriate formatters, and log levels
    based on the environment.
    """

    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Determine log level based on environment
    log_level = "DEBUG" if settings.DEBUG else "INFO"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s - %(name)s - %(message)s"},
            "json": {
                "()": "app.core.logging_config.JSONFormatter",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "detailed",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "app.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(log_dir / "errors.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
            "audio_processing": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "detailed",
                "filename": str(log_dir / "audio_processing.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "security": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "WARNING",
                "formatter": "json",
                "filename": str(log_dir / "security.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
            "export_operations": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(log_dir / "export_operations.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
            "consensus_operations": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": str(log_dir / "consensus_operations.log"),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
        },
        "loggers": {
            # Root logger
            "": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # Application loggers
            "app": {
                "level": log_level,
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # Audio processing specific logger
            "app.services.audio_processing_service": {
                "level": "INFO",
                "handlers": ["console", "audio_processing", "error_file"],
                "propagate": False,
            },
            "app.tasks.audio_processing": {
                "level": "INFO",
                "handlers": ["console", "audio_processing", "error_file"],
                "propagate": False,
            },
            # Security logger for authentication and authorization
            "app.core.security": {
                "level": "WARNING",
                "handlers": ["console", "security", "error_file"],
                "propagate": False,
            },
            "app.core.middleware": {
                "level": "WARNING",
                "handlers": ["console", "security", "error_file"],
                "propagate": False,
            },
            # Export operations logger
            "app.services.export_batch_service": {
                "level": "INFO",
                "handlers": ["console", "export_operations", "error_file"],
                "propagate": False,
            },
            "app.tasks.export_optimization": {
                "level": "INFO",
                "handlers": ["console", "export_operations", "error_file"],
                "propagate": False,
            },
            # Consensus operations logger
            "app.services.consensus_service": {
                "level": "INFO",
                "handlers": ["console", "consensus_operations", "error_file"],
                "propagate": False,
            },
            # Database logger
            "app.db": {
                "level": "WARNING",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            # Third-party loggers
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console", "file"],
                "propagate": False,
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["console", "error_file"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["file"],
                "propagate": False,
            },
            "sqlalchemy.engine": {
                "level": "WARNING",
                "handlers": ["file", "error_file"],
                "propagate": False,
            },
            "celery": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "redis": {
                "level": "WARNING",
                "handlers": ["file", "error_file"],
                "propagate": False,
            },
        },
    }

    return config


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Formats log records as JSON objects with consistent fields
    for better log analysis and monitoring.
    """

    def format(self, record: logging.LogRecord) -> str:
        import json
        from datetime import datetime

        # Create base log entry
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_entry["ip_address"] = record.ip_address
        if hasattr(record, "user_agent"):
            log_entry["user_agent"] = record.user_agent

        # Export operation specific fields
        if hasattr(record, "batch_id"):
            log_entry["batch_id"] = record.batch_id
        if hasattr(record, "chunk_count"):
            log_entry["chunk_count"] = record.chunk_count
        if hasattr(record, "chunk_ids"):
            log_entry["chunk_ids"] = record.chunk_ids
        if hasattr(record, "operation_type"):
            log_entry["operation_type"] = record.operation_type
        if hasattr(record, "storage_type"):
            log_entry["storage_type"] = record.storage_type
        if hasattr(record, "file_size_bytes"):
            log_entry["file_size_bytes"] = record.file_size_bytes
        if hasattr(record, "duration_seconds"):
            log_entry["duration_seconds"] = record.duration_seconds

        # R2 operation specific fields
        if hasattr(record, "r2_operation_class"):
            log_entry["r2_operation_class"] = record.r2_operation_class
        if hasattr(record, "r2_object_key"):
            log_entry["r2_object_key"] = record.r2_object_key

        # Consensus operation specific fields
        if hasattr(record, "consensus_quality"):
            log_entry["consensus_quality"] = record.consensus_quality
        if hasattr(record, "transcript_count"):
            log_entry["transcript_count"] = record.transcript_count
        if hasattr(record, "ready_for_export"):
            log_entry["ready_for_export"] = record.ready_for_export

        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging():
    """
    Set up logging configuration for the application.

    This function should be called once at application startup
    to configure all loggers with the appropriate handlers and formatters.
    """
    config = get_logging_config()
    logging.config.dictConfig(config)

    # Log startup message
    logger = logging.getLogger("app.core.logging_config")
    logger.info("Logging configuration initialized successfully")
    logger.info(f"Log level: {'DEBUG' if settings.DEBUG else 'INFO'}")
    logger.info(f"Log files location: {Path('logs').absolute()}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name, typically __name__ from the calling module

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter for adding contextual information to log records.

    This adapter allows adding request-specific information like user ID,
    request ID, and IP address to all log messages within a request context.
    """

    def process(self, msg, kwargs):
        """Add extra context to log records."""
        return msg, kwargs
