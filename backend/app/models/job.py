"""
Job, ScanSchedule, VulnerabilityDefinition, Finding, and Report models
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.db.database import Base


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    status = Column(String(20), default=JobStatus.PENDING.value, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    owner = relationship("User", back_populates="scan_jobs")
    target = relationship("Target", back_populates="scan_jobs")
    findings = relationship("Finding", back_populates="scan_job", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="scan_job", cascade="all, delete-orphan")
    tool_executions = relationship("ToolExecution", back_populates="scan_job", cascade="all, delete-orphan")


class ScanSchedule(Base):
    __tablename__ = "scan_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    schedule_type = Column(String(20), default='weekly')
    is_active = Column(Boolean, default=True)
    next_scan_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="scan_schedules")
    target = relationship("Target", back_populates="scan_schedules")


class VulnerabilityDefinition(Base):
    __tablename__ = "vulnerability_definitions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)

    # Relationships
    findings = relationship("Finding", back_populates="vulnerability_definition")


class FindingSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FindingStatus(str, enum.Enum):
    NEW = "new"
    REOPENED = "reopened"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scan_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, index=True)
    definition_id = Column(Integer, ForeignKey("vulnerability_definitions.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("targets.id"), nullable=False, index=True)
    severity = Column(SQLEnum(FindingSeverity, native_enum=False, create_constraint=False, values_callable=lambda x: [e.value for e in x]), nullable=False, index=True)
    status = Column(SQLEnum(FindingStatus, native_enum=False, create_constraint=False, values_callable=lambda x: [e.value for e in x]), default=FindingStatus.NEW, index=True)
    first_seen_at = Column(DateTime, default=datetime.utcnow, index=True)
    last_seen_at = Column(DateTime, nullable=True)
    location = Column(Text, nullable=True)  # e.g., URL path, IP:Port, filename
    evidence = Column(Text, nullable=True)  # e.g., Server response, code snippet
    confidence = Column(String(20), nullable=True)  # e.g., 'high', 'medium', 'low'
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Relationships
    scan_job = relationship("ScanJob", back_populates="findings")
    tool = relationship("Tool", back_populates="findings")
    vulnerability_definition = relationship("VulnerabilityDefinition", back_populates="findings")
    target = relationship("Target", back_populates="findings")
    assigned_to = relationship("User", back_populates="assigned_findings", foreign_keys=[assigned_to_user_id])


class ToolExecution(Base):
    """Store tool execution outputs and results for each stage"""
    __tablename__ = "tool_executions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scan_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, index=True)
    stage_number = Column(Integer, nullable=False)  # 1-6 for the stages
    stage_name = Column(String(200), nullable=False)  # e.g., "Stage 1: Subdomain Enumeration"
    status = Column(String(20), default="pending")  # pending, running, completed, failed (DB column; keep ≤20 chars)
    execution_time = Column(Integer, nullable=True)  # seconds
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    output = Column(Text, nullable=True)  # JSON string of tool output
    raw_output = Column(Text, nullable=True)  # Raw stdout/stderr
    error = Column(Text, nullable=True)  # Error message if failed
    input_data = Column(Text, nullable=True)  # JSON string of input data passed to this tool

    # Relationships
    scan_job = relationship("ScanJob", back_populates="tool_executions")
    tool = relationship("Tool", back_populates="tool_executions")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("scan_jobs.job_id", ondelete="CASCADE"), nullable=False, index=True)
    format = Column(String(10), nullable=False)  # e.g., 'pdf', 'html'
    file_path = Column(String(500), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    scan_job = relationship("ScanJob", back_populates="reports")
