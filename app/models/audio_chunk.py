from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class AudioChunk(Base):
    __tablename__ = "audio_chunks"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(
        Integer, ForeignKey("voice_recordings.id"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)  # Order within the recording
    file_path = Column(String(500), nullable=False)
    start_time = Column(Float, nullable=False)  # Start time in seconds
    end_time = Column(Float, nullable=False)  # End time in seconds
    duration = Column(Float, nullable=False)  # Duration in seconds
    sentence_hint = Column(Text, nullable=True)  # Optional hint about expected content
    meta_data = Column(JSON, default=dict)  # Audio quality, processing info, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    recording = relationship("VoiceRecording", back_populates="audio_chunks")
    transcriptions = relationship("Transcription", back_populates="chunk")
