"""
Consensus and Quality Validation API endpoints.

This module provides endpoints for managing consensus calculation,
quality validation, and manual review processes.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.core.dependencies import get_db, get_current_user, require_admin_or_sworik
from app.models.user import User
from app.models.quality_review import ReviewDecision
from app.services.consensus_service import ConsensusService
from app.tasks.audio_processing import calculate_consensus_for_chunks, recalculate_all_consensus

router = APIRouter(prefix="/api/consensus", tags=["consensus"])


class ConsensusEvaluationResponse(BaseModel):
    """Response model for consensus evaluation."""
    chunk_id: int
    consensus_text: str
    confidence_score: float
    requires_review: bool
    participant_count: int
    quality_score: float
    transcription_similarities: List[float]
    flagged_reasons: List[str]


class ValidationStatusResponse(BaseModel):
    """Response model for validation status."""
    chunk_id: int
    is_validated: bool
    consensus_transcription_id: Optional[int]
    validation_confidence: float
    requires_manual_review: bool
    last_updated: str


class ManualReviewRequest(BaseModel):
    """Request model for manual review decisions."""
    decision: ReviewDecision
    selected_transcription_id: Optional[int] = Field(None, description="ID of transcription to mark as consensus")
    comment: Optional[str] = Field(None, description="Optional review comment")


class ManualReviewResponse(BaseModel):
    """Response model for manual review decisions."""
    success: bool
    message: str
    chunk_id: int
    decision: ReviewDecision


class ChunkReviewInfo(BaseModel):
    """Information about a chunk requiring review."""
    chunk_id: int
    recording_id: int
    duration: float
    transcription_count: int
    flagged_reasons: List[str]
    transcriptions: List[Dict[str, Any]]


class ValidationStatisticsResponse(BaseModel):
    """Response model for validation statistics."""
    total_chunks_with_transcriptions: int
    validated_chunks: int
    chunks_requiring_review: int
    consensus_transcriptions: int
    validation_rate: float
    average_confidence_score: float
    average_quality_score: float
    quality_review_counts: Dict[str, int]


@router.post("/evaluate/{chunk_id}", response_model=ConsensusEvaluationResponse)
async def evaluate_chunk_consensus(
    chunk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """
    Evaluate consensus for a specific chunk.
    
    This endpoint manually triggers consensus evaluation for a single chunk.
    Typically used for testing or re-evaluation after manual corrections.
    """
    consensus_service = ConsensusService(db)
    
    try:
        result = consensus_service.evaluate_chunk_consensus(chunk_id)
        
        return ConsensusEvaluationResponse(
            chunk_id=result.chunk_id,
            consensus_text=result.consensus_text,
            confidence_score=result.confidence_score,
            requires_review=result.requires_review,
            participant_count=result.participant_count,
            quality_score=result.quality_score,
            transcription_similarities=result.transcription_similarities,
            flagged_reasons=result.flagged_reasons
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate consensus for chunk {chunk_id}: {str(e)}"
        )


@router.post("/validate/{chunk_id}", response_model=ValidationStatusResponse)
async def update_chunk_validation(
    chunk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """
    Update validation status for a specific chunk.
    
    This endpoint evaluates consensus and updates the validation status
    for a single chunk, including marking consensus transcriptions.
    """
    consensus_service = ConsensusService(db)
    
    try:
        # First evaluate consensus
        consensus_result = consensus_service.evaluate_chunk_consensus(chunk_id)
        
        # Then update validation status
        validation_status = consensus_service.update_chunk_validation_status(consensus_result)
        
        return ValidationStatusResponse(
            chunk_id=validation_status.chunk_id,
            is_validated=validation_status.is_validated,
            consensus_transcription_id=validation_status.consensus_transcription_id,
            validation_confidence=validation_status.validation_confidence,
            requires_manual_review=validation_status.requires_manual_review,
            last_updated=validation_status.last_updated.isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update validation for chunk {chunk_id}: {str(e)}"
        )


@router.post("/batch-calculate")
async def trigger_batch_consensus_calculation(
    chunk_ids: List[int],
    current_user: User = Depends(require_admin_or_sworik)
):
    """
    Trigger consensus calculation for multiple chunks.
    
    This endpoint queues a background task to calculate consensus
    for the specified chunks. Returns a task ID for tracking progress.
    """
    try:
        # Queue the consensus calculation task
        task = calculate_consensus_for_chunks.delay(chunk_ids)
        
        return {
            "message": f"Consensus calculation queued for {len(chunk_ids)} chunks",
            "task_id": task.id,
            "chunk_count": len(chunk_ids)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue consensus calculation: {str(e)}"
        )


@router.post("/recalculate-all")
async def trigger_full_consensus_recalculation(
    current_user: User = Depends(require_admin_or_sworik)
):
    """
    Trigger consensus recalculation for all eligible chunks.
    
    This endpoint queues a background task to recalculate consensus
    for all chunks that have multiple transcriptions.
    """
    try:
        # Queue the full recalculation task
        task = recalculate_all_consensus.delay()
        
        return {
            "message": "Full consensus recalculation queued",
            "task_id": task.id
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue full consensus recalculation: {str(e)}"
        )


@router.get("/review-queue", response_model=List[ChunkReviewInfo])
async def get_chunks_requiring_review(
    limit: int = Query(50, ge=1, le=100, description="Maximum number of chunks to return"),
    skip: int = Query(0, ge=0, description="Number of chunks to skip for pagination"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """
    Get chunks that require manual review.
    
    Returns a paginated list of chunks that have been flagged for manual review
    due to low consensus confidence or other quality issues.
    """
    consensus_service = ConsensusService(db)
    
    try:
        chunks = consensus_service.get_chunks_requiring_review(limit=limit, skip=skip)
        
        return [
            ChunkReviewInfo(
                chunk_id=chunk["chunk_id"],
                recording_id=chunk["recording_id"],
                duration=chunk["duration"],
                transcription_count=chunk["transcription_count"],
                flagged_reasons=chunk["flagged_reasons"],
                transcriptions=chunk["transcriptions"]
            )
            for chunk in chunks
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chunks requiring review: {str(e)}"
        )


@router.post("/manual-review/{chunk_id}", response_model=ManualReviewResponse)
async def submit_manual_review(
    chunk_id: int,
    review_request: ManualReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """
    Submit a manual review decision for a chunk.
    
    This endpoint allows reviewers to make decisions about chunks that
    have been flagged for manual review due to consensus issues.
    """
    consensus_service = ConsensusService(db)
    
    try:
        success = consensus_service.manual_review_decision(
            chunk_id=chunk_id,
            reviewer_id=current_user.id,
            decision=review_request.decision,
            selected_transcription_id=review_request.selected_transcription_id,
            comment=review_request.comment
        )
        
        if success:
            return ManualReviewResponse(
                success=True,
                message=f"Manual review decision recorded: {review_request.decision.value}",
                chunk_id=chunk_id,
                decision=review_request.decision
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record manual review decision"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit manual review: {str(e)}"
        )


@router.get("/statistics", response_model=ValidationStatisticsResponse)
async def get_validation_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_sworik)
):
    """
    Get validation and consensus statistics.
    
    Returns comprehensive statistics about the validation status
    of chunks, consensus rates, and quality metrics.
    """
    consensus_service = ConsensusService(db)
    
    try:
        stats = consensus_service.get_validation_statistics()
        
        return ValidationStatisticsResponse(
            total_chunks_with_transcriptions=stats["total_chunks_with_transcriptions"],
            validated_chunks=stats["validated_chunks"],
            chunks_requiring_review=stats["chunks_requiring_review"],
            consensus_transcriptions=stats["consensus_transcriptions"],
            validation_rate=stats["validation_rate"],
            average_confidence_score=stats["average_confidence_score"],
            average_quality_score=stats["average_quality_score"],
            quality_review_counts=stats["quality_review_counts"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation statistics: {str(e)}"
        )


@router.get("/chunk/{chunk_id}/status")
async def get_chunk_validation_status(
    chunk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current validation status of a specific chunk.
    
    Returns information about whether the chunk is validated,
    has consensus, and any review requirements.
    """
    from app.models.transcription import Transcription
    from app.models.audio_chunk import AudioChunk
    
    try:
        # Get chunk and its transcriptions
        chunk = db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk not found"
            )
        
        transcriptions = db.query(Transcription).filter(
            Transcription.chunk_id == chunk_id
        ).all()
        
        if not transcriptions:
            return {
                "chunk_id": chunk_id,
                "has_transcriptions": False,
                "transcription_count": 0,
                "is_validated": False,
                "has_consensus": False,
                "requires_review": False
            }
        
        # Check validation and consensus status
        is_validated = any(t.is_validated for t in transcriptions)
        has_consensus = any(t.is_consensus for t in transcriptions)
        
        # Check if requires review from metadata
        requires_review = False
        for transcription in transcriptions:
            if (transcription.meta_data and 
                'consensus_evaluation' in transcription.meta_data and
                transcription.meta_data['consensus_evaluation'].get('requires_review', False)):
                requires_review = True
                break
        
        return {
            "chunk_id": chunk_id,
            "has_transcriptions": True,
            "transcription_count": len(transcriptions),
            "is_validated": is_validated,
            "has_consensus": has_consensus,
            "requires_review": requires_review,
            "transcriptions": [
                {
                    "id": t.id,
                    "text": t.text,
                    "is_consensus": t.is_consensus,
                    "is_validated": t.is_validated,
                    "quality": t.quality,
                    "confidence": t.confidence
                }
                for t in transcriptions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chunk validation status: {str(e)}"
        )