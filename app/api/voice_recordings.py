from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_active_user, require_admin_or_sworik
from app.models.user import User
from app.models.voice_recording import RecordingStatus
from app.schemas.voice_recording import (
    RecordingSessionCreate, RecordingSessionResponse, RecordingUploadRequest,
    VoiceRecordingResponse, VoiceRecordingListResponse, RecordingProgressResponse,
    RecordingStatistics
)
from app.services.voice_recording_service import VoiceRecordingService
import json

router = APIRouter(prefix="/recordings", tags=["voice-recordings"])


@router.post("/sessions", response_model=RecordingSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_recording_session(
    session_data: RecordingSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new recording session for a script.
    
    This endpoint creates a recording session that associates a user with a script
    for voice recording. The session has a 2-hour timeout and provides the script
    text and metadata needed for recording.
    """
    recording_service = VoiceRecordingService(db)
    return recording_service.create_recording_session(current_user.id, session_data)


@router.post("/upload", response_model=VoiceRecordingResponse, status_code=status.HTTP_201_CREATED)
async def upload_recording(
    audio_file: UploadFile = File(..., description="Audio file to upload"),
    session_id: str = Form(..., description="Recording session ID"),
    duration: float = Form(..., description="Recording duration in seconds"),
    audio_format: str = Form(..., description="Audio format (wav, mp3, m4a, flac, webm)"),
    file_size: int = Form(..., description="File size in bytes"),
    sample_rate: Optional[int] = Form(None, description="Sample rate in Hz"),
    channels: Optional[int] = Form(None, description="Number of audio channels"),
    bit_depth: Optional[int] = Form(None, description="Audio bit depth"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Upload a voice recording for processing.
    
    This endpoint accepts audio files and associated metadata, validates the file,
    stores it securely, and creates a database record for further processing.
    The recording will be queued for intelligent chunking.
    """
    # Validate content type
    if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
        from app.core.logging_config import get_logger
        logger = get_logger(__name__)
        logger.warning(
            f"Invalid content type for audio upload: {audio_file.content_type}",
            extra={
                "user_id": current_user.id,
                "filename": audio_file.filename,
                "content_type": audio_file.content_type
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an audio file"
        )
    
    # Create upload request object
    upload_data = RecordingUploadRequest(
        session_id=session_id,
        duration=duration,
        audio_format=audio_format,
        sample_rate=sample_rate,
        channels=channels,
        bit_depth=bit_depth,
        file_size=file_size
    )
    
    recording_service = VoiceRecordingService(db)
    return recording_service.upload_recording(current_user.id, upload_data, audio_file)


@router.get("/", response_model=VoiceRecordingListResponse)
async def get_user_recordings(
    skip: int = Query(0, ge=0, description="Number of recordings to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of recordings to return"),
    status: Optional[RecordingStatus] = Query(None, description="Filter by recording status"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of current user's recordings.
    
    Returns recordings ordered by creation date (newest first) with optional
    status filtering and pagination support.
    """
    recording_service = VoiceRecordingService(db)
    return recording_service.get_user_recordings(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status
    )


@router.get("/{recording_id}", response_model=VoiceRecordingResponse)
async def get_recording(
    recording_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific recording by ID.
    
    Users can only access their own recordings unless they have admin privileges.
    """
    recording_service = VoiceRecordingService(db)
    
    # Regular users can only access their own recordings
    user_id = current_user.id if current_user.role not in ["admin", "sworik_developer"] else None
    
    recording = recording_service.get_recording_by_id(recording_id, user_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    return VoiceRecordingResponse.model_validate(recording)


@router.get("/{recording_id}/progress", response_model=RecordingProgressResponse)
async def get_recording_progress(
    recording_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get processing progress for a recording.
    
    Returns the current processing status and progress percentage for tracking
    the chunking and validation pipeline.
    """
    recording_service = VoiceRecordingService(db)
    
    # Verify user has access to this recording
    user_id = current_user.id if current_user.role not in ["admin", "sworik_developer"] else None
    recording = recording_service.get_recording_by_id(recording_id, user_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    return recording_service.get_recording_progress(recording_id)


@router.delete("/{recording_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recording(
    recording_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a recording and its associated file.
    
    Users can only delete their own recordings. Recordings that have been
    processed into chunks cannot be deleted without first removing the chunks.
    """
    recording_service = VoiceRecordingService(db)
    
    # Regular users can only delete their own recordings
    user_id = current_user.id if current_user.role not in ["admin", "sworik_developer"] else None
    
    recording_service.delete_recording(recording_id, user_id)
    return None


# Admin endpoints
@router.get("/admin/all", response_model=VoiceRecordingListResponse)
async def get_all_recordings(
    skip: int = Query(0, ge=0, description="Number of recordings to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of recordings to return"),
    status: Optional[RecordingStatus] = Query(None, description="Filter by recording status"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of all recordings (admin only).
    
    Available to admins and Sworik developers for monitoring and management.
    Supports filtering by status and user ID.
    """
    recording_service = VoiceRecordingService(db)
    
    if user_id:
        return recording_service.get_user_recordings(
            user_id=user_id,
            skip=skip,
            limit=limit,
            status=status
        )
    else:
        # Get all recordings across all users
        # This would need to be implemented in the service
        # For now, return empty response
        return VoiceRecordingListResponse(
            recordings=[],
            total=0,
            page=1,
            per_page=limit,
            total_pages=0
        )


@router.get("/admin/statistics", response_model=RecordingStatistics)
async def get_recording_statistics(
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Get statistics about recordings in the database.
    
    Available to admins and Sworik developers for monitoring and reporting.
    Includes counts by status, duration category, language, and duration metrics.
    """
    recording_service = VoiceRecordingService(db)
    return recording_service.get_recording_statistics()


@router.patch("/{recording_id}/status")
async def update_recording_status(
    recording_id: int,
    new_status: RecordingStatus,
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Update recording status (admin only).
    
    Available to admins and Sworik developers for manual status management
    and troubleshooting processing issues.
    """
    recording_service = VoiceRecordingService(db)
    
    recording = recording_service.update_recording_status(
        recording_id=recording_id,
        status=new_status,
        meta_data_update={"status_updated_by": current_user.id}
    )
    
    return VoiceRecordingResponse.model_validate(recording)


@router.post("/{recording_id}/process")
async def trigger_audio_processing(
    recording_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually trigger audio processing for a recording.
    
    This endpoint allows users to manually trigger the audio chunking process
    for their recordings, or admins to reprocess failed recordings.
    """
    recording_service = VoiceRecordingService(db)
    
    # Verify user has access to this recording
    user_id = current_user.id if current_user.role not in ["admin", "sworik_developer"] else None
    recording = recording_service.get_recording_by_id(recording_id, user_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Check if recording is in a processable state
    if recording.status not in [RecordingStatus.UPLOADED, RecordingStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Recording cannot be processed in current status: {recording.status}"
        )
    
    # Trigger processing
    recording_service._trigger_audio_processing(recording_id)
    
    return {
        "message": "Audio processing triggered successfully",
        "recording_id": recording_id,
        "status": "queued"
    }


@router.get("/{recording_id}/processing-status")
async def get_processing_status(
    recording_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed processing status for a recording.
    
    Returns information about the background processing task including
    current status, progress, and any error messages.
    """
    recording_service = VoiceRecordingService(db)
    
    # Verify user has access to this recording
    user_id = current_user.id if current_user.role not in ["admin", "sworik_developer"] else None
    recording = recording_service.get_recording_by_id(recording_id, user_id)
    if not recording:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found"
        )
    
    # Get task status
    task_status = recording_service.get_processing_task_status(recording_id)
    
    return {
        "recording_id": recording_id,
        "recording_status": recording.status,
        "task_status": task_status,
        "chunks_created": len(recording.audio_chunks) if recording.audio_chunks else 0
    }


# Admin endpoints for batch processing
@router.post("/admin/batch-process")
async def batch_process_recordings(
    recording_ids: list[int],
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Process multiple recordings in batch (admin only).
    
    Triggers audio processing for multiple recordings simultaneously.
    Useful for bulk processing of uploaded recordings.
    """
    from app.tasks.audio_processing import batch_process_recordings as batch_task
    
    # Validate all recording IDs exist
    recording_service = VoiceRecordingService(db)
    valid_recordings = []
    
    for recording_id in recording_ids:
        recording = recording_service.get_recording_by_id(recording_id)
        if recording:
            valid_recordings.append(recording_id)
    
    if not valid_recordings:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid recordings found"
        )
    
    # Trigger batch processing
    task = batch_task.delay(valid_recordings)
    
    return {
        "message": f"Batch processing triggered for {len(valid_recordings)} recordings",
        "task_id": task.id,
        "recording_ids": valid_recordings
    }


@router.post("/admin/reprocess-failed")
async def reprocess_failed_recordings(
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Reprocess all failed recordings (admin only).
    
    Finds all recordings with failed status and attempts to reprocess them.
    Useful for recovering from system issues or processing improvements.
    """
    from app.tasks.audio_processing import reprocess_failed_recordings as reprocess_task
    
    # Trigger reprocessing
    task = reprocess_task.delay()
    
    return {
        "message": "Failed recordings reprocessing triggered",
        "task_id": task.id
    }


@router.post("/admin/cleanup-orphaned-chunks")
async def cleanup_orphaned_chunks(
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Clean up orphaned audio chunk files (admin only).
    
    Removes audio chunk files that don't have corresponding database records.
    Useful for cleaning up after failed processing or data corruption.
    """
    from app.tasks.audio_processing import cleanup_orphaned_chunks as cleanup_task
    
    # Trigger cleanup
    task = cleanup_task.delay()
    
    return {
        "message": "Orphaned chunks cleanup triggered",
        "task_id": task.id
    }