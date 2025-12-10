#!/usr/bin/env python3
"""
Script to verify scan data in the database
Checks if scans are working and retrieves findings and tool outputs
"""
import sys
import os
import json
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.job import ScanJob, Finding, ToolExecution, JobStatus
from app.models.target import Target
from app.models.tool import Tool
from sqlalchemy import func, case

def verify_scans():
    """Verify scans are working and show data"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("SCAN DATA VERIFICATION")
        print("=" * 80)
        print()
        
        # 1. Check total scans
        total_scans = db.query(ScanJob).count()
        completed_scans = db.query(ScanJob).filter(ScanJob.status == JobStatus.COMPLETED.value).count()
        failed_scans = db.query(ScanJob).filter(ScanJob.status == JobStatus.FAILED.value).count()
        running_scans = db.query(ScanJob).filter(ScanJob.status == JobStatus.RUNNING.value).count()
        
        print(f"📊 SCAN STATISTICS:")
        print(f"   Total Scans: {total_scans}")
        print(f"   ✅ Completed: {completed_scans}")
        print(f"   ❌ Failed: {failed_scans}")
        print(f"   🔄 Running: {running_scans}")
        print()
        
        # 2. Check findings
        total_findings = db.query(Finding).count()
        findings_by_severity = db.query(
            Finding.severity,
            func.count(Finding.id).label('count')
        ).group_by(Finding.severity).all()
        
        print(f"🔍 FINDINGS STATISTICS:")
        print(f"   Total Findings: {total_findings}")
        if findings_by_severity:
            for severity, count in findings_by_severity:
                print(f"   - {severity.upper()}: {count}")
        print()
        
        # 3. Check tool executions
        total_executions = db.query(ToolExecution).count()
        executions_by_stage = db.query(
            ToolExecution.stage_number,
            ToolExecution.stage_name,
            func.count(ToolExecution.id).label('count'),
            func.sum(case((ToolExecution.status == 'completed', 1), else_=0)).label('completed'),
            func.sum(case((ToolExecution.status == 'failed', 1), else_=0)).label('failed')
        ).group_by(ToolExecution.stage_number, ToolExecution.stage_name).order_by(ToolExecution.stage_number).all()
        
        print(f"🛠️  TOOL EXECUTIONS:")
        print(f"   Total Executions: {total_executions}")
        if executions_by_stage:
            for stage_num, stage_name, count, completed, failed in executions_by_stage:
                print(f"   Stage {stage_num}: {stage_name}")
                print(f"      Total: {count}, Completed: {completed}, Failed: {failed}")
        print()
        
        # 4. Get recent scans with details
        print("=" * 80)
        print("RECENT SCANS (Last 5):")
        print("=" * 80)
        print()
        
        recent_scans = db.query(ScanJob)\
            .order_by(ScanJob.created_at.desc())\
            .limit(5)\
            .all()
        
        for scan in recent_scans:
            target = db.query(Target).filter(Target.id == scan.target_id).first()
            findings_count = db.query(Finding).filter(Finding.job_id == scan.job_id).count()
            executions_count = db.query(ToolExecution).filter(ToolExecution.job_id == scan.job_id).count()
            
            print(f"📋 Job ID: {scan.job_id}")
            print(f"   Target: {target.url if target else 'Unknown'}")
            print(f"   Status: {scan.status}")
            print(f"   Created: {scan.created_at}")
            print(f"   Completed: {scan.completed_at or 'N/A'}")
            print(f"   Findings: {findings_count}")
            print(f"   Tool Executions: {executions_count}")
            
            # Show stages
            executions = db.query(ToolExecution)\
                .filter(ToolExecution.job_id == scan.job_id)\
                .order_by(ToolExecution.stage_number)\
                .all()
            
            if executions:
                print(f"   Stages:")
                for exec in executions:
                    tool = db.query(Tool).filter(Tool.id == exec.tool_id).first()
                    status_icon = "✅" if exec.status == "completed" else "❌" if exec.status == "failed" else "🔄"
                    print(f"      {status_icon} Stage {exec.stage_number}: {exec.stage_name} ({tool.display_name if tool else 'Unknown'})")
                    if exec.execution_time:
                        print(f"         Execution Time: {exec.execution_time}s")
                    if exec.error:
                        print(f"         Error: {exec.error[:100]}...")
            print()
        
        # 5. Show sample findings
        if total_findings > 0:
            print("=" * 80)
            print("SAMPLE FINDINGS (Last 5):")
            print("=" * 80)
            print()
            
            sample_findings = db.query(Finding)\
                .order_by(Finding.first_seen_at.desc())\
                .limit(5)\
                .all()
            
            for finding in sample_findings:
                vuln_def = finding.vulnerability_definition
                tool = finding.tool
                print(f"🔎 Finding ID: {finding.id}")
                print(f"   Vulnerability: {vuln_def.name if vuln_def else 'Unknown'}")
                print(f"   Severity: {finding.severity.value.upper()}")
                print(f"   Tool: {tool.display_name if tool else 'Unknown'}")
                print(f"   Location: {finding.location or 'N/A'}")
                print(f"   Status: {finding.status.value}")
                print()
        
        # 6. Show sample tool outputs
        if total_executions > 0:
            print("=" * 80)
            print("SAMPLE TOOL OUTPUTS (Last 3):")
            print("=" * 80)
            print()
            
            sample_executions = db.query(ToolExecution)\
                .order_by(ToolExecution.completed_at.desc())\
                .limit(3)\
                .all()
            
            for exec in sample_executions:
                tool = db.query(Tool).filter(Tool.id == exec.tool_id).first()
                print(f"🛠️  Execution ID: {exec.id}")
                print(f"   Stage: {exec.stage_name}")
                print(f"   Tool: {tool.display_name if tool else 'Unknown'}")
                print(f"   Status: {exec.status}")
                print(f"   Execution Time: {exec.execution_time or 'N/A'}s")
                
                if exec.output:
                    try:
                        output_data = json.loads(exec.output)
                        print(f"   Output Keys: {list(output_data.keys())[:5]}...")
                    except:
                        print(f"   Output Size: {len(exec.output)} chars")
                
                if exec.error:
                    print(f"   Error: {exec.error[:200]}...")
                print()
        
        print("=" * 80)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_scans()

