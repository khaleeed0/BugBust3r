"""
Scan endpoints
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4
from urllib.parse import urlparse

from app.db.database import get_db
from app.models.job import ScanJob, JobStatus
from app.models.target import Target
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user
from app.services.task_queue import execute_scan_task
from app.services.scan_service import ScanService

logger = logging.getLogger(__name__)

router = APIRouter()


class ScanCreate(BaseModel):
    target_id: int


class ScanResponse(BaseModel):
    id: int
    job_id: UUID
    target_id: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    target_url: Optional[str] = None  # Include for convenience

    class Config:
        from_attributes = True


class LocalScanRequest(BaseModel):
    target_url: str
    label: Optional[str] = "Local Host"
    source_path: Optional[str] = None  # Optional path to source code directory to scan


class LocalScanResponse(BaseModel):
    job_id: UUID
    status: str
    target_url: str
    environment: str
    alert_count: int
    alerts: List[Dict[str, Any]]
    results: Optional[Dict[str, Any]] = None  # Tool outputs (addresssanitizer, ghauri)
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None  # Include error message if scan failed


@router.post("", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new scan job"""
    # Verify target exists (allow using targets created by other users, since URL is unique globally)
    target = db.query(Target)\
        .filter(Target.id == scan_data.target_id)\
        .first()
    
    if not target:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target not found"
        )
    
    # Create job
    try:
        job = ScanJob(
            target_id=target.id,
            user_id=current_user.id,
            status=JobStatus.PENDING.value
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Queue the scan task
        try:
            execute_scan_task.delay(job.id)
            logger.info(f"Scan job {job.job_id} queued successfully")
        except Exception as e:
            logger.error(f"Failed to queue scan task: {e}")
            # Update job status to failed if queueing fails
            job.status = JobStatus.FAILED.value
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to queue scan task: {str(e)}"
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create scan job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scan job: {str(e)}"
        )
    
    # Include target URL for response
    response = ScanResponse(
        id=job.id,
        job_id=job.job_id,
        target_id=job.target_id,
        status=job.status,
        created_at=job.created_at,
        completed_at=job.completed_at,
        target_url=target.url
    )
    
    return response


@router.get("", response_model=List[ScanResponse])
async def get_scans(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all scans for current user"""
    scans = db.query(ScanJob)\
        .filter(ScanJob.user_id == current_user.id)\
        .order_by(ScanJob.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    # Include target URL for each scan
    result = []
    for scan in scans:
        target = db.query(Target).filter(Target.id == scan.target_id).first()
        result.append(ScanResponse(
            id=scan.id,
            job_id=scan.job_id,
            target_id=scan.target_id,
            status=scan.status,
            created_at=scan.created_at,
            completed_at=scan.completed_at,
            target_url=target.url if target else None
        ))
    
    return result


@router.post(
    "/local-testing",
    response_model=LocalScanResponse,
    status_code=status.HTTP_201_CREATED
)
async def run_local_testing_scan(
    scan_data: LocalScanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run a development/localhost scan using AddressSanitizer (localhost only)"""
    target_url = scan_data.target_url.strip()
    if not target_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target URL is required"
        )

    parsed = urlparse(target_url if "://" in target_url else f"http://{target_url}")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid http(s) URL"
        )

    hostname = parsed.hostname or ""
    if hostname not in ("localhost", "127.0.0.1"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Local testing scans only support localhost or 127.0.0.1 targets"
        )

    normalized_url = parsed.geturl()
    job = None
    target = None

    try:
        # Find or create target
        target = db.query(Target).filter(Target.url == normalized_url).first()
        if not target:
            target = Target(
                user_id=current_user.id,
                url=normalized_url,
                name=scan_data.label or "Local Host",
                description="Auto-created for LocalHostTesting",
                asset_value="low"
            )
            db.add(target)
            db.commit()
            db.refresh(target)

        # Create scan job
        job = ScanJob(
            target_id=target.id,
            user_id=current_user.id,
            status=JobStatus.PENDING.value
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Execute localhost testing scan (AddressSanitizer + Ghauri; no source path required)
        scan_service = ScanService(db)
        source_path = getattr(scan_data, "source_path", None)
        result = scan_service.execute_localhost_testing(job.id, source_path=source_path)
        db.refresh(job)

        # Format alerts for response (include user-friendly fields for report)
        formatted_alerts = []
        for alert in result.get("alerts", []):
            formatted_alerts.append({
                "name": alert.get("name", "Security Issue"),
                "risk": alert.get("risk", "Info"),
                "description": alert.get("description", ""),
                "solution": alert.get("solution", ""),
                "location": alert.get("location", ""),
                "severity_explanation": alert.get("severity_explanation", ""),
                "evidence": alert.get("evidence", ""),
                "url": alert.get("url", normalized_url),
                "tool": alert.get("tool", "unknown")
            })

        return LocalScanResponse(
            job_id=job.job_id,
            status=result.get("status", job.status),
            target_url=target.url,
            environment="development",
            alert_count=result.get("alert_count", len(formatted_alerts)),
            alerts=formatted_alerts,
            results=result.get("results"),
            created_at=job.created_at,
            completed_at=job.completed_at,
            error=result.get("error")
        )

    except Exception as e:
        logger.error(f"Local testing scan failed: {e}", exc_info=True)
        if db:
            try:
                db.rollback()  # Reset session after any flush/commit error
                if job:
                    job.status = JobStatus.FAILED.value
                    job.completed_at = datetime.utcnow()
                    db.commit()
            except Exception:
                db.rollback()
        # Always return 200 with body so frontend shows the error instead of "request failed 500"
        now = datetime.utcnow()
        return LocalScanResponse(
            job_id=job.job_id if job else uuid4(),
            status="failed",
            target_url=normalized_url,
            environment="development",
            alert_count=0,
            alerts=[],
            results={},
            created_at=job.created_at if job else now,
            completed_at=now,
            error=str(e)
        )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific scan by ID"""
    scan = db.query(ScanJob)\
        .filter(ScanJob.id == scan_id, ScanJob.user_id == current_user.id)\
        .first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    target = db.query(Target).filter(Target.id == scan.target_id).first()
    
    return ScanResponse(
        id=scan.id,
        job_id=scan.job_id,
        target_id=scan.target_id,
        status=scan.status,
        created_at=scan.created_at,
        completed_at=scan.completed_at,
        target_url=target.url if target else None
    )


