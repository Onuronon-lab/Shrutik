from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Language(Base):
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(10), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    scripts = relationship("Script", back_populates="language")
    voice_recordings = relationship("VoiceRecording", back_populates="language")
    transcriptions = relationship("Transcription", back_populates="language")
