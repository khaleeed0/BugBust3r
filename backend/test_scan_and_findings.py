#!/usr/bin/env python3
"""
Test script to create a scan and verify findings are stored in the database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.job import ScanJob, JobStatus
from app.models.target import Target
from app.models.user import User
from app.models.job import Finding
from app.services.scan_service import ScanService
from app.services.task_queue import execute_scan_task
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_scan():
    """Create a test scan on a vulnerable website"""
    db = SessionLocal()
    try:
        # Get or create a test user
        user = db.query(User).filter(User.username == "testuser").first()
        if not user:
            from app.core.security import get_password_hash
            user = User(
                username="testuser",
                email="test@example.com",
                password_hash=get_password_hash("testpass123"),
                role="user"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing user: {user.username}")
        
        # Get or create a test target (vulnerable website)
        target_url = "http://testphp.vulnweb.com"
        target = db.query(Target).filter(Target.url == target_url).first()
        if not target:
            target = Target(
                url=target_url,
                name="Test Vulnerable Website",
                user_id=user.id,
                description="Test website with known vulnerabilities"
            )
            db.add(target)
            db.commit()
            db.refresh(target)
            print(f"✅ Created target: {target.url}")
        else:
            print(f"✅ Using existing target: {target.url}")
        
        # Create a scan job
        job = ScanJob(
            target_id=target.id,
            user_id=user.id,
            status=JobStatus.PENDING.value
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        print(f"✅ Created scan job: {job.job_id}")
        
        # Execute scan synchronously for testing
        print("\n" + "="*80)
        print("Starting scan execution...")
        print("="*80)
        
        scan_service = ScanService(db)
        try:
            result = scan_service.execute_scan(job.id)
            print(f"✅ Scan completed: {result}")
        except Exception as e:
            print(f"❌ Scan failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Refresh job to get latest status
        db.refresh(job)
        print(f"\n✅ Scan job status: {job.status}")
        print(f"✅ Completed at: {job.completed_at}")
        
        # Check findings
        findings = db.query(Finding).filter(Finding.job_id == job.job_id).all()
        print(f"\n✅ Findings stored in database: {len(findings)}")
        
        if findings:
            print("\n" + "="*80)
            print("FINDINGS DETAILS")
            print("="*80)
            for finding in findings[:10]:  # Show first 10
                print(f"\nFinding ID: {finding.id}")
                print(f"  Severity: {finding.severity}")
                print(f"  Location: {finding.location}")
                print(f"  Tool ID: {finding.tool_id}")
                print(f"  Vulnerability: {finding.vulnerability_definition.name if finding.vulnerability_definition else 'N/A'}")
                if finding.evidence:
                    print(f"  Evidence: {finding.evidence[:100]}...")
        
        return job.job_id, len(findings)
        
    finally:
        db.close()

if __name__ == "__main__":
    job_id, findings_count = create_test_scan()
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Job ID: {job_id}")
    print(f"Findings stored: {findings_count}")
    print("="*80)

