from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class ExportDownload(Base):
    __tablename__ = "export_downloads"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(
        String(255), ForeignKey("export_batches.batch_id"), nullable=False, index=True
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    downloaded_at = Column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6
    user_agent = Column(String(500), nullable=True)

    # Relationships
    batch = relationship("ExportBatch", back_populates="downloads")
    user = relationship("User")

    # Composite index for daily download counting
    __table_args__ = (
        Index("ix_export_downloads_user_download_date", "user_id", "downloaded_at"),
    )
