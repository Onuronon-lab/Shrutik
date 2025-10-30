"""
Celery tasks for audio processing and chunking.

These tasks handle background processing of uploaded voice recordings,
including intelligent chunking and metadata extraction.
"""

import logging
from typing import List, Optional
from celery import current_task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.db.database import SessionLocal
from app.services.audio_processing_service import audio_chunking_service, AudioProcessingError
from app.models.voice_recording import VoiceRecording, RecordingStatus
from app.models.audio_chunk import AudioChunk

logger = logging.getLogger(__name__)


def get_db() -> Session:
    """Get database session for Celery tasks."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


@celery_app.task(bind=True, name="process_audio_recording")
def process_audio_recording(self, recording_id: int) -> dict:
    """
    Process an uploaded audio recording by chunking it intelligently.
    
    Args:
        recording_id: ID of the VoiceRecording to process
        
    Returns:
        dict: Processing results with chunk count and status
    """
    db = get_db()
    
    try:
        logger.info(f"Starting audio processing task for recording {recording_id}")
        
        # Update task progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Loading recording...'}
        )
        
        # Get recording from database
        recording = db.query(VoiceRecording).filter(
            VoiceRecording.id == recording_id
        ).first()
        
        if not recording:
            raise AudioProcessingError(f"Recording {recording_id} not found")
        
        if recording.status != RecordingStatus.UPLOADED:
            logger.warning(f"Recording {recording_id} status is {recording.status}, skipping")
            return {
                'status': 'skipped',
                'message': f'Recording status is {recording.status}',
                'recording_id': recording_id,
                'chunks_created': 0
            }
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 20, 'total': 100, 'status': 'Processing audio...'}
        )
        
        # Process the recording
        audio_chunks = audio_chunking_service.process_recording(
            recording_id=recording_id,
            file_path=recording.file_path,
            db=db
        )
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 90, 'total': 100, 'status': 'Finalizing...'}
        )
        
        # Prepare result
        result = {
            'status': 'success',
            'message': f'Successfully processed recording into {len(audio_chunks)} chunks',
            'recording_id': recording_id,
            'chunks_created': len(audio_chunks),
            'chunk_details': [
                {
                    'chunk_id': chunk.id,
                    'chunk_index': chunk.chunk_index,
                    'duration': chunk.duration,
                    'start_time': chunk.start_time,
                    'end_time': chunk.end_time
                }
                for chunk in audio_chunks
            ]
        }
        
        logger.info(f"Successfully completed audio processing for recording {recording_id}")
        return result
        
    except AudioProcessingError as e:
        logger.error(f"Audio processing error for recording {recording_id}: {e}")
        
        # Update recording status to failed
        try:
            recording = db.query(VoiceRecording).filter(
                VoiceRecording.id == recording_id
            ).first()
            if recording:
                recording.status = RecordingStatus.FAILED
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update recording status: {db_error}")
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'recording_id': recording_id}
        )
        
        return {
            'status': 'failed',
            'message': str(e),
            'recording_id': recording_id,
            'chunks_created': 0
        }
        
    except Exception as e:
        logger.error(f"Unexpected error processing recording {recording_id}: {e}")
        
        # Update recording status to failed
        try:
            recording = db.query(VoiceRecording).filter(
                VoiceRecording.id == recording_id
            ).first()
            if recording:
                recording.status = RecordingStatus.FAILED
                db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update recording status: {db_error}")
        
        # Update task state
        self.update_state(
            state='FAILURE',
            meta={'error': str(e), 'recording_id': recording_id}
        )
        
        return {
            'status': 'failed',
            'message': f'Unexpected error: {str(e)}',
            'recording_id': recording_id,
            'chunks_created': 0
        }
        
    finally:
        db.close()


@celery_app.task(name="batch_process_recordings")
def batch_process_recordings(recording_ids: List[int]) -> dict:
    """
    Process multiple recordings in batch.
    
    Args:
        recording_ids: List of VoiceRecording IDs to process
        
    Returns:
        dict: Batch processing results
    """
    logger.info(f"Starting batch processing for {len(recording_ids)} recordings")
    
    results = {
        'total_recordings': len(recording_ids),
        'successful': 0,
        'failed': 0,
        'skipped': 0,
        'details': []
    }
    
    for recording_id in recording_ids:
        try:
            # Process each recording
            result = process_audio_recording.delay(recording_id)
            task_result = result.get(timeout=600)  # 10 minute timeout per recording
            
            results['details'].append(task_result)
            
            if task_result['status'] == 'success':
                results['successful'] += 1
            elif task_result['status'] == 'failed':
                results['failed'] += 1
            else:
                results['skipped'] += 1
                
        except Exception as e:
            logger.error(f"Failed to process recording {recording_id} in batch: {e}")
            results['failed'] += 1
            results['details'].append({
                'status': 'failed',
                'message': str(e),
                'recording_id': recording_id,
                'chunks_created': 0
            })
    
    logger.info(f"Batch processing completed: {results['successful']} successful, "
                f"{results['failed']} failed, {results['skipped']} skipped")
    
    return results


@celery_app.task(name="reprocess_failed_recordings")
def reprocess_failed_recordings() -> dict:
    """
    Reprocess recordings that failed during previous attempts.
    
    Returns:
        dict: Reprocessing results
    """
    db = get_db()
    
    try:
        # Find failed recordings
        failed_recordings = db.query(VoiceRecording).filter(
            VoiceRecording.status == RecordingStatus.FAILED
        ).all()
        
        if not failed_recordings:
            return {
                'status': 'success',
                'message': 'No failed recordings to reprocess',
                'recordings_found': 0,
                'recordings_processed': 0
            }
        
        recording_ids = [r.id for r in failed_recordings]
        logger.info(f"Found {len(recording_ids)} failed recordings to reprocess")
        
        # Reset status to uploaded for reprocessing
        for recording in failed_recordings:
            recording.status = RecordingStatus.UPLOADED
        db.commit()
        
        # Process in batch
        batch_result = batch_process_recordings.delay(recording_ids)
        result = batch_result.get(timeout=3600)  # 1 hour timeout for batch
        
        return {
            'status': 'success',
            'message': f'Reprocessed {len(recording_ids)} failed recordings',
            'recordings_found': len(recording_ids),
            'recordings_processed': len(recording_ids),
            'batch_result': result
        }
        
    except Exception as e:
        logger.error(f"Failed to reprocess failed recordings: {e}")
        return {
            'status': 'failed',
            'message': str(e),
            'recordings_found': 0,
            'recordings_processed': 0
        }
        
    finally:
        db.close()


@celery_app.task(name="cleanup_orphaned_chunks")
def cleanup_orphaned_chunks() -> dict:
    """
    Clean up audio chunk files that don't have corresponding database records.
    
    Returns:
        dict: Cleanup results
    """
    import os
    from pathlib import Path
    
    db = get_db()
    
    try:
        chunks_dir = Path(settings.UPLOAD_DIR) / "chunks"
        
        if not chunks_dir.exists():
            return {
                'status': 'success',
                'message': 'No chunks directory found',
                'files_removed': 0
            }
        
        # Get all chunk file paths from database
        db_chunk_paths = set()
        chunks = db.query(AudioChunk).all()
        for chunk in chunks:
            db_chunk_paths.add(chunk.file_path)
        
        # Find orphaned files
        orphaned_files = []
        for recording_dir in chunks_dir.iterdir():
            if recording_dir.is_dir():
                for chunk_file in recording_dir.glob("*.wav"):
                    if str(chunk_file) not in db_chunk_paths:
                        orphaned_files.append(chunk_file)
        
        # Remove orphaned files
        removed_count = 0
        for file_path in orphaned_files:
            try:
                file_path.unlink()
                removed_count += 1
                logger.info(f"Removed orphaned chunk file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to remove orphaned file {file_path}: {e}")
        
        return {
            'status': 'success',
            'message': f'Cleaned up {removed_count} orphaned chunk files',
            'files_removed': removed_count,
            'orphaned_files_found': len(orphaned_files)
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup orphaned chunks: {e}")
        return {
            'status': 'failed',
            'message': str(e),
            'files_removed': 0
        }
        
    finally:
        db.close()