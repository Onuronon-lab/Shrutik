from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
import os
from app.db.database import get_db
from app.core.dependencies import get_current_active_user, require_admin_or_sworik
from app.models.user import User
from app.schemas.transcription import (
    TranscriptionTaskRequest, TranscriptionTaskResponse, TranscriptionSubmission,
    TranscriptionSubmissionResponse, TranscriptionListResponse, TranscriptionResponse,
    TranscriptionUpdate, TranscriptionStatistics, ChunkSkipRequest, ChunkSkipResponse
)
from app.services.transcription_service import TranscriptionService

router = APIRouter(prefix="/transcriptions", tags=["transcriptions"])


@router.post("/tasks", response_model=TranscriptionTaskResponse, status_code=status.HTTP_200_OK)
@performance_monitor.monitor_endpoint("transcription_tasks")
async def get_transcription_task(
    task_request: TranscriptionTaskRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get random untranscribed audio chunks for transcription.
    
    This endpoint serves random audio chunks based on the requested quantity.
    Users can specify language preference and chunks to skip. The response
    includes a session ID for tracking the transcription batch.
    """
    from app.core.performance import performance_monitor
    
    transcription_service = TranscriptionService(db)
    return transcription_service.get_random_chunks_for_transcription(current_user.id, task_request)


@router.post("/submit", response_model=TranscriptionSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_transcriptions(
    submission: TranscriptionSubmission,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Submit transcriptions for audio chunks.
    
    This endpoint accepts transcriptions for chunks from a transcription task session.
    It validates the session, prevents duplicate transcriptions by the same user,
    and triggers consensus calculation for the affected chunks.
    """
    transcription_service = TranscriptionService(db)
    return transcription_service.submit_transcriptions(current_user.id, submission)


@router.post("/skip", response_model=ChunkSkipResponse, status_code=status.HTTP_200_OK)
async def skip_chunk(
    skip_request: ChunkSkipRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Skip a difficult or unclear audio chunk.
    
    This endpoint allows users to skip chunks that are too difficult to transcribe,
    such as those with poor audio quality or unclear speech. The skip is recorded
    for analytics and to potentially flag problematic chunks.
    """
    transcription_service = TranscriptionService(db)
    return transcription_service.skip_chunk(current_user.id, skip_request)


@router.get("/", response_model=TranscriptionListResponse)
@performance_monitor.monitor_endpoint("user_transcriptions")
async def get_user_transcriptions(
    skip: int = Query(0, ge=0, description="Number of transcriptions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transcriptions to return"),
    language_id: Optional[int] = Query(None, description="Filter by language ID"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of current user's transcriptions.
    
    Returns transcriptions ordered by creation date (newest first) with optional
    language filtering and pagination support.
    """
    transcription_service = TranscriptionService(db)
    return transcription_service.get_user_transcriptions(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        language_id=language_id
    )


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
async def get_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific transcription by ID.
    
    Users can only access their own transcriptions unless they have admin privileges.
    """
    transcription_service = TranscriptionService(db)
    
    # Regular users can only access their own transcriptions
    user_id = current_user.id if current_user.role not in ["admin", "sworik_developer"] else None
    
    transcription = transcription_service.get_transcription_by_id(transcription_id, user_id)
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    return TranscriptionResponse.model_validate(transcription)


@router.patch("/{transcription_id}", response_model=TranscriptionResponse)
async def update_transcription(
    transcription_id: int,
    update_data: TranscriptionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing transcription.
    
    Users can only update their own transcriptions unless they have admin privileges.
    This endpoint allows for correcting transcription text, updating quality scores,
    or modifying metadata.
    """
    transcription_service = TranscriptionService(db)
    
    # Regular users can only update their own transcriptions
    user_id = current_user.id if current_user.role not in ["admin", "sworik_developer"] else None
    
    transcription = transcription_service.update_transcription(
        transcription_id=transcription_id,
        update_data=update_data,
        user_id=user_id
    )
    
    return TranscriptionResponse.model_validate(transcription)


@router.delete("/{transcription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transcription(
    transcription_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a transcription.
    
    Users can only delete their own transcriptions unless they have admin privileges.
    Deleting a transcription may affect consensus calculations for the associated chunk.
    """
    transcription_service = TranscriptionService(db)
    
    # Regular users can only delete their own transcriptions
    user_id = current_user.id if current_user.role not in ["admin", "sworik_developer"] else None
    
    transcription = transcription_service.get_transcription_by_id(transcription_id, user_id)
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    # Delete the transcription
    transcription_service.db.delete(transcription)
    transcription_service.db.commit()
    
    # Trigger consensus recalculation for the affected chunk
    transcription_service._trigger_consensus_calculation([transcription.chunk_id])
    
    return None


# Admin endpoints
@router.get("/admin/all", response_model=TranscriptionListResponse)
async def get_all_transcriptions(
    skip: int = Query(0, ge=0, description="Number of transcriptions to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of transcriptions to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    language_id: Optional[int] = Query(None, description="Filter by language ID"),
    is_consensus: Optional[bool] = Query(None, description="Filter by consensus status"),
    is_validated: Optional[bool] = Query(None, description="Filter by validation status"),
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of all transcriptions (admin only).
    
    Available to admins and Sworik developers for monitoring and management.
    Supports filtering by user, language, consensus status, and validation status.
    """
    from app.models.transcription import Transcription
    
    query = db.query(Transcription)
    
    # Apply filters
    filters = []
    if user_id:
        filters.append(Transcription.user_id == user_id)
    if language_id:
        filters.append(Transcription.language_id == language_id)
    if is_consensus is not None:
        filters.append(Transcription.is_consensus == is_consensus)
    if is_validated is not None:
        filters.append(Transcription.is_validated == is_validated)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    transcriptions = query.order_by(Transcription.created_at.desc()).offset(skip).limit(limit).all()
    
    # Calculate pagination info
    total_pages = (total + limit - 1) // limit
    page = (skip // limit) + 1
    
    return TranscriptionListResponse(
        transcriptions=[TranscriptionResponse.model_validate(t) for t in transcriptions],
        total=total,
        page=page,
        per_page=limit,
        total_pages=total_pages
    )


@router.get("/admin/statistics", response_model=TranscriptionStatistics)
async def get_transcription_statistics(
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Get statistics about transcriptions in the database.
    
    Available to admins and Sworik developers for monitoring and reporting.
    Includes counts by user and language, consensus rates, quality metrics,
    and chunk coverage statistics.
    """
    transcription_service = TranscriptionService(db)
    return transcription_service.get_transcription_statistics()


@router.patch("/admin/{transcription_id}/consensus")
async def set_consensus_transcription(
    transcription_id: int,
    is_consensus: bool,
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Manually set or unset a transcription as consensus (admin only).
    
    This endpoint allows admins to manually override consensus calculations
    for quality control or correction purposes.
    """
    transcription_service = TranscriptionService(db)
    
    transcription = transcription_service.get_transcription_by_id(transcription_id)
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    # If setting as consensus, unset other consensus transcriptions for the same chunk
    if is_consensus:
        from app.models.transcription import Transcription
        db.query(Transcription).filter(
            and_(
                Transcription.chunk_id == transcription.chunk_id,
                Transcription.id != transcription_id
            )
        ).update({"is_consensus": False})
    
    # Update the transcription
    transcription.is_consensus = is_consensus
    transcription.meta_data = transcription.meta_data or {}
    transcription.meta_data["consensus_set_by"] = current_user.id
    transcription.meta_data["consensus_set_at"] = datetime.now(timezone.utc).isoformat()
    
    db.commit()
    db.refresh(transcription)
    
    return TranscriptionResponse.model_validate(transcription)


@router.patch("/admin/{transcription_id}/validate")
async def validate_transcription(
    transcription_id: int,
    is_validated: bool,
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Manually validate or invalidate a transcription (admin only).
    
    This endpoint allows admins to manually validate transcriptions
    for quality assurance purposes.
    """
    transcription_service = TranscriptionService(db)
    
    transcription = transcription_service.get_transcription_by_id(transcription_id)
    if not transcription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found"
        )
    
    # Update validation status
    transcription.is_validated = is_validated
    transcription.meta_data = transcription.meta_data or {}
    transcription.meta_data["validated_by"] = current_user.id
    transcription.meta_data["validated_at"] = datetime.now(timezone.utc).isoformat()
    
    db.commit()
    db.refresh(transcription)
    
    return TranscriptionResponse.model_validate(transcription)


@router.post("/admin/recalculate-consensus")
async def recalculate_consensus(
    chunk_ids: Optional[list[int]] = None,
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Manually trigger consensus recalculation (admin only).
    
    This endpoint allows admins to trigger consensus recalculation for specific
    chunks or all chunks if no chunk IDs are provided.
    """
    try:
        from app.tasks.audio_processing import calculate_consensus_for_chunks, recalculate_all_consensus
        
        if chunk_ids:
            # Recalculate for specific chunks
            task = calculate_consensus_for_chunks.delay(chunk_ids)
            message = f"Consensus recalculation triggered for {len(chunk_ids)} chunks"
        else:
            # Recalculate for all chunks
            task = recalculate_all_consensus.delay()
            message = "Consensus recalculation triggered for all chunks"
        
        return {
            "message": message,
            "task_id": task.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger consensus recalculation: {str(e)}"
        )


@router.get("/admin/chunks/problematic")
async def get_problematic_chunks(
    min_skips: int = Query(3, ge=1, description="Minimum number of skips to consider problematic"),
    skip: int = Query(0, ge=0, description="Number of chunks to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of chunks to return"),
    current_user: User = Depends(require_admin_or_sworik),
    db: Session = Depends(get_db)
):
    """
    Get chunks that have been skipped frequently (admin only).
    
    This endpoint helps identify problematic audio chunks that users
    frequently skip, which may indicate quality issues or unclear speech.
    """
    from app.models.audio_chunk import AudioChunk
    from app.models.transcription import Transcription
    from sqlalchemy import text
    
    # Query chunks with skip counts from metadata
    query = db.query(AudioChunk).filter(
        text("JSON_LENGTH(meta_data->'$.skips') >= :min_skips")
    ).params(min_skips=min_skips)
    
    total = query.count()
    chunks = query.offset(skip).limit(limit).all()
    
    # Format response with skip information
    problematic_chunks = []
    for chunk in chunks:
        skip_count = len(chunk.meta_data.get("skips", [])) if chunk.meta_data else 0
        transcription_count = db.query(Transcription).filter(Transcription.chunk_id == chunk.id).count()
        
        problematic_chunks.append({
            "chunk_id": chunk.id,
            "recording_id": chunk.recording_id,
            "duration": chunk.duration,
            "skip_count": skip_count,
            "transcription_count": transcription_count,
            "file_path": chunk.file_path
        })
    
    return {
        "chunks": problematic_chunks,
        "total": total,
        "page": (skip // limit) + 1,
        "per_page": limit,
        "total_pages": (total + limit - 1) // limit
    }