from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uuid
import logging

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.core.exceptions import (
    VoiceCollectionError,
    custom_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.core.monitoring import MonitoringMiddleware, run_health_check
from app.core.middleware import AuthContextMiddleware
from app.api.auth import router as auth_router
from app.api.scripts import router as scripts_router
from app.api.voice_recordings import router as voice_recordings_router
from app.api.transcriptions import router as transcriptions_router
from app.api.chunks import router as chunks_router
from app.api.consensus import router as consensus_router
from app.api.admin import router as admin_router
from app.api.export import router as export_router
from app.api.jobs import router as jobs_router

# Import all models to ensure they're registered with SQLAlchemy
import app.models

# Setup logging before creating the app
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Voice Data Collection Platform",
    description="Crowdsourcing platform for Bangla voice recordings and transcriptions",
    version="1.0.0"
)

# Add request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to each request for tracing."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request start
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "user_agent": request.headers.get("user-agent"),
            "ip_address": request.client.host if request.client else None
        }
    )
    
    response = await call_next(request)
    
    # Log request completion
    logger.info(
        f"Request completed: {request.method} {request.url.path} - {response.status_code}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code
        }
    )
    
    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id
    return response

# Add monitoring middleware
app.add_middleware(MonitoringMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.add_middleware(AuthContextMiddleware)

# Add exception handlers
app.add_exception_handler(VoiceCollectionError, custom_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(auth_router, prefix="/api")
app.include_router(scripts_router, prefix="/api")
app.include_router(voice_recordings_router, prefix="/api")
app.include_router(transcriptions_router, prefix="/api")
app.include_router(chunks_router, prefix="/api")
app.include_router(consensus_router)
app.include_router(admin_router, prefix="/api")
app.include_router(export_router)
app.include_router(jobs_router, prefix="/api")

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Voice Data Collection Platform API"}

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        health_status = await run_health_check()
        logger.info(f"Health check completed: {health_status['status']}")
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": "Health check failed",
            "error": str(e)
        }

@app.on_event("startup")
async def startup_event():
    """Application startup event handler."""
    logger.info("Voice Data Collection Platform starting up...")
    logger.info(f"Environment: {'Development' if settings.DEBUG else 'Production'}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    logger.info(f"Redis URL: {settings.REDIS_URL}")
    logger.info(f"Celery enabled: {settings.USE_CELERY}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler."""
    logger.info("Voice Data Collection Platform shutting down...")
    # Perform cleanup tasks here if needed