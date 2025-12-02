import enum

from sqlalchemy import JSON, Column, DateTime, Enum, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class ReviewDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    FLAGGED = "flagged"


class QualityReview(Base):
    __tablename__ = "quality_reviews"

    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(
        Integer, ForeignKey("transcriptions.id"), nullable=False, index=True
    )
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    decision = Column(Enum(ReviewDecision), nullable=False, index=True)
    rating = Column(Float, nullable=True)  # Optional numeric rating (1-5)
    comment = Column(Text, nullable=True)  # Optional review comment
    meta_data = Column(JSON, default=dict)  # Additional review data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transcription = relationship("Transcription", back_populates="quality_reviews")
    reviewer = relationship("User", back_populates="quality_reviews")
