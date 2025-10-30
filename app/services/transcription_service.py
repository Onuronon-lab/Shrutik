import uuid
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, not_
from fastapi import HTTPException, status
from app.models.audio_chunk import AudioChunk
from app.models.transcription import Transcription
from app.models.voice_recording import VoiceRecording
from app.models.language import Language
from app.models.user import User
from app.schemas.transcription import (
    TranscriptionCreate, TranscriptionUpdate, TranscriptionResponse,
    AudioChunkForTranscription, TranscriptionTaskRequest, TranscriptionTaskResponse,
    TranscriptionSubmission, TranscriptionSubmissionResponse, TranscriptionListResponse,
    TranscriptionStatistics, ChunkSkipRequest, ChunkSkipResponse
)


class TranscriptionSession:
    """Represents an active transcription session."""
    
    def __init__(self, session_id: str, user_id: int, chunk_ids: List[int]):
        self.session_id = session_id
        self.user_id = user_id
        self.chunk_ids = chunk_ids
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(hours=2)  # 2-hour session timeout


class TranscriptionService:
    """Service for managing transcriptions and transcription tasks."""
    
    def __init__(self, db: Session):
        self.db = db
        self._active_sessions: Dict[str, TranscriptionSession] = {}
    
    def get_random_chunks_for_transcription(
        self, 
        user_id: int, 
        task_request: TranscriptionTaskRequest
    ) -> TranscriptionTaskResponse:
        """Get random untranscribed audio chunks for transcription."""
        
        # Base query for chunks that need transcription
        query = self.db.query(AudioChunk).join(VoiceRecording)
        
        # Filter by language if specified
        if task_request.language_id:
            query = query.filter(VoiceRecording.language_id == task_request.language_id)
        
        # Exclude chunks that the user has already transcribed
        user_transcribed_chunks = self.db.query(Transcription.chunk_id).filter(
            Transcription.user_id == user_id
        ).subquery()
        
        query = query.filter(~AudioChunk.id.in_(user_transcribed_chunks))
        
        # Exclude chunks in skip list
        if task_request.skip_chunk_ids:
            query = query.filter(~AudioChunk.id.in_(task_request.skip_chunk_ids))
        
        # Only include chunks from successfully processed recordings
        from app.models.voice_recording import RecordingStatus
        query = query.filter(VoiceRecording.status == RecordingStatus.CHUNKED)
        
        # Get total available count
        total_available = query.count()
        
        if total_available == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No untranscribed chunks available for the specified criteria"
            )
        
        # Get random chunks limited by quantity
        chunks = query.order_by(func.random()).limit(task_request.quantity).all()
        
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No chunks available for transcription"
            )
        
        # Convert to response format with transcription counts
        chunk_responses = []
        for chunk in chunks:
            transcription_count = self.db.query(Transcription).filter(
                Transcription.chunk_id == chunk.id
            ).count()
            
            chunk_response = AudioChunkForTranscription(
                id=chunk.id,
                recording_id=chunk.recording_id,
                chunk_index=chunk.chunk_index,
                file_path=chunk.file_path,
                start_time=chunk.start_time,
                end_time=chunk.end_time,
                duration=chunk.duration,
                sentence_hint=chunk.sentence_hint,
                transcription_count=transcription_count
            )
            chunk_responses.append(chunk_response)
        
        # Create session
        session_id = str(uuid.uuid4())
        chunk_ids = [chunk.id for chunk in chunks]
        session = TranscriptionSession(session_id, user_id, chunk_ids)
        self._active_sessions[session_id] = session
        
        return TranscriptionTaskResponse(
            chunks=chunk_responses,
            total_available=total_available,
            session_id=session_id
        )
    
    def get_transcription_session(self, session_id: str) -> Optional[TranscriptionSession]:
        """Get an active transcription session."""
        session = self._active_sessions.get(session_id)
        if session and session.expires_at > datetime.now(timezone.utc):
            return session
        elif session:
            # Remove expired session
            del self._active_sessions[session_id]
        return None
    
    def submit_transcriptions(
        self, 
        user_id: int, 
        submission: TranscriptionSubmission
    ) -> TranscriptionSubmissionResponse:
        """Submit transcriptions for audio chunks."""
        
        # Validate session
        session = self.get_transcription_session(submission.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired transcription session"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to current user"
            )
        
        # Validate that all chunk IDs are in the session
        submitted_chunk_ids = [t.chunk_id for t in submission.transcriptions]
        invalid_chunks = set(submitted_chunk_ids) - set(session.chunk_ids)
        if invalid_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid chunk IDs not in session: {list(invalid_chunks)}"
            )
        
        # Check for duplicate transcriptions by this user
        existing_transcriptions = self.db.query(Transcription).filter(
            and_(
                Transcription.user_id == user_id,
                Transcription.chunk_id.in_(submitted_chunk_ids)
            )
        ).all()
        
        if existing_transcriptions:
            existing_chunk_ids = [t.chunk_id for t in existing_transcriptions]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User has already transcribed chunks: {existing_chunk_ids}"
            )
        
        # Create transcription records
        created_transcriptions = []
        
        try:
            for transcription_data in submission.transcriptions:
                # Validate chunk exists and is from a processed recording
                from app.models.voice_recording import RecordingStatus
                chunk = self.db.query(AudioChunk).join(VoiceRecording).filter(
                    and_(
                        AudioChunk.id == transcription_data.chunk_id,
                        VoiceRecording.status == RecordingStatus.CHUNKED
                    )
                ).first()
                
                if not chunk:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Chunk {transcription_data.chunk_id} not found or not ready for transcription"
                    )
                
                # Create transcription record
                db_transcription = Transcription(
                    chunk_id=transcription_data.chunk_id,
                    user_id=user_id,
                    language_id=transcription_data.language_id,
                    text=transcription_data.text,
                    quality=transcription_data.quality or 0.0,
                    confidence=transcription_data.confidence or 0.0,
                    meta_data=transcription_data.meta_data or {}
                )
                
                self.db.add(db_transcription)
                created_transcriptions.append(db_transcription)
            
            # Handle skipped chunks
            if submission.skipped_chunk_ids:
                self._record_chunk_skips(user_id, submission.skipped_chunk_ids, session.session_id)
            
            self.db.commit()
            
            # Refresh all created transcriptions
            for transcription in created_transcriptions:
                self.db.refresh(transcription)
            
            # Clean up session
            if session.session_id in self._active_sessions:
                del self._active_sessions[session.session_id]
            
            # Trigger consensus calculation for affected chunks
            self._trigger_consensus_calculation(submitted_chunk_ids)
            
            return TranscriptionSubmissionResponse(
                submitted_count=len(created_transcriptions),
                skipped_count=len(submission.skipped_chunk_ids or []),
                transcriptions=[TranscriptionResponse.model_validate(t) for t in created_transcriptions],
                message=f"Successfully submitted {len(created_transcriptions)} transcriptions"
            )
            
        except Exception as e:
            self.db.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit transcriptions: {str(e)}"
            )
    
    def skip_chunk(self, user_id: int, skip_request: ChunkSkipRequest) -> ChunkSkipResponse:
        """Record that a user skipped a difficult chunk."""
        
        # Validate chunk exists
        chunk = self.db.query(AudioChunk).filter(AudioChunk.id == skip_request.chunk_id).first()
        if not chunk:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chunk not found"
            )
        
        # Record the skip in metadata (could be a separate table in production)
        skip_record = {
            "user_id": user_id,
            "chunk_id": skip_request.chunk_id,
            "reason": skip_request.reason,
            "skipped_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Update chunk metadata to track skips
        if chunk.meta_data is None:
            chunk.meta_data = {}
        
        if "skips" not in chunk.meta_data:
            chunk.meta_data["skips"] = []
        
        chunk.meta_data["skips"].append(skip_record)
        
        self.db.commit()
        self.db.refresh(chunk)
        
        # Count total skips for this chunk
        skip_count = len(chunk.meta_data.get("skips", []))
        
        return ChunkSkipResponse(
            chunk_id=skip_request.chunk_id,
            skipped_by_user=user_id,
            reason=skip_request.reason,
            skip_count=skip_count,
            created_at=datetime.now(timezone.utc)
        )
    
    def get_user_transcriptions(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        language_id: Optional[int] = None
    ) -> TranscriptionListResponse:
        """Get paginated list of user's transcriptions."""
        
        query = self.db.query(Transcription).filter(Transcription.user_id == user_id)
        
        if language_id:
            query = query.filter(Transcription.language_id == language_id)
        
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
    
    def get_transcription_by_id(
        self, 
        transcription_id: int, 
        user_id: Optional[int] = None
    ) -> Optional[Transcription]:
        """Get transcription by ID, optionally filtered by user."""
        
        query = self.db.query(Transcription).filter(Transcription.id == transcription_id)
        if user_id:
            query = query.filter(Transcription.user_id == user_id)
        return query.first()
    
    def update_transcription(
        self, 
        transcription_id: int, 
        update_data: TranscriptionUpdate,
        user_id: Optional[int] = None
    ) -> Transcription:
        """Update an existing transcription."""
        
        transcription = self.get_transcription_by_id(transcription_id, user_id)
        if not transcription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcription not found"
            )
        
        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(transcription, field, value)
        
        self.db.commit()
        self.db.refresh(transcription)
        return transcription
    
    def get_transcription_statistics(self) -> TranscriptionStatistics:
        """Get statistics about transcriptions in the database."""
        
        total_transcriptions = self.db.query(Transcription).count()
        
        # Count by user
        user_stats = self.db.query(
            User.name,
            User.email,
            func.count(Transcription.id).label('transcription_count'),
            func.avg(Transcription.quality).label('avg_quality')
        ).join(Transcription).group_by(User.id, User.name, User.email).all()
        
        # Count by language
        language_stats = self.db.query(
            Language.name,
            Language.code,
            func.count(Transcription.id).label('transcription_count')
        ).join(Transcription).group_by(Language.id, Language.name, Language.code).all()
        
        # Calculate consensus and validation rates
        consensus_count = self.db.query(Transcription).filter(Transcription.is_consensus == True).count()
        validated_count = self.db.query(Transcription).filter(Transcription.is_validated == True).count()
        
        consensus_rate = (consensus_count / total_transcriptions * 100) if total_transcriptions > 0 else 0
        validation_rate = (validated_count / total_transcriptions * 100) if total_transcriptions > 0 else 0
        
        # Calculate average quality score
        avg_quality = self.db.query(func.avg(Transcription.quality)).scalar() or 0
        
        # Count chunks with and without transcriptions
        chunks_with_transcriptions = self.db.query(AudioChunk.id).join(Transcription).distinct().count()
        total_chunks = self.db.query(AudioChunk).count()
        chunks_needing_transcription = total_chunks - chunks_with_transcriptions
        
        return TranscriptionStatistics(
            total_transcriptions=total_transcriptions,
            by_user=[
                {
                    "name": stat.name,
                    "email": stat.email,
                    "count": stat.transcription_count,
                    "avg_quality": round(float(stat.avg_quality or 0), 2)
                }
                for stat in user_stats
            ],
            by_language=[
                {"language": lang.name, "code": lang.code, "count": lang.transcription_count}
                for lang in language_stats
            ],
            consensus_rate=round(consensus_rate, 2),
            validation_rate=round(validation_rate, 2),
            average_quality_score=round(float(avg_quality), 2),
            chunks_with_transcriptions=chunks_with_transcriptions,
            chunks_needing_transcription=chunks_needing_transcription
        )
    
    def _record_chunk_skips(self, user_id: int, chunk_ids: List[int], session_id: str) -> None:
        """Record that chunks were skipped by a user."""
        
        for chunk_id in chunk_ids:
            chunk = self.db.query(AudioChunk).filter(AudioChunk.id == chunk_id).first()
            if chunk:
                skip_record = {
                    "user_id": user_id,
                    "chunk_id": chunk_id,
                    "session_id": session_id,
                    "skipped_at": datetime.now(timezone.utc).isoformat()
                }
                
                if chunk.meta_data is None:
                    chunk.meta_data = {}
                
                if "skips" not in chunk.meta_data:
                    chunk.meta_data["skips"] = []
                
                chunk.meta_data["skips"].append(skip_record)
    
    def _trigger_consensus_calculation(self, chunk_ids: List[int]) -> None:
        """Trigger consensus calculation for chunks with new transcriptions."""
        
        try:
            # Import here to avoid circular imports
            from app.tasks.audio_processing import calculate_consensus_for_chunks
            
            # Queue consensus calculation task
            task = calculate_consensus_for_chunks.delay(chunk_ids)
            
            # Could store task ID for tracking if needed
            print(f"Triggered consensus calculation for chunks {chunk_ids}, task ID: {task.id}")
            
        except Exception as e:
            # Log error but don't fail the transcription submission
            print(f"Warning: Failed to trigger consensus calculation for chunks {chunk_ids}: {e}")