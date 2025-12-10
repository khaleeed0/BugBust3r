"""
Tool model
"""
from sqlalchemy import Column, Integer, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class Tool(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    display_name = Column(String(100), nullable=False)
    docker_image = Column(String(255), nullable=False)
    celery_queue = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # e.g., 'Discovery', 'Scanning'

    # Relationships
    findings = relationship("Finding", back_populates="tool")
    tool_executions = relationship("ToolExecution", back_populates="tool")

