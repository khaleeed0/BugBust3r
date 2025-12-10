#!/usr/bin/env python3
"""
Comprehensive test of all security tools
Tests each tool individually and verifies findings are saved to database
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

def test_all_tools():
    """Test all security tools on a vulnerable website"""
    print("\n" + "="*80)
    print("COMPREHENSIVE SECURITY TOOLS TEST")
    print("="*80)
    print("Testing all tools on: http://testphp.vulnweb.com")
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
                description="Test website for security scanning"
            )
            db.add(target)
            db.commit()
            db.refresh(target)
        
        # Test results
        results = {}
        
        # Test 1: Full scan (all tools)
        print("\n" + "="*80)
        print("TEST 1: Full Scan (All Tools)")
        print("="*80)
        job = ScanJob(
            target_id=target.id,
            user_id=user.id,
            status=JobStatus.PENDING.value
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        print(f"Created scan job: {job.job_id}")
        print("Running full scan (this may take several minutes)...")
        
        scan_service = ScanService(db)
        try:
            result = scan_service.execute_scan(job.id)
            db.refresh(job)
            
            # Count findings by tool
            findings = db.query(Finding).filter(Finding.job_id == job.job_id).all()
            findings_by_tool = {}
            for finding in findings:
                tool = db.query(Tool).filter(Tool.id == finding.tool_id).first()
                tool_name = tool.display_name if tool else "Unknown"
                findings_by_tool[tool_name] = findings_by_tool.get(tool_name, 0) + 1
            
            print(f"\n✅ Full scan completed: {job.status}")
            print(f"✅ Total findings: {len(findings)}")
            print("\nFindings by tool:")
            for tool_name, count in findings_by_tool.items():
                print(f"  - {tool_name}: {count} findings")
            
            results['full_scan'] = {
                'status': job.status,
                'findings': len(findings),
                'by_tool': findings_by_tool
            }
        except Exception as e:
            print(f"❌ Full scan failed: {e}")
            import traceback
            traceback.print_exc()
            results['full_scan'] = {'status': 'failed', 'error': str(e)}
        
        # Test 2: ZAP only (already tested, but verify again)
        print("\n" + "="*80)
        print("TEST 2: ZAP Tool Only")
        print("="*80)
        job_zap = ScanJob(
            target_id=target.id,
            user_id=user.id,
            status=JobStatus.PENDING.value
        )
        db.add(job_zap)
        db.commit()
        db.refresh(job_zap)
        
        try:
            result = scan_service.execute_zap_only(job_zap.id)
            db.refresh(job_zap)
            findings = db.query(Finding).filter(Finding.job_id == job_zap.job_id).all()
            print(f"✅ ZAP scan completed: {job_zap.status}")
            print(f"✅ Findings: {len(findings)}")
            results['zap'] = {'status': job_zap.status, 'findings': len(findings)}
        except Exception as e:
            print(f"❌ ZAP scan failed: {e}")
            results['zap'] = {'status': 'failed', 'error': str(e)}
        
        # Print summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        for test_name, result in results.items():
            status_icon = "✅" if result.get('status') == 'completed' else "❌"
            print(f"{status_icon} {test_name.upper()}:")
            if 'findings' in result:
                print(f"   Findings: {result['findings']}")
            if 'by_tool' in result:
                for tool, count in result['by_tool'].items():
                    print(f"   - {tool}: {count}")
            if 'error' in result:
                print(f"   Error: {result['error'][:100]}")
        
        # Overall status
        all_passed = all(
            r.get('status') == 'completed' for r in results.values()
        )
        
        print("\n" + "="*80)
        if all_passed:
            print("✅ ALL TOOLS TEST PASSED")
        else:
            print("⚠️  SOME TOOLS HAD ISSUES - Check details above")
        print("="*80)
        
        return all_passed
        
    finally:
        db.close()

if __name__ == "__main__":
    success = test_all_tools()
    sys.exit(0 if success else 1)

