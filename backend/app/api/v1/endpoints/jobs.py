"""
Job endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.db.database import get_db
from app.models.job import ScanJob, Finding, JobStatus
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from uuid import UUID
import json

router = APIRouter()


class JobStatusResponse(BaseModel):
    id: int
    job_id: UUID
    target_id: int
    target_url: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    findings_count: int = 0
    findings: List[Dict[str, Any]] = []

    class Config:
        from_attributes = True


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get job status and findings"""
    job = db.query(ScanJob)\
        .filter(ScanJob.job_id == job_id, ScanJob.user_id == current_user.id)\
        .first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # Get target URL
    from app.models.target import Target
    target = db.query(Target).filter(Target.id == job.target_id).first()
    
    # Get all findings for this job
    findings = db.query(Finding)\
        .filter(Finding.job_id == job_id)\
        .order_by(Finding.first_seen_at)\
        .all()
    
    # Format findings
    findings_data = []
    for finding in findings:
        findings_data.append({
            "id": finding.id,
            "severity": finding.severity.value,
            "status": finding.status.value,
            "location": finding.location,
            "evidence": finding.evidence,
            "confidence": finding.confidence,
            "first_seen_at": finding.first_seen_at.isoformat() if finding.first_seen_at else None,
            "last_seen_at": finding.last_seen_at.isoformat() if finding.last_seen_at else None,
            "vulnerability_name": finding.vulnerability_definition.name if finding.vulnerability_definition else None,
            "tool_name": finding.tool.name if finding.tool else None
        })
    
    return {
        "id": job.id,
        "job_id": job.job_id,
        "target_id": job.target_id,
        "target_url": target.url if target else None,
        "status": job.status.value,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "findings_count": len(findings),
        "findings": findings_data
    }


