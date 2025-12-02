import enum

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class RecordingStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    CHUNKED = "chunked"
    FAILED = "failed"


class VoiceRecording(Base):
    __tablename__ = "voice_recordings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"), nullable=False, index=True)
    language_id = Column(
        Integer, ForeignKey("languages.id"), nullable=False, index=True
    )
    file_path = Column(String(500), nullable=False)
    duration = Column(Float, nullable=False)  # Duration in seconds
    status = Column(
        Enum(RecordingStatus),
        default=RecordingStatus.UPLOADED,
        nullable=False,
        index=True,
    )
    meta_data = Column(JSON, default=dict)  # Audio quality, format, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="voice_recordings")
    script = relationship("Script", back_populates="voice_recordings")
    language = relationship("Language", back_populates="voice_recordings")
    audio_chunks = relationship("AudioChunk", back_populates="recording")
