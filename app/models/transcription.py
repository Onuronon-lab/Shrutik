from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(Integer, ForeignKey("audio_chunks.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    language_id = Column(Integer, ForeignKey("languages.id"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    quality = Column(Float, default=0.0)      # Quality score (0-1)
    confidence = Column(Float, default=0.0)   # Confidence score (0-1)
    is_consensus = Column(Boolean, default=False, index=True)  # Is this the consensus transcription?
    is_validated = Column(Boolean, default=False, index=True)  # Has been validated
    meta_data = Column(JSON, default=dict)     # Processing info, flags, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    chunk = relationship("AudioChunk", back_populates="transcriptions")
    user = relationship("User", back_populates="transcriptions")
    language = relationship("Language", back_populates="transcriptions")
    quality_reviews = relationship("QualityReview", back_populates="transcription")