#!/usr/bin/env python3
"""
Script to manually reprocess a recording and create chunks.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.services.audio_processing_service import audio_chunking_service
from app.models.voice_recording import VoiceRecording, RecordingStatus

def reprocess_recording(recording_id: int):
    """Reprocess a recording to create chunks."""
    db = SessionLocal()
    try:
        # Get the recording
        recording = db.query(VoiceRecording).filter(VoiceRecording.id == recording_id).first()
        if not recording:
            print(f"Recording {recording_id} not found")
            return
        
        print(f"Processing recording {recording_id}: {recording.file_path}")
        
        # Process the recording
        chunks = audio_chunking_service.process_recording(
            recording_id=recording.id,
            file_path=recording.file_path,
            db=db
        )
        
        # Update recording status
        recording.status = RecordingStatus.CHUNKED
        db.commit()
        
        print(f"Successfully created {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            print(f"  Chunk {i}: {chunk.file_path} ({chunk.duration:.2f}s)")
            
    except Exception as e:
        print(f"Error processing recording: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    recording_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    reprocess_recording(recording_id)