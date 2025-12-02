"""
System Monitoring and Logging API

This module provides endpoints for system monitoring, logging, and performance metrics.
All endpoints require admin privileges for security.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.cache import cache_manager
from app.core.dependencies import require_admin, require_admin_or_sworik
from app.core.performance import performance_metrics, performance_optimizer
from app.core.rate_limiting import rate_limit_manager
from app.db.database import get_db
from app.models.user import User

router = APIRouter(prefix="/system", tags=["system"])


# Health and Status Endpoints
@router.get("/health")
async def get_system_health(current_user: User = Depends(require_admin_or_sworik)):
    """Get comprehensive system health metrics."""
    from app.core.logging_config import get_logger
    from app.core.monitoring import run_health_check

    logger = get_logger(__name__)

    try:
        health_status = await run_health_check()
        logger.info(f"System health check requested by user {current_user.id}")
        return health_status
    except Exception as e:
        logger.error(f"System health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health status",
        )


@router.get("/metrics")
async def get_system_metrics(current_user: User = Depends(require_admin_or_sworik)):
    """Get detailed system metrics."""
    from app.core.logging_config import get_logger
    from app.core.monitoring import get_system_metrics

    logger = get_logger(__name__)

    try:
        metrics = await get_system_metrics()
        logger.info(f"System metrics requested by user {current_user.id}")
        return {
            "timestamp": metrics.timestamp.isoformat(),
            "cpu_percent": metrics.cpu_percent,
            "memory_percent": metrics.memory_percent,
            "disk_percent": metrics.disk_percent,
            "active_connections": metrics.active_connections,
            "redis_connected": metrics.redis_connected,
            "database_connected": metrics.database_connected,
            "celery_workers": metrics.celery_workers,
            "queue_size": metrics.queue_size,
            "error_rate": metrics.error_rate,
            "response_time_avg": metrics.response_time_avg,
        }
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics",
        )


@router.get("/alerts")
async def get_recent_alerts(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get recent system alerts."""
    from app.core.logging_config import get_logger
    from app.core.monitoring import health_checker

    logger = get_logger(__name__)

    try:
        alerts = await health_checker.get_recent_alerts(limit=limit)
        logger.info(f"System alerts requested by user {current_user.id}")
        return {"alerts": alerts, "total_count": len(alerts)}
    except Exception as e:
        logger.error(f"Failed to get system alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system alerts",
        )


