#!/usr/bin/env python3
"""
Complete ZAP tool test - verify it works and saves findings to database
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

def test_zap_complete():
    """Test ZAP tool end-to-end"""
    print("\n" + "="*80)
    print("ZAP TOOL COMPLETE TEST")
    print("="*80)
    
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
        
        # Get or create target
        target_url = "http://testphp.vulnweb.com"
        target = db.query(Target).filter(Target.url == target_url).first()
        if not target:
            target = Target(
                url=target_url,
                name="Test Vulnerable Website",
                user_id=user.id,
                description="Test website for ZAP scanning"
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
        
        print(f"✅ Created scan job: {job.job_id}")
        print(f"Target: {target.url}")
        print("\n" + "="*80)
        print("Running ZAP scan...")
        print("="*80)
        
        # Execute ZAP scan
        scan_service = ScanService(db)
        try:
            result = scan_service.execute_zap_only(job.id)
            print(f"\n✅ ZAP scan completed!")
            print(f"Status: {result.get('status')}")
            print(f"Alert count: {result.get('alert_count', 0)}")
            
            if result.get('error'):
                print(f"⚠️  Error: {result.get('error')[:200]}")
            
            if result.get('alerts'):
                print(f"\nFound {len(result.get('alerts', []))} alerts:")
                for i, alert in enumerate(result.get('alerts', [])[:10], 1):
                    print(f"  {i}. {alert.get('name', 'Unknown')} - Risk: {alert.get('risk', 'Unknown')}")
                    if alert.get('url'):
                        print(f"      URL: {alert.get('url')}")
        except Exception as e:
            print(f"❌ ZAP scan failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Refresh job
        db.refresh(job)
        print(f"\n✅ Scan job status: {job.status}")
        
        # Check findings in database
        findings = db.query(Finding).filter(Finding.job_id == job.job_id).all()
        print(f"\n✅ Findings stored in database: {len(findings)}")
        
        if findings:
            print("\n" + "="*80)
            print("FINDINGS IN DATABASE")
            print("="*80)
            for finding in findings[:10]:
                tool = db.query(Tool).filter(Tool.id == finding.tool_id).first()
                vuln = db.query(VulnerabilityDefinition).filter(VulnerabilityDefinition.id == finding.definition_id).first()
                print(f"\nFinding ID: {finding.id}")
                print(f"  Tool: {tool.display_name if tool else 'Unknown'}")
                print(f"  Vulnerability: {vuln.name if vuln else 'Unknown'}")
                print(f"  Severity: {finding.severity.value}")
                print(f"  Location: {finding.location[:100] if finding.location else 'N/A'}")
                if finding.evidence:
                    print(f"  Evidence: {finding.evidence[:150]}...")
        else:
            print("\n⚠️  No findings stored in database")
        
        return len(findings) > 0
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_zap_complete()
    print("\n" + "="*80)
    if success:
        print("✅ ZAP TEST PASSED - Tool is working and findings are stored!")
    else:
        print("❌ ZAP TEST FAILED - Check errors above")
    print("="*80)
    sys.exit(0 if success else 1)

