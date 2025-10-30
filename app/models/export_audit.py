"""
Export audit log model for tracking data export activities.

This model stores audit trails for all data export operations
to ensure transparency and compliance with data governance requirements.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.database import Base


class ExportAuditLog(Base):
    """Audit log for data export operations."""
    
    __tablename__ = "export_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    export_id = Column(String(255), nullable=False, index=True)  # UUID for export operation
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    export_type = Column(String(50), nullable=False, index=True)  # 'dataset' or 'metadata'
    format = Column(String(20), nullable=False)  # Export format (json, csv, etc.)
    filters_applied = Column(JSON, default=dict)  # Filters used in the export
    records_exported = Column(Integer, nullable=False, default=0)
    file_size_bytes = Column(BigInteger, nullable=True)  # Size of exported file
    ip_address = Column(String(45), nullable=True)  # IPv4 or IPv6 address
    user_agent = Column(String(500), nullable=True)  # Browser/client user agent
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", backref="export_audit_logs")