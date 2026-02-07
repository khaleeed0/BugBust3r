"""
Reports endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from app.db.database import get_db
from app.models.job import ScanJob, Finding, Report, ToolExecution, JobStatus
from app.models.target import Target
from app.models.user import User
from app.models.tool import Tool
from app.api.v1.endpoints.auth import get_current_user
from collections import defaultdict
import json

router = APIRouter()


class ReportSummary(BaseModel):
    job_id: UUID
    target_url: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    findings_count: int
    findings_summary: Dict[str, Any]


class FullReport(BaseModel):
    job_id: UUID
    target_url: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime]
    findings: List[Dict[str, Any]]
    reports: List[Dict[str, Any]]
    stages: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None


@router.get("", response_model=List[ReportSummary])
async def get_reports(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all reports for current user"""
    jobs = db.query(ScanJob)\
        .filter(
            ScanJob.user_id == current_user.id,
            ScanJob.status.in_([JobStatus.COMPLETED.value, JobStatus.FAILED.value])
        )\
        .order_by(ScanJob.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    reports = []
    for job in jobs:
        target = db.query(Target).filter(Target.id == job.target_id).first()
        
        findings = db.query(Finding)\
            .filter(Finding.job_id == job.job_id)\
            .all()
        
        # Generate findings summary with additional fields for frontend
        findings_by_tool = defaultdict(list)
        for finding in findings:
            tool_name = finding.tool.name if finding.tool else "unknown"
            findings_by_tool[tool_name].append(finding)
        
        # Count findings by type for summary
        subdomains_found = len([f for f in findings if f.vulnerability_definition and "Subdomain" in f.vulnerability_definition.name])
        http_services = len([f for f in findings if f.vulnerability_definition and "HTTP Service" in f.vulnerability_definition.name])
        directories_found = len([f for f in findings if f.vulnerability_definition and "Directory" in f.vulnerability_definition.name])
        security_alerts = len([f for f in findings if f.tool and f.tool.name == 'zap'])
        vulnerabilities = len([f for f in findings if f.tool and f.tool.name == 'nuclei'])
        sql_injections = len([f for f in findings if f.tool and f.tool.name == 'sqlmap'])
        addresssanitizer_findings = len([f for f in findings if f.tool and f.tool.name == 'addresssanitizer'])
        
        findings_summary = {
            "total": len(findings),
            "critical": len([f for f in findings if f.severity.value == "critical"]),
            "high": len([f for f in findings if f.severity.value == "high"]),
            "medium": len([f for f in findings if f.severity.value == "medium"]),
            "low": len([f for f in findings if f.severity.value == "low"]),
            "info": len([f for f in findings if f.severity.value == "info"]),
            "new": len([f for f in findings if f.status.value == "new"]),
            "resolved": len([f for f in findings if f.status.value == "resolved"]),
            # Additional fields for frontend
            "subdomains_found": subdomains_found,
            "http_services": http_services,
            "directories_found": directories_found,
            "security_alerts": security_alerts,
            "vulnerabilities": vulnerabilities,
            "sql_injections": sql_injections,
            "addresssanitizer_findings": addresssanitizer_findings
        }
        
        # Count completed stages and total stages
        completed_stages = len(findings_by_tool)
        total_stages = 6  # Fixed number of stages
        tools_used = list(findings_by_tool.keys())
        
        reports.append({
            "job_id": job.job_id,
            "target_url": target.url if target else "Unknown",
            "status": job.status if isinstance(job.status, str) else job.status.value,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
            "findings_count": len(findings),
            "findings_summary": findings_summary,
            "completed_stages": completed_stages,
            "total_stages": total_stages,
            "tools_used": tools_used
        })
    
    return reports


@router.get("/{job_id}", response_model=FullReport)
async def get_report(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full report for a specific job"""
    job = db.query(ScanJob)\
        .filter(ScanJob.job_id == job_id, ScanJob.user_id == current_user.id)\
        .first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    target = db.query(Target).filter(Target.id == job.target_id).first()
    
    findings = db.query(Finding)\
        .filter(Finding.job_id == job_id)\
        .order_by(Finding.first_seen_at)\
        .all()
    
    findings_data = []
    for finding in findings:
        findings_data.append({
            "id": finding.id,
            "severity": finding.severity.value,
            "status": finding.status.value,
            "vulnerability_name": finding.vulnerability_definition.name if finding.vulnerability_definition else "Unknown",
            "tool_name": finding.tool.display_name if finding.tool else "Unknown",
            "location": finding.location,
            "evidence": finding.evidence,
            "confidence": finding.confidence,
            "first_seen_at": finding.first_seen_at.isoformat() if finding.first_seen_at else None,
            "last_seen_at": finding.last_seen_at.isoformat() if finding.last_seen_at else None,
            "description": finding.vulnerability_definition.description if finding.vulnerability_definition else None,
            "recommendation": finding.vulnerability_definition.recommendation if finding.vulnerability_definition else None
        })
    
    # Get tool executions from database (stored outputs)
    tool_executions = db.query(ToolExecution)\
        .filter(ToolExecution.job_id == job_id)\
        .order_by(ToolExecution.stage_number)\
        .all()
    
    # Build stages from tool executions (preferred) or from findings (fallback)
    stages_data = []
    if tool_executions:
        # Use stored tool executions
        for execution in tool_executions:
            try:
                output_data = json.loads(execution.output) if execution.output else {}
            except:
                output_data = {"raw_output": execution.raw_output or ""}
            
            stages_data.append({
                "stage": execution.stage_name,
                "tool_name": execution.tool.display_name if execution.tool else "Unknown",
                "status": execution.status,
                "execution_time": execution.execution_time,
                "order": execution.stage_number,
                "output": output_data,
                "input_data": json.loads(execution.input_data) if execution.input_data else None,
                "error": execution.error
            })
    else:
        # Fallback: Build stages from findings if no executions stored
        findings_by_tool = defaultdict(list)
        for finding in findings:
            tool_name = finding.tool.name if finding.tool else "unknown"
            findings_by_tool[tool_name].append(finding)
        
        stage_mapping = {
            'sublist3r': {'stage': 'Stage 1: Subdomain Enumeration', 'order': 1},
            'httpx': {'stage': 'Stage 2: HTTP Service Detection', 'order': 2},
            'gobuster': {'stage': 'Stage 3: Directory Discovery', 'order': 3},
            'zap': {'stage': 'Stage 4: Web Application Scanning', 'order': 4},
            'nuclei': {'stage': 'Stage 5: Template-Based Scanning', 'order': 5},
            'sqlmap': {'stage': 'Stage 6: SQL Injection Testing', 'order': 6}
        }
        
        for tool_name, tool_findings in findings_by_tool.items():
            tool = tool_findings[0].tool if tool_findings else None
            stage_info = stage_mapping.get(tool_name, {'stage': f'Tool: {tool.display_name if tool else tool_name}', 'order': 99})
            
            output = {
                "findings_count": len(tool_findings),
                "findings": [
                    {
                        "vulnerability": f.vulnerability_definition.name if f.vulnerability_definition else "Unknown",
                        "severity": f.severity.value,
                        "location": f.location,
                        "evidence": f.evidence
                    }
                    for f in tool_findings[:10]
                ]
            }
            
            stages_data.append({
                "stage": stage_info['stage'],
                "tool_name": tool.display_name if tool else tool_name,
                "status": "completed" if tool_findings else "pending",
                "execution_time": None,
                "order": stage_info['order'],
                "output": output
            })
        
        stages_data.sort(key=lambda x: x['order'])
    
    # Get generated reports
    report_files = db.query(Report)\
        .filter(Report.job_id == job_id)\
        .all()
    
    reports_data = []
    for report in report_files:
        reports_data.append({
            "id": report.id,
            "format": report.format,
            "file_path": report.file_path,
            "generated_at": report.generated_at.isoformat()
        })
    
    return {
        "job_id": job.job_id,
        "target_url": target.url if target else "Unknown",
        "status": job.status if isinstance(job.status, str) else job.status.value,
        "created_at": job.created_at,
        "completed_at": job.completed_at,
        "findings": findings_data,
        "reports": reports_data,
        "stages": stages_data,
        "error_message": None  # Could be extracted from job if stored
    }