# Logging Endpoints
@router.get("/logs")
async def get_system_logs(
    log_type: str = Query(
        "app", description="Log type: app, errors, audio_processing, security"
    ),
    level: str = Query(
        "INFO", description="Log level filter: DEBUG, INFO, WARNING, ERROR"
    ),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_admin),
):
    """Get system logs (admin only)."""
    try:
        # Define available log files
        log_files = {
            "app": "logs/app.log",
            "errors": "logs/errors.log",
            "audio_processing": "logs/audio_processing.log",
            "security": "logs/security.log",
        }

        if log_type not in log_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log type. Available: {list(log_files.keys())}",
            )

        log_file_path = Path(log_files[log_type])

        if not log_file_path.exists():
            return {
                "logs": [],
                "total_count": 0,
                "log_type": log_type,
                "message": f"Log file {log_file_path} not found",
            }

        # Read log file
        logs = []
        total_lines = 0

        with open(log_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            total_lines = len(lines)

            # Get last N lines (most recent first)
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            recent_lines.reverse()  # Most recent first

            for line in recent_lines:
                line = line.strip()
                if not line:
                    continue

                try:
                    # Try to parse as JSON (for structured logs)
                    if line.startswith("{"):
                        log_entry = json.loads(line)
                        # Filter by log level if specified
                        if (
                            level != "ALL"
                            and log_entry.get("level", "").upper() != level.upper()
                        ):
                            continue
                        logs.append(log_entry)
                    else:
                        # Parse plain text logs
                        parts = line.split(" - ", 4)
                        if len(parts) >= 4:
                            log_entry = {
                                "timestamp": parts[0],
                                "logger": parts[1],
                                "level": parts[2],
                                "message": (
                                    " - ".join(parts[3:])
                                    if len(parts) > 4
                                    else parts[3]
                                ),
                                "raw": line,
                            }
                            # Filter by log level
                            if (
                                level != "ALL"
                                and log_entry.get("level", "").upper() != level.upper()
                            ):
                                continue
                            logs.append(log_entry)
                        else:
                            # Fallback for unparseable lines
                            logs.append(
                                {
                                    "timestamp": datetime.now().isoformat(),
                                    "level": "UNKNOWN",
                                    "message": line,
                                    "raw": line,
                                }
                            )
                except json.JSONDecodeError:
                    # Handle malformed JSON
                    logs.append(
                        {
                            "timestamp": datetime.now().isoformat(),
                            "level": "UNKNOWN",
                            "message": line,
                            "raw": line,
                        }
                    )

        return {
            "logs": logs,
            "total_count": len(logs),
            "total_lines_in_file": total_lines,
            "log_type": log_type,
            "log_level_filter": level,
            "log_file": str(log_file_path),
            "file_size_mb": round(log_file_path.stat().st_size / (1024 * 1024), 2),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read logs: {str(e)}",
        )


@router.get("/logs/files")
async def get_log_files(current_user: User = Depends(require_admin)):
    """Get available log files and their information (admin only)."""
    try:
        log_dir = Path("logs")

        if not log_dir.exists():
            return {"log_files": [], "message": "Logs directory not found"}

        log_files = []

        for log_file in log_dir.glob("*.log"):
            try:
                stat = log_file.stat()
                log_files.append(
                    {
                        "name": log_file.name,
                        "path": str(log_file),
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "size_bytes": stat.st_size,
                        "modified": stat.st_mtime,
                        "created": stat.st_ctime,
                        "readable": os.access(log_file, os.R_OK),
                    }
                )
            except Exception as e:
                log_files.append(
                    {"name": log_file.name, "path": str(log_file), "error": str(e)}
                )

        return {
            "log_files": sorted(
                log_files, key=lambda x: x.get("modified", 0), reverse=True
            ),
            "total_files": len(log_files),
            "log_directory": str(log_dir.absolute()),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list log files: {str(e)}",
        )


@router.delete("/logs/{log_type}")
async def clear_log_file(log_type: str, current_user: User = Depends(require_admin)):
    """Clear a specific log file (admin only)."""
    try:
        # Define available log files
        log_files = {
            "app": "logs/app.log",
            "errors": "logs/errors.log",
            "audio_processing": "logs/audio_processing.log",
            "security": "logs/security.log",
        }

        if log_type not in log_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid log type. Available: {list(log_files.keys())}",
            )

        log_file_path = Path(log_files[log_type])

        if log_file_path.exists():
            # Clear the file by truncating it
            with open(log_file_path, "w") as f:
                f.truncate(0)

            return {
                "message": f"Log file {log_type} cleared successfully",
                "log_file": str(log_file_path),
                "cleared_by": current_user.email,
            }
        else:
            return {
                "message": f"Log file {log_type} does not exist",
                "log_file": str(log_file_path),
            }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear log file: {str(e)}",
        )


# Performance Monitoring Endpoints
@router.get("/performance/dashboard")
async def get_performance_dashboard(
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get comprehensive performance dashboard data."""
    try:
        dashboard_data = performance_optimizer.get_performance_dashboard()
        return dashboard_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance dashboard: {str(e)}",
        )


@router.get("/performance/endpoints")
async def get_endpoint_performance(
    endpoint: Optional[str] = Query(None, description="Filter by specific endpoint"),
    days: int = Query(1, ge=1, le=7, description="Number of days to analyze"),
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get performance metrics for API endpoints."""
    try:
        if endpoint:
            metrics = performance_metrics.get_endpoint_metrics(endpoint, "GET", days)
            return {"endpoint_metrics": [metrics]}
        else:
            # Get metrics for common endpoints
            common_endpoints = [
                "/api/transcriptions/tasks",
                "/api/transcriptions/submit",
                "/api/recordings/upload",
                "/api/chunks/{chunk_id}/audio",
                "/api/auth/login",
            ]

            all_metrics = []
            for ep in common_endpoints:
                metrics = performance_metrics.get_endpoint_metrics(ep, "GET", days)
                all_metrics.append(metrics)

            return {"endpoint_metrics": all_metrics}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get endpoint performance: {str(e)}",
        )


@router.get("/performance/cache")
async def get_cache_performance(current_user: User = Depends(require_admin_or_sworik)):
    """Get cache performance metrics and optimization recommendations."""
    try:
        cache_stats = performance_optimizer.optimize_cache_settings()

        # Add cache size information
        cache_info = {
            "redis_connected": cache_manager.redis.ping(),
            "cache_keys_count": (
                len(cache_manager.redis.client.keys("*"))
                if cache_manager.redis.ping()
                else 0
            ),
        }

        return {"cache_optimization": cache_stats, "cache_info": cache_info}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache performance: {str(e)}",
        )


@router.get("/performance/database")
async def get_database_performance(
    current_user: User = Depends(require_admin_or_sworik),
):
    """Get database performance metrics."""
    try:
        from app.core.performance import query_optimizer
        from app.db.database import get_connection_pool_status

        pool_status = get_connection_pool_status()
        query_report = query_optimizer.get_query_performance_report()

        return {"connection_pool": pool_status, "query_performance": query_report}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get database performance: {str(e)}",
        )


