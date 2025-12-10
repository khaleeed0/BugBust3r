"""
Target model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Target(Base):
    __tablename__ = "targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(500), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    asset_value = Column(String(50), nullable=True)  # e.g., 'critical', 'high', 'low'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="targets")
    scan_jobs = relationship("ScanJob", back_populates="target")
    scan_schedules = relationship("ScanSchedule", back_populates="target")
    findings = relationship("Finding", back_populates="target")

