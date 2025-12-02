import enum

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class StorageType(str, enum.Enum):
    LOCAL = "local"
    R2 = "r2"


class ExportBatchStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportBatch(Base):
    __tablename__ = "export_batches"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(255), unique=True, nullable=False, index=True)  # UUID
    archive_path = Column(String(500), nullable=False)  # Local or R2 path (.tar.zst)
    storage_type = Column(Enum(StorageType), nullable=False)
    chunk_count = Column(Integer, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)

    # Chunk IDs included in this batch (for tracking and preventing re-export)
    chunk_ids = Column(JSON, nullable=False)

    # Status tracking
    status = Column(
        Enum(ExportBatchStatus),
        default=ExportBatchStatus.PENDING,
        nullable=False,
        index=True,
    )
    exported = Column(Boolean, default=False, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)

    # Metadata
    checksum = Column(String(64), nullable=True)  # SHA256 checksum
    compression_level = Column(Integer, nullable=True)
    format_version = Column(String(10), default="1.0", nullable=False)

    # Audit metadata
    recording_id_range = Column(JSON, nullable=True)  # {"min": 1, "max": 100}
    language_stats = Column(JSON, nullable=True)  # {"Bengali": 60, "Hindi": 40}
    total_duration_seconds = Column(Float, nullable=True)

    # Filter criteria used for this batch (for audit and debugging)
    filter_criteria = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    created_by = relationship("User")
    downloads = relationship("ExportDownload", back_populates="batch")
