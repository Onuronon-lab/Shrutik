import os
import uuid
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from fastapi import HTTPException, status, UploadFile
import librosa
import soundfile as sf
from app.models.voice_recording import VoiceRecording, RecordingStatus
from app.models.script import Script
from app.models.language import Language
from app.models.user import User
from app.schemas.voice_recording import (
    VoiceRecordingCreate, VoiceRecordingUpdate, VoiceRecordingResponse,
    VoiceRecordingListResponse, RecordingSessionCreate, RecordingSessionResponse,
    RecordingUploadRequest, RecordingProgressResponse, RecordingStatistics
)
from app.core.config import settings


class RecordingSession:
    """Represents an active recording session."""
    
    def __init__(self, session_id: str, script_id: int, user_id: int, language_id: int):
        self.session_id = session_id
        self.script_id = script_id
        self.user_id = user_id
        self.language_id = language_id
        self.created_at = datetime.now(timezone.utc)
        self.expires_at = self.created_at + timedelta(hours=2)  # 2-hour session timeout


class VoiceRecordingService:
    """Service for managing voice recordings and recording sessions."""
    
    def __init__(self, db: Session):
        self.db = db
        self._active_sessions: Dict[str, RecordingSession] = {}
    
    def create_recording_session(
        self, 
        user_id: int, 
        session_data: RecordingSessionCreate
    ) -> RecordingSessionResponse:
        """Create a new recording session for a user."""
        # Validate script exists
        script = self.db.query(Script).filter(Script.id == session_data.script_id).first()
        if not script:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Script not found"
            )
        
        # Use script's language or provided language
        language_id = session_data.language_id or script.language_id
        
        # Validate language exists
        language = self.db.query(Language).filter(Language.id == language_id).first()
        if not language:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Language with ID {language_id} not found"
            )
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session
        session = RecordingSession(
            session_id=session_id,
            script_id=script.id,
            user_id=user_id,
            language_id=language_id
        )
        
        # Store session (in production, use Redis or database)
        self._active_sessions[session_id] = session
        
        return RecordingSessionResponse(
            session_id=session_id,
            script_id=script.id,
            script_text=script.text,
            language_id=language_id,
            expected_duration_category=script.duration_category.value,
            created_at=session.created_at,
            expires_at=session.expires_at
        )
    
    def get_recording_session(self, session_id: str) -> Optional[RecordingSession]:
        """Get an active recording session."""
        session = self._active_sessions.get(session_id)
        if session and session.expires_at > datetime.now(timezone.utc):
            return session
        elif session:
            # Remove expired session
            del self._active_sessions[session_id]
        return None
    
    def upload_recording(
        self, 
        user_id: int, 
        upload_data: RecordingUploadRequest, 
        audio_file: UploadFile
    ) -> VoiceRecordingResponse:
        """Upload and process a voice recording."""
        # Validate session
        session = self.get_recording_session(upload_data.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired recording session"
            )
        
        if session.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to current user"
            )
        
        # Validate file format
        if not audio_file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided"
            )
        
        file_extension = os.path.splitext(audio_file.filename)[1].lower()
        if file_extension not in settings.ALLOWED_AUDIO_FORMATS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported audio format. Allowed: {', '.join(settings.ALLOWED_AUDIO_FORMATS)}"
            )
        
        # Validate file size
        if upload_data.file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE // (1024 * 1024)}MB"
            )
        
        try:
            # Generate unique filename
            file_hash = hashlib.md5(f"{session.session_id}_{user_id}_{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()
            filename = f"{file_hash}{file_extension}"
            
            # Create upload directory structure
            upload_dir = os.path.join(settings.UPLOAD_DIR, "recordings", str(user_id))
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                content = audio_file.file.read()
                buffer.write(content)
            
            # Validate audio file and extract metadata
            audio_metadata = self._validate_and_extract_audio_metadata(file_path, upload_data)
            
            # Create database record
            recording_data = VoiceRecordingCreate(
                script_id=session.script_id,
                language_id=session.language_id,
                duration=upload_data.duration,
                meta_data={
                    "session_id": session.session_id,
                    "audio_format": upload_data.audio_format,
                    "sample_rate": upload_data.sample_rate,
                    "channels": upload_data.channels,
                    "bit_depth": upload_data.bit_depth,
                    "file_size": upload_data.file_size,
                    "original_filename": audio_file.filename,
                    **audio_metadata
                }
            )
            
            db_recording = VoiceRecording(
                user_id=user_id,
                script_id=recording_data.script_id,
                language_id=recording_data.language_id,
                file_path=file_path,
                duration=recording_data.duration,
                status=RecordingStatus.UPLOADED,
                meta_data=recording_data.meta_data
            )
            
            self.db.add(db_recording)
            self.db.commit()
            self.db.refresh(db_recording)
            
            # Clean up session
            if session.session_id in self._active_sessions:
                del self._active_sessions[session.session_id]
            
            # Trigger background audio processing
            self._trigger_audio_processing(db_recording.id)
            
            return VoiceRecordingResponse.model_validate(db_recording)
            
        except Exception as e:
            # Clean up file if database operation fails
            if 'file_path' in locals() and os.path.exists(file_path):
                os.remove(file_path)
            
            if isinstance(e, HTTPException):
                raise e
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process recording: {str(e)}"
            )
    
    def _validate_and_extract_audio_metadata(
        self, 
        file_path: str, 
        upload_data: RecordingUploadRequest
    ) -> Dict[str, Any]:
        """Validate audio file and extract metadata using librosa."""
        try:
            # Load audio file
            y, sr = librosa.load(file_path, sr=None)
            
            # Extract metadata
            actual_duration = librosa.get_duration(y=y, sr=sr)
            actual_sample_rate = sr
            actual_channels = 1 if len(y.shape) == 1 else y.shape[0]
            
            # Validate duration matches uploaded metadata (within 5% tolerance)
            duration_diff = abs(actual_duration - upload_data.duration)
            if duration_diff > (upload_data.duration * 0.05):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Duration mismatch: uploaded {upload_data.duration}s, actual {actual_duration:.2f}s"
                )
            
            # Calculate audio quality metrics
            rms_energy = librosa.feature.rms(y=y)[0]
            spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # Detect silence periods
            silence_threshold = 0.01
            silence_frames = rms_energy < silence_threshold
            silence_percentage = (silence_frames.sum() / len(silence_frames)) * 100
            
            return {
                "validated_duration": actual_duration,
                "validated_sample_rate": actual_sample_rate,
                "validated_channels": actual_channels,
                "rms_energy_mean": float(rms_energy.mean()),
                "spectral_centroid_mean": float(spectral_centroid.mean()),
                "zero_crossing_rate_mean": float(zero_crossing_rate.mean()),
                "silence_percentage": float(silence_percentage),
                "quality_score": self._calculate_quality_score(rms_energy, silence_percentage)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid audio file: {str(e)}"
            )
    
    def _calculate_quality_score(self, rms_energy, silence_percentage: float) -> float:
        """Calculate a quality score for the audio recording."""
        # Simple quality scoring based on energy and silence
        energy_score = min(rms_energy.mean() * 100, 100)  # Normalize to 0-100
        silence_penalty = min(silence_percentage * 2, 50)  # Penalize excessive silence
        
        quality_score = max(energy_score - silence_penalty, 0)
        return float(quality_score)
    
    def get_recording_by_id(self, recording_id: int, user_id: Optional[int] = None) -> Optional[VoiceRecording]:
        """Get recording by ID, optionally filtered by user."""
        query = self.db.query(VoiceRecording).filter(VoiceRecording.id == recording_id)
        if user_id:
            query = query.filter(VoiceRecording.user_id == user_id)
        return query.first()
    
    def get_user_recordings(
        self, 
        user_id: int, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[RecordingStatus] = None
    ) -> VoiceRecordingListResponse:
        """Get paginated list of user's recordings."""
        query = self.db.query(VoiceRecording).filter(VoiceRecording.user_id == user_id)
        
        if status:
            query = query.filter(VoiceRecording.status == status)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        recordings = query.order_by(VoiceRecording.created_at.desc()).offset(skip).limit(limit).all()
        
        # Calculate pagination info
        total_pages = (total + limit - 1) // limit
        page = (skip // limit) + 1
        
        return VoiceRecordingListResponse(
            recordings=recordings,
            total=total,
            page=page,
            per_page=limit,
            total_pages=total_pages
        )
    
    def update_recording_status(
        self, 
        recording_id: int, 
        status: RecordingStatus, 
        meta_data_update: Optional[Dict[str, Any]] = None
    ) -> VoiceRecording:
        """Update recording status and metadata."""
        recording = self.get_recording_by_id(recording_id)
        if not recording:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )
        
        recording.status = status
        
        if meta_data_update:
            if recording.meta_data is None:
                recording.meta_data = {}
            recording.meta_data.update(meta_data_update)
        
        self.db.commit()
        self.db.refresh(recording)
        return recording
    
    def get_recording_progress(self, recording_id: int) -> RecordingProgressResponse:
        """Get processing progress for a recording."""
        recording = self.get_recording_by_id(recording_id)
        if not recording:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )
        
        # Calculate progress based on status
        progress_map = {
            RecordingStatus.UPLOADED: (10.0, "Recording uploaded successfully"),
            RecordingStatus.PROCESSING: (50.0, "Processing audio chunks"),
            RecordingStatus.CHUNKED: (100.0, "Processing completed"),
            RecordingStatus.FAILED: (0.0, "Processing failed")
        }
        
        progress, message = progress_map.get(recording.status, (0.0, "Unknown status"))
        
        return RecordingProgressResponse(
            recording_id=recording.id,
            status=recording.status,
            progress_percentage=progress,
            message=message,
            estimated_completion=None  # Could be calculated based on queue length
        )
    
    def get_recording_statistics(self) -> RecordingStatistics:
        """Get statistics about recordings in the database."""
        total_recordings = self.db.query(VoiceRecording).count()
        
        # Count by status
        status_stats = {}
        for status in RecordingStatus:
            count = self.db.query(VoiceRecording).filter(VoiceRecording.status == status).count()
            status_stats[status.value] = count
        
        # Count by duration category (via script)
        duration_stats = self.db.query(
            Script.duration_category,
            func.count(VoiceRecording.id).label('recording_count')
        ).join(VoiceRecording).group_by(Script.duration_category).all()
        
        duration_dict = {stat.duration_category.value: stat.recording_count for stat in duration_stats}
        
        # Count by language
        language_stats = self.db.query(
            Language.name,
            Language.code,
            func.count(VoiceRecording.id).label('recording_count')
        ).join(VoiceRecording).group_by(Language.id, Language.name, Language.code).all()
        
        # Calculate total duration
        total_duration_seconds = self.db.query(func.sum(VoiceRecording.duration)).scalar() or 0
        total_duration_hours = total_duration_seconds / 3600
        
        # Calculate average duration
        avg_duration_seconds = self.db.query(func.avg(VoiceRecording.duration)).scalar() or 0
        avg_duration_minutes = avg_duration_seconds / 60
        
        return RecordingStatistics(
            total_recordings=total_recordings,
            by_status=status_stats,
            by_duration_category=duration_dict,
            by_language=[
                {"language": lang.name, "code": lang.code, "count": lang.recording_count}
                for lang in language_stats
            ],
            total_duration_hours=round(total_duration_hours, 2),
            average_duration_minutes=round(avg_duration_minutes, 2)
        )
    
    def delete_recording(self, recording_id: int, user_id: Optional[int] = None) -> bool:
        """Delete a recording and its associated file."""
        recording = self.get_recording_by_id(recording_id, user_id)
        if not recording:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found"
            )
        
        # Check if recording has been processed (has chunks)
        from app.models.audio_chunk import AudioChunk
        chunks_count = self.db.query(AudioChunk).filter(AudioChunk.recording_id == recording_id).count()
        
        if chunks_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete recording: {chunks_count} audio chunks exist. Delete chunks first."
            )
        
        # Delete file from filesystem
        if os.path.exists(recording.file_path):
            try:
                os.remove(recording.file_path)
            except OSError as e:
                # Log error but don't fail the deletion
                print(f"Warning: Could not delete file {recording.file_path}: {e}")
        
        # Delete database record
        self.db.delete(recording)
        self.db.commit()
        return True
    
    def _trigger_audio_processing(self, recording_id: int) -> None:
        """Trigger background audio processing for a recording."""
        try:
            from app.tasks.audio_processing import process_audio_recording
            
            # Queue the audio processing task
            task = process_audio_recording.delay(recording_id)
            
            # Update recording metadata with task ID for tracking
            recording = self.get_recording_by_id(recording_id)
            if recording:
                if recording.meta_data is None:
                    recording.meta_data = {}
                recording.meta_data["processing_task_id"] = task.id
                self.db.commit()
                
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Warning: Failed to trigger audio processing for recording {recording_id}: {e}")
    
    def get_processing_task_status(self, recording_id: int) -> Optional[Dict[str, Any]]:
        """Get the status of the background processing task for a recording."""
        recording = self.get_recording_by_id(recording_id)
        if not recording or not recording.meta_data:
            return None
        
        task_id = recording.meta_data.get("processing_task_id")
        if not task_id:
            return None
        
        try:
            from app.core.celery_app import celery_app
            from celery.result import AsyncResult
            
            result = AsyncResult(task_id, app=celery_app)
            
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "info": result.info if hasattr(result, 'info') else None
            }
            
        except Exception as e:
            print(f"Error getting task status for recording {recording_id}: {e}")
            return None