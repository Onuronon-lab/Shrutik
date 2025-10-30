from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
from app.db.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/chunks", tags=["chunks"])


@router.get("/{chunk_id}/audio", 
           summary="Get Audio File for Chunk",
           description="Serve the audio file for a specific audio chunk",
           responses={
               200: {"description": "Audio file", "content": {"audio/wav": {}}},
               404: {"description": "Chunk or audio file not found"},
               401: {"description": "Authentication required"}
           })
async def get_chunk_audio(
    chunk_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Serve audio file for a specific chunk.
    
    This endpoint serves the audio file associated with a chunk for transcription.
    Users can only access chunks that are available for transcription.
    
    - **chunk_id**: The ID of the audio chunk
    - **Returns**: Audio file (WAV format)
    """
    from app.models.audio_chunk import AudioChunk
    
    # Get the chunk from database
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
    
    # Return the audio file with headers optimized for browser playback
    return FileResponse(
        path=chunk.file_path,
        media_type="audio/wav",
        filename=f"chunk_{chunk_id}.wav",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "*"
        }
    )