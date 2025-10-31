from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy.orm import Session
import os
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.core.cdn import media_delivery
from app.core.cache import cache_result
from app.core.performance import performance_monitor

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.get("/{chunk_id}/audio", 
           summary="Get Audio File for Chunk",
           description="Serve the audio file for a specific audio chunk with CDN optimization",
           responses={
               200: {"description": "Audio file", "content": {"audio/wav": {}}},
               302: {"description": "Redirect to CDN URL"},
               404: {"description": "Chunk or audio file not found"},
               401: {"description": "Authentication required"}
           })
@performance_monitor.monitor_endpoint("chunks_audio")
async def get_chunk_audio(
    chunk_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Serve audio file for a specific chunk with CDN optimization.
    
    This endpoint serves the audio file associated with a chunk for transcription.
    Uses CDN when available for optimized delivery, otherwise serves directly.
    
    - **chunk_id**: The ID of the audio chunk
    - **Returns**: Audio file (WAV format) or redirect to CDN
    """
    from app.models.audio_chunk import AudioChunk
    
    # Get optimized audio response with CDN support
    user_agent = request.headers.get("user-agent", "")
    optimization = media_delivery.get_optimized_audio_response(chunk_id, user_agent)
    
    if "error" in optimization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=optimization["error"]
        )
    
    # If CDN is enabled and URL is different from local, redirect to CDN
    cdn_url = optimization.get("url", "")
    if cdn_url and not cdn_url.startswith("/api/"):
        # Add cache headers to redirect response
        headers = optimization.get("cache_headers", {})
        return RedirectResponse(
            url=cdn_url,
            status_code=status.HTTP_302_FOUND,
            headers=headers
        )
    
    # Serve file locally with optimization
    chunk = db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio chunk not found"
        )
    
    # Check if file exists
    if not os.path.exists(chunk.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio file not found on disk"
        )
    
    # Get cache headers from optimization
    cache_headers = optimization.get("cache_headers", {})
    
    # Add performance headers
    headers = {
        "Accept-Ranges": "bytes",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET",
        "Access-Control-Allow-Headers": "*",
        **cache_headers
    }
    
    # Add preload hint if recommended
    if optimization.get("preload", False):
        headers["Link"] = f'<{cdn_url}>; rel=preload; as=audio'
    
    return FileResponse(
        path=chunk.file_path,
        media_type="audio/wav",
        filename=f"chunk_{chunk_id}.wav",
        headers=headers
    )


@router.get("/{chunk_id}/info")
@cache_result("chunk_info", ttl=3600)  # 1 hour cache
async def get_chunk_info(
    chunk_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get metadata information about an audio chunk.
    
    Returns chunk metadata including duration, transcription count,
    and optimization information without serving the actual file.
    """
    from app.models.audio_chunk import AudioChunk
    from app.models.transcription import Transcription
    
    chunk = db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio chunk not found"
        )
    
    # Get transcription count
    transcription_count = db.query(Transcription).filter(
        Transcription.chunk_id == chunk_id
    ).count()
    
    # Get optimization info
    optimization = media_delivery.get_optimized_audio_response(chunk_id)
    
    return {
        "chunk_id": chunk.id,
        "recording_id": chunk.recording_id,
        "chunk_index": chunk.chunk_index,
        "duration": chunk.duration,
        "start_time": chunk.start_time,
        "end_time": chunk.end_time,
        "transcription_count": transcription_count,
        "file_size": optimization.get("file_size", 0),
        "optimized_url": optimization.get("url", ""),
        "cache_headers": optimization.get("cache_headers", {}),
        "alternatives": optimization.get("alternatives", [])
    }