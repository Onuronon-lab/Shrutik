import enum

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class DurationCategory(str, enum.Enum):
    SHORT = "2_minutes"
    MEDIUM = "5_minutes"
    LONG = "10_minutes"


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    duration_category = Column(Enum(DurationCategory), nullable=False, index=True)
    language_id = Column(
        Integer, ForeignKey("languages.id"), nullable=False, index=True
    )
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    language = relationship("Language", back_populates="scripts")
    voice_recordings = relationship("VoiceRecording", back_populates="script")
