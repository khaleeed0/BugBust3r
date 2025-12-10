"""
User model
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default='user')
    api_key = Column(String(255), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    targets = relationship("Target", back_populates="owner", cascade="all, delete-orphan")
    scan_jobs = relationship("ScanJob", back_populates="owner")
    scan_schedules = relationship("ScanSchedule", back_populates="owner")
    assigned_findings = relationship("Finding", back_populates="assigned_to", foreign_keys="Finding.assigned_to_user_id")