@router.get("/performance/rate-limits")
async def get_rate_limit_stats(current_user: User = Depends(require_admin_or_sworik)):
    """Get rate limiting statistics."""
    try:
        stats = rate_limit_manager.get_rate_limit_statistics()
        return {"rate_limit_stats": stats}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit stats: {str(e)}",
        )


# Cache Management Endpoints
@router.post("/cache/clear")
async def clear_cache(
    cache_type: str = Query(
        "all", description="Type of cache to clear (all, api, db, stats)"
    ),
    current_user: User = Depends(require_admin),
):
    """Clear cache (admin only)."""
    try:
        if cache_type == "all":
            cache_manager.redis.client.flushdb()
            message = "All caches cleared"
        elif cache_type == "api":
            from app.core.cache import api_cache

            api_cache.cache.delete_pattern("api_response:*")
            message = "API response cache cleared"
        elif cache_type == "db":
            from app.core.cache import db_cache

            db_cache.cache.delete_pattern("db_query:*")
            message = "Database query cache cleared"
        elif cache_type == "stats":
            from app.core.cache import stats_cache

            stats_cache.invalidate_statistics()
            message = "Statistics cache cleared"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid cache type"
            )

        return {"message": message}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}",
        )


@router.post("/rate-limits/{user_id}/reset")
async def reset_user_rate_limit(
    user_id: int, current_user: User = Depends(require_admin)
):
    """Reset rate limits for a specific user (admin only)."""
    try:
        success = rate_limit_manager.reset_user_rate_limit(user_id)

        if success:
            return {"message": f"Rate limits reset for user {user_id}"}
        else:
            return {"message": f"No rate limits found for user {user_id}"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset rate limits: {str(e)}",
        )


# CDN Status
@router.get("/cdn")
async def get_cdn_status(current_user: User = Depends(require_admin_or_sworik)):
    """Get CDN status and configuration."""
    try:
        from app.core.cdn import cdn_manager

        cdn_status = {
            "enabled": cdn_manager.config.is_cdn_enabled(),
            "base_url": cdn_manager.config.CDN_BASE_URL,
            "provider": cdn_manager.config.CDN_PROVIDER,
            "audio_cache_ttl": cdn_manager.config.AUDIO_CACHE_TTL,
            "static_cache_ttl": cdn_manager.config.STATIC_CACHE_TTL,
        }

        return {"cdn_status": cdn_status}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get CDN status: {str(e)}",
        )


# Storage Information
@router.get("/storage")
async def get_storage_info(current_user: User = Depends(require_admin_or_sworik)):
    """Get storage usage information."""
    try:
        import shutil
        from pathlib import Path

        # Calculate storage usage
        upload_dir = Path("uploads")
        logs_dir = Path("logs")

        storage_info = {
            "upload_directory": {
                "path": str(upload_dir.absolute()),
                "exists": upload_dir.exists(),
                "size_mb": 0,
                "file_count": 0,
            },
            "logs_directory": {
                "path": str(logs_dir.absolute()),
                "exists": logs_dir.exists(),
                "size_mb": 0,
                "file_count": 0,
            },
        }

        # Calculate upload directory size
        if upload_dir.exists():
            total_size = sum(
                f.stat().st_size for f in upload_dir.rglob("*") if f.is_file()
            )
            file_count = sum(1 for f in upload_dir.rglob("*") if f.is_file())
            storage_info["upload_directory"]["size_mb"] = round(
                total_size / (1024 * 1024), 2
            )
            storage_info["upload_directory"]["file_count"] = file_count

        # Calculate logs directory size
        if logs_dir.exists():
            total_size = sum(
                f.stat().st_size for f in logs_dir.rglob("*") if f.is_file()
            )
            file_count = sum(1 for f in logs_dir.rglob("*") if f.is_file())
            storage_info["logs_directory"]["size_mb"] = round(
                total_size / (1024 * 1024), 2
            )
            storage_info["logs_directory"]["file_count"] = file_count

        # Get disk usage for the current directory
        disk_usage = shutil.disk_usage(".")
        storage_info["disk_usage"] = {
            "total_gb": round(disk_usage.total / (1024**3), 2),
            "used_gb": round((disk_usage.total - disk_usage.free) / (1024**3), 2),
            "available_gb": round(disk_usage.free / (1024**3), 2),
            "usage_percent": round(
                ((disk_usage.total - disk_usage.free) / disk_usage.total) * 100, 2
            ),
        }

        return storage_info

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage info: {str(e)}",
        )
