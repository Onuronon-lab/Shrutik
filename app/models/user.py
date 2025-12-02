import enum

from sqlalchemy import JSON, Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class UserRole(str, enum.Enum):
    CONTRIBUTOR = "contributor"
    ADMIN = "admin"
    SWORIK_DEVELOPER = "sworik_developer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole), default=UserRole.CONTRIBUTOR, nullable=False, index=True
    )
    meta_data = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    voice_recordings = relationship("VoiceRecording", back_populates="user")
    transcriptions = relationship("Transcription", back_populates="user")
    quality_reviews = relationship("QualityReview", back_populates="reviewer")
