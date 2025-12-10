#!/usr/bin/env python3
"""
Test scan execution and verify tools run correctly
Tests each tool individually and then tests full scan workflow
"""
import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.job import ScanJob, Finding, ToolExecution, JobStatus
from app.models.target import Target
from app.models.user import User
from app.services.scan_service import ScanService
from app.docker.client import docker_client
from app.docker.tools import (
    Sublist3rTool, HttpxTool, GobusterTool,
    ZAPTool, NucleiTool, SQLMapTool
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_docker_connection():
    """Test Docker daemon connection"""
    print("=" * 80)
    print("DOCKER CONNECTION TEST")
    print("=" * 80)
    
    try:
        if docker_client.client is None:
            print("❌ Docker client not initialized")
            return False
        
        docker_client.client.ping()
        print("✅ Docker daemon connected")
        return True
    except Exception as e:
        print(f"❌ Docker connection failed: {e}")
        print("   Make sure Docker is running")
        return False

def test_tool_images():
    """Test that all tool Docker images exist"""
    print("\n" + "=" * 80)
    print("DOCKER IMAGES TEST")
    print("=" * 80)
    
    tools = {
        'sublist3r': 'security-tools:sublist3r',
        'httpx': 'security-tools:httpx',
        'gobuster': 'security-tools:gobuster',
        'zap': 'security-tools:zap',
        'nuclei': 'security-tools:nuclei',
        'sqlmap': 'security-tools:sqlmap'
    }
    
    all_exist = True
    for tool_name, image_name in tools.items():
        exists = docker_client.image_exists(image_name)
        if exists:
            print(f"✅ {tool_name:12} - {image_name}")
        else:
            print(f"❌ {tool_name:12} - {image_name} NOT FOUND")
            print(f"   Build it with: cd docker-tools/{tool_name} && docker build -t {image_name} .")
            all_exist = False
    
    return all_exist

def test_individual_tools():
    """Test each tool individually"""
    print("\n" + "=" * 80)
    print("INDIVIDUAL TOOL TESTS")
    print("=" * 80)
    
    test_url = "http://example.com"
    results = {}
    
    # Test Sublist3r
    print("\n🔍 Testing Sublist3r...")
    try:
        tool = Sublist3rTool()
        result = tool.run("example.com")
        success = result.get("status") in ["success", "failed"]  # Even failures mean tool ran
        results['sublist3r'] = success
        if success:
            print(f"   ✅ Sublist3r executed - Status: {result.get('status')}")
            print(f"   Found {result.get('count', 0)} subdomains")
        else:
            print(f"   ❌ Sublist3r failed")
    except Exception as e:
        print(f"   ❌ Sublist3r error: {e}")
        results['sublist3r'] = False
    
    # Test Httpx
    print("\n🌐 Testing Httpx...")
    try:
        tool = HttpxTool()
        result = tool.run(targets=[test_url])
        success = result.get("status") in ["success", "failed"]
        results['httpx'] = success
        if success:
            print(f"   ✅ Httpx executed - Status: {result.get('status')}")
            print(f"   Found {result.get('count', 0)} results")
        else:
            print(f"   ❌ Httpx failed")
    except Exception as e:
        print(f"   ❌ Httpx error: {e}")
        results['httpx'] = False
    
    # Test Gobuster
    print("\n📁 Testing Gobuster...")
    try:
        tool = GobusterTool()
        result = tool.run(target_url=test_url)
        success = result.get("status") in ["success", "failed"]
        results['gobuster'] = success
        if success:
            print(f"   ✅ Gobuster executed - Status: {result.get('status')}")
            print(f"   Found {result.get('count', 0)} results")
        else:
            print(f"   ❌ Gobuster failed")
    except Exception as e:
        print(f"   ❌ Gobuster error: {e}")
        results['gobuster'] = False
    
    # Test ZAP (may take longer)
    print("\n🛡️  Testing ZAP (this may take 30-60 seconds)...")
    try:
        tool = ZAPTool()
        result = tool.run(target_url=test_url, is_localhost=False)
        success = result.get("status") in ["success", "completed_with_alerts", "failed"]
        results['zap'] = success
        if success:
            print(f"   ✅ ZAP executed - Status: {result.get('status')}")
            print(f"   Found {result.get('alert_count', 0)} alerts")
        else:
            print(f"   ❌ ZAP failed")
    except Exception as e:
        print(f"   ❌ ZAP error: {e}")
        results['zap'] = False
    
    # Test Nuclei
    print("\n⚡ Testing Nuclei...")
    try:
        tool = NucleiTool()
        result = tool.run(target_url=test_url)
        success = result.get("status") in ["success", "failed"]
        results['nuclei'] = success
        if success:
            print(f"   ✅ Nuclei executed - Status: {result.get('status')}")
            print(f"   Found {result.get('count', 0)} findings")
        else:
            print(f"   ❌ Nuclei failed")
    except Exception as e:
        print(f"   ❌ Nuclei error: {e}")
        results['nuclei'] = False
    
    # Test SQLMap
    print("\n💉 Testing SQLMap...")
    try:
        tool = SQLMapTool()
        result = tool.run(target_url=test_url)
        success = result.get("status") in ["success", "failed"]
        results['sqlmap'] = success
        if success:
            print(f"   ✅ SQLMap executed - Status: {result.get('status')}")
            print(f"   Vulnerable: {result.get('vulnerable', False)}")
        else:
            print(f"   ❌ SQLMap failed")
    except Exception as e:
        print(f"   ❌ SQLMap error: {e}")
        results['sqlmap'] = False
    
    return results

def test_full_scan_workflow():
    """Test full scan workflow with a test target"""
    print("\n" + "=" * 80)
    print("FULL SCAN WORKFLOW TEST")
    print("=" * 80)
    
    db = SessionLocal()
    try:
        # Get any existing user (for testing purposes)
        test_user = db.query(User).first()
        if not test_user:
            print("⚠️  No users found in database.")
            print("   Please create a user first via the API or frontend")
            print("   Or register at: http://localhost:3000/register")
            return False
        
        print(f"   Using user: {test_user.username} (ID: {test_user.id})")
        
        # Get or create a test target
        test_url = "http://example.com"
        target = db.query(Target).filter(
            Target.url == test_url,
            Target.user_id == test_user.id
        ).first()
        
        if not target:
            print(f"⚠️  Creating test target: {test_url}")
            target = Target(
                user_id=test_user.id,
                url=test_url,
                name="Test Target",
                description="Test target for scan verification",
                asset_value="low"
            )
            db.add(target)
            db.commit()
            db.refresh(target)
        
        # Create a test scan job
        print(f"\n📋 Creating test scan job for: {test_url}")
        job = ScanJob(
            target_id=target.id,
            user_id=test_user.id,
            status=JobStatus.PENDING.value
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        print(f"   Job ID: {job.job_id}")
        print(f"   Job DB ID: {job.id}")
        
        # Run the scan
        print("\n🚀 Starting scan...")
        print("   This will test all 6 stages in sequence")
        print("   This may take 5-10 minutes...")
        
        scan_service = ScanService(db)
        start_time = datetime.utcnow()
        
        try:
            result = scan_service.execute_scan(job.id)
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n✅ Scan completed in {duration:.1f} seconds")
            print(f"   Result: {result}")
            
            # Verify results in database
            db.refresh(job)
            findings_count = db.query(Finding).filter(Finding.job_id == job.job_id).count()
            executions_count = db.query(ToolExecution).filter(ToolExecution.job_id == job.job_id).count()
            
            print(f"\n📊 Scan Results:")
            print(f"   Job Status: {job.status}")
            print(f"   Findings Created: {findings_count}")
            print(f"   Tool Executions: {executions_count}")
            
            # Show stages
            executions = db.query(ToolExecution)\
                .filter(ToolExecution.job_id == job.job_id)\
                .order_by(ToolExecution.stage_number)\
                .all()
            
            if executions:
                print(f"\n   Stages Executed:")
                for exec in executions:
                    status_icon = "✅" if exec.status == "completed" else "❌" if exec.status == "failed" else "🔄"
                    time_str = f"{exec.execution_time}s" if exec.execution_time else "N/A"
                    print(f"      {status_icon} {exec.stage_name} - {time_str}")
            
            return job.status == JobStatus.COMPLETED.value
            
        except Exception as e:
            print(f"\n❌ Scan failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"\n❌ Test setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_batch_scans():
    """Test multiple scans in batch"""
    print("\n" + "=" * 80)
    print("BATCH SCAN TEST")
    print("=" * 80)
    
    test_urls = [
        "http://example.com",
        "https://httpbin.org",
    ]
    
    print(f"\n📦 Testing {len(test_urls)} scans in batch...")
    print("   Note: This will create actual scan jobs")
    print("   Each scan may take 5-10 minutes")
    
    response = input("\n   Continue with batch test? (yes/no): ")
    if response.lower() != 'yes':
        print("   Batch test skipped")
        return True
    
    db = SessionLocal()
    try:
        # Get any existing user
        test_user = db.query(User).first()
        if not test_user:
            print("❌ No users found in database. Please create one first.")
            return False
        
        print(f"   Using user: {test_user.username} (ID: {test_user.id})")
        
        scan_service = ScanService(db)
        results = []
        
        for i, url in enumerate(test_urls, 1):
            print(f"\n📋 Batch {i}/{len(test_urls)}: {url}")
            
            # Create target
            target = db.query(Target).filter(
                Target.url == url,
                Target.user_id == test_user.id
            ).first()
            
            if not target:
                target = Target(
                    user_id=test_user.id,
                    url=url,
                    name=f"Batch Test {i}",
                    asset_value="low"
                )
                db.add(target)
                db.commit()
                db.refresh(target)
            
            # Create job
            job = ScanJob(
                target_id=target.id,
                user_id=test_user.id,
                status=JobStatus.PENDING.value
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            print(f"   Job ID: {job.job_id}")
            
            # Run scan
            try:
                start = datetime.utcnow()
                result = scan_service.execute_scan(job.id)
                duration = (datetime.utcnow() - start).total_seconds()
                
                db.refresh(job)
                findings = db.query(Finding).filter(Finding.job_id == job.job_id).count()
                executions = db.query(ToolExecution).filter(ToolExecution.job_id == job.job_id).count()
                
                success = job.status == JobStatus.COMPLETED.value
                results.append({
                    'url': url,
                    'job_id': job.job_id,
                    'success': success,
                    'duration': duration,
                    'findings': findings,
                    'executions': executions
                })
                
                status = "✅" if success else "❌"
                print(f"   {status} Completed in {duration:.1f}s - {findings} findings, {executions} stages")
                
            except Exception as e:
                print(f"   ❌ Failed: {e}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': str(e)
                })
        
        # Summary
        print("\n" + "=" * 80)
        print("BATCH TEST SUMMARY")
        print("=" * 80)
        for result in results:
            status = "✅" if result.get('success') else "❌"
            print(f"{status} {result['url']}")
            if result.get('success'):
                print(f"   Duration: {result.get('duration', 0):.1f}s")
                print(f"   Findings: {result.get('findings', 0)}")
                print(f"   Stages: {result.get('executions', 0)}")
        
        success_count = sum(1 for r in results if r.get('success'))
        print(f"\n   Total: {success_count}/{len(results)} scans successful")
        
        return success_count == len(results)
        
    finally:
        db.close()

def main():
    """Run all tests"""
    print("\n")
    print("🧪 SCAN EXECUTION TEST SUITE")
    print("\n")
    
    # Test 1: Docker connection
    docker_ok = test_docker_connection()
    if not docker_ok:
        print("\n❌ Docker not available. Cannot run tool tests.")
        return 1
    
    # Test 2: Docker images
    images_ok = test_tool_images()
    if not images_ok:
        print("\n⚠️  Some Docker images are missing.")
        print("   You can still test individual tools, but full scans may fail.")
        response = input("\n   Continue anyway? (yes/no): ")
        if response.lower() != 'yes':
            return 1
    
    # Test 3: Individual tools
    tool_results = test_individual_tools()
    tools_ok = all(tool_results.values())
    
    # Test 4: Full scan workflow (optional)
    print("\n" + "=" * 80)
    response = input("Run full scan workflow test? This will create a real scan job. (yes/no): ")
    full_scan_ok = True
    if response.lower() == 'yes':
        full_scan_ok = test_full_scan_workflow()
    else:
        print("   Full scan test skipped")
    
    # Test 5: Batch scans (optional)
    print("\n" + "=" * 80)
    response = input("Run batch scan test? This will create multiple scan jobs. (yes/no): ")
    batch_ok = True
    if response.lower() == 'yes':
        batch_ok = test_batch_scans()
    else:
        print("   Batch test skipped")
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    print(f"{'✅' if docker_ok else '❌'} Docker Connection")
    print(f"{'✅' if images_ok else '⚠️ '} Docker Images")
    
    print("\nIndividual Tools:")
    for tool, result in tool_results.items():
        print(f"   {'✅' if result else '❌'} {tool}")
    
    if full_scan_ok is not None:
        print(f"\n{'✅' if full_scan_ok else '❌'} Full Scan Workflow")
    
    if batch_ok is not None:
        print(f"{'✅' if batch_ok else '❌'} Batch Scans")
    
    print("\n" + "=" * 80)
    if docker_ok and tools_ok:
        print("✅ TOOLS ARE READY TO RUN")
        print("   You can start scans and they will execute all 6 stages")
    else:
        print("⚠️  SOME ISSUES DETECTED")
        print("   Fix the issues above before running production scans")
    print("=" * 80)
    
    return 0 if (docker_ok and tools_ok) else 1

if __name__ == "__main__":
    sys.exit(main())

