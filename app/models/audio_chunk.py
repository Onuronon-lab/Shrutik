from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
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

    # Export optimization fields
    transcript_count = Column(Integer, default=0, nullable=False, index=True)
    ready_for_export = Column(Boolean, default=False, nullable=False, index=True)
    consensus_quality = Column(Float, default=0.0, nullable=False)
    consensus_transcript_id = Column(
        Integer,
        ForeignKey("transcriptions.id", use_alter=True, name="fk_consensus_transcript"),
        nullable=True,
    )
    consensus_failed_count = Column(Integer, default=0, nullable=False)

    # Relationships
    recording = relationship("VoiceRecording", back_populates="audio_chunks")
    transcriptions = relationship(
        "Transcription",
        back_populates="chunk",
        foreign_keys="Transcription.chunk_id",
        overlaps="consensus_transcript",
    )
    consensus_transcript = relationship(
        "Transcription",
        foreign_keys=[consensus_transcript_id],
        overlaps="transcriptions",
    )
