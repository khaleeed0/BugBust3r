#!/usr/bin/env python3
"""
Test ZAP and Nuclei tools and verify findings are saved to database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.job import ScanJob, JobStatus, Finding
from app.models.target import Target
from app.models.user import User
from app.models.tool import Tool
from app.models.job import VulnerabilityDefinition
from app.services.scan_service import ScanService
from app.core.security import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_zap_and_nuclei():
    """Test ZAP and Nuclei on a vulnerable website and verify findings"""
    db = SessionLocal()
    try:
        # Get or create test user
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=get_password_hash("testpass123"),
                role="user"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Create target for vulnerable website
        target_url = "http://testphp.vulnweb.com"
        target = db.query(Target).filter(Target.url == target_url).first()
        if not target:
            target = Target(
                url=target_url,
                name="Test Vulnerable Website",
                user_id=user.id,
                description="Test website for ZAP and Nuclei"
            )
            db.add(target)
            db.commit()
            db.refresh(target)
        
        # Create scan job
        job = ScanJob(
            target_id=target.id,
            user_id=user.id,
            status=JobStatus.PENDING.value
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        print(f"\n{'='*80}")
        print(f"Testing scan on: {target_url}")
        print(f"Job ID: {job.job_id}")
        print(f"{'='*80}\n")
        
        # Execute scan
        scan_service = ScanService(db)
        try:
            result = scan_service.execute_scan(job.id)
            print(f"✅ Scan completed: {result.get('status')}")
        except Exception as e:
            print(f"❌ Scan failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Refresh job
        db.refresh(job)
        print(f"\nScan Status: {job.status}")
        print(f"Completed At: {job.completed_at}")
        
        # Check findings
        findings = db.query(Finding).filter(Finding.job_id == job.job_id).all()
        print(f"\n{'='*80}")
        print(f"FINDINGS SUMMARY")
        print(f"{'='*80}")
        print(f"Total Findings: {len(findings)}")
        
        # Group by tool
        findings_by_tool = {}
        for finding in findings:
            tool = db.query(Tool).filter(Tool.id == finding.tool_id).first()
            tool_name = tool.display_name if tool else f"Tool {finding.tool_id}"
            if tool_name not in findings_by_tool:
                findings_by_tool[tool_name] = []
            findings_by_tool[tool_name].append(finding)
        
        print(f"\nFindings by Tool:")
        for tool_name, tool_findings in findings_by_tool.items():
            print(f"  {tool_name}: {len(tool_findings)} findings")
            for finding in tool_findings[:3]:  # Show first 3
                vuln = db.query(VulnerabilityDefinition).filter(VulnerabilityDefinition.id == finding.definition_id).first()
                print(f"    - {vuln.name if vuln else 'Unknown'} ({finding.severity.value})")
                if finding.location:
                    print(f"      Location: {finding.location[:80]}")
        
        # Check specifically for ZAP and Nuclei findings
        zap_tool = db.query(Tool).filter(Tool.name == "zap").first()
        nuclei_tool = db.query(Tool).filter(Tool.name == "nuclei").first()
        
        zap_findings = []
        nuclei_findings = []
        
        if zap_tool:
            zap_findings = [f for f in findings if f.tool_id == zap_tool.id]
        if nuclei_tool:
            nuclei_findings = [f for f in findings if f.tool_id == nuclei_tool.id]
        
        print(f"\n{'='*80}")
        print(f"ZAP AND NUCLEI RESULTS")
        print(f"{'='*80}")
        print(f"ZAP Findings: {len(zap_findings)}")
        print(f"Nuclei Findings: {len(nuclei_findings)}")
        
        if len(zap_findings) > 0:
            print(f"\n✅ ZAP is working and found {len(zap_findings)} vulnerabilities!")
        else:
            print(f"\n⚠️  ZAP did not find any vulnerabilities (may still be working)")
        
        if len(nuclei_findings) > 0:
            print(f"✅ Nuclei is working and found {len(nuclei_findings)} vulnerabilities!")
        else:
            print(f"⚠️  Nuclei did not find any vulnerabilities (may still be working)")
        
        print(f"\n{'='*80}")
        
        return job.job_id, len(findings), len(zap_findings), len(nuclei_findings)
        
    finally:
        db.close()

if __name__ == "__main__":
    job_id, total_findings, zap_findings, nuclei_findings = test_zap_and_nuclei()
    print(f"\nFinal Results:")
    print(f"  Job ID: {job_id}")
    print(f"  Total Findings: {total_findings}")
    print(f"  ZAP Findings: {zap_findings}")
    print(f"  Nuclei Findings: {nuclei_findings}")


