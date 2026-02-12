#!/usr/bin/env python3
"""
Test script to run Semgrep scan, verify output, and check database storage
"""
import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def register_user():
    """Register a test user"""
    print("📝 Registering test user...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={
            "username": "semgreptest",
            "email": "semgreptest@example.com",
            "password": "test123456"
        }
    )
    if response.status_code == 201:
        print("✓ User registered successfully")
        return response.json()
    elif response.status_code == 400 and "already exists" in response.text.lower():
        print("✓ User already exists, proceeding with login...")
        return None
    else:
        print(f"✗ Registration failed: {response.status_code} - {response.text}")
        return None

def login():
    """Login and get access token"""
    print("🔐 Logging in...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={
            "username": "semgreptest",
            "password": "test123456"
        }
    )
    if response.status_code == 200:
        token_data = response.json()
        print("✓ Login successful")
        return token_data["access_token"]
    else:
        print(f"✗ Login failed: {response.status_code} - {response.text}")
        return None

def create_localhost_scan(token, target_url="http://localhost:3000"):
    """Create a localhost testing scan with Semgrep"""
    print(f"\n🔍 Creating Semgrep scan for {target_url}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(
        f"{BASE_URL}/scans/local-testing",
        headers=headers,
        json={
            "target_url": target_url,
            "label": "Semgrep Test Scan"
        }
    )
    
    if response.status_code == 201:
        scan_data = response.json()
        print(f"✓ Scan created successfully")
        print(f"  Job ID: {scan_data.get('job_id')}")
        print(f"  Status: {scan_data.get('status')}")
        print(f"  Alert Count: {scan_data.get('alert_count', 0)}")
        return scan_data
    else:
        print(f"✗ Scan creation failed: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def get_job_status(token, job_id):
    """Get job status and results"""
    print(f"\n📊 Checking job status for {job_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/jobs/{job_id}/status",
        headers=headers
    )
    
    if response.status_code == 200:
        job_data = response.json()
        print(f"✓ Job Status: {job_data.get('status')}")
        return job_data
    else:
        print(f"✗ Failed to get job status: {response.status_code}")
        return None

def get_report(token, job_id):
    """Get full report for the job"""
    print(f"\n📄 Generating report for job {job_id}...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(
        f"{BASE_URL}/reports/{job_id}",
        headers=headers
    )
    
    if response.status_code == 200:
        report_data = response.json()
        print(f"✓ Report generated successfully")
        return report_data
    else:
        print(f"✗ Failed to get report: {response.status_code}")
        print(f"  Response: {response.text}")
        return None

def display_scan_results(scan_data):
    """Display scan results"""
    print("\n" + "="*60)
    print("📋 SCAN RESULTS")
    print("="*60)
    
    if scan_data:
        print(f"Job ID: {scan_data.get('job_id')}")
        print(f"Status: {scan_data.get('status')}")
        print(f"Target URL: {scan_data.get('target_url')}")
        print(f"Alert Count: {scan_data.get('alert_count', 0)}")
        
        alerts = scan_data.get('alerts', [])
        if alerts:
            print(f"\n🔍 Found {len(alerts)} security findings:")
            for i, alert in enumerate(alerts, 1):
                print(f"\n  Finding #{i}:")
                print(f"    Name: {alert.get('name', 'N/A')}")
                print(f"    Risk: {alert.get('risk', 'N/A')}")
                print(f"    Tool: {alert.get('tool', 'N/A')}")
                print(f"    Description: {alert.get('description', 'N/A')[:100]}...")
        else:
            print("\n⚠️  No alerts found")
        
        results = scan_data.get('results', {})
        if results:
            print(f"\n📊 Tool Results:")
            for tool_name, tool_result in results.items():
                print(f"  {tool_name}:")
                print(f"    Status: {tool_result.get('status', 'N/A')}")
                print(f"    Count: {tool_result.get('count', 0)}")
                if tool_result.get('error'):
                    print(f"    Error: {tool_result.get('error')[:100]}...")

def display_report(report_data):
    """Display report details"""
    print("\n" + "="*60)
    print("📄 REPORT DETAILS")
    print("="*60)
    
    if report_data:
        print(f"Job ID: {report_data.get('job_id')}")
        print(f"Status: {report_data.get('status')}")
        print(f"Target: {report_data.get('target_url')}")
        
        findings = report_data.get('findings', [])
        print(f"\n🔍 Total Findings: {len(findings)}")
        
        # Group by tool
        tool_counts = {}
        for finding in findings:
            tool_name = finding.get('tool_name', 'unknown')
            tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
        
        print(f"\n📊 Findings by Tool:")
        for tool, count in tool_counts.items():
            print(f"  {tool}: {count}")
        
        # Show Semgrep findings specifically
        semgrep_findings = [f for f in findings if f.get('tool_name') == 'semgrep']
        if semgrep_findings:
            print(f"\n🔍 Semgrep Findings ({len(semgrep_findings)}):")
            for i, finding in enumerate(semgrep_findings[:5], 1):  # Show first 5
                print(f"\n  Finding #{i}:")
                print(f"    Name: {finding.get('name', 'N/A')}")
                print(f"    Severity: {finding.get('severity', 'N/A')}")
                print(f"    Location: {finding.get('location', 'N/A')}")
                print(f"    Description: {finding.get('description', 'N/A')[:80]}...")
        
        # Show tool executions
        executions = report_data.get('tool_executions', [])
        if executions:
            print(f"\n⚙️  Tool Executions ({len(executions)}):")
            for exec in executions:
                print(f"  {exec.get('stage_name', 'N/A')}: {exec.get('status', 'N/A')}")

def main():
    print("="*60)
    print("🧪 SEMGREP SCAN TEST")
    print("="*60)
    
    # Step 1: Register user (if needed)
    user = register_user()
    
    # Step 2: Login
    token = login()
    if not token:
        print("✗ Cannot proceed without authentication token")
        sys.exit(1)
    
    # Step 3: Create scan
    scan_data = create_localhost_scan(token)
    if not scan_data:
        print("✗ Cannot proceed without scan data")
        sys.exit(1)
    
    job_id = scan_data.get('job_id')
    
    # Step 4: Display initial results
    display_scan_results(scan_data)
    
    # Step 5: Wait a bit and check job status
    print("\n⏳ Waiting 3 seconds for job to complete...")
    time.sleep(3)
    
    job_status = get_job_status(token, job_id)
    if job_status:
        print(f"  Final Status: {job_status.get('status')}")
    
    # Step 6: Get full report
    report_data = get_report(token, job_id)
    if report_data:
        display_report(report_data)
    
    # Step 7: Verify database storage
    print("\n" + "="*60)
    print("💾 DATABASE VERIFICATION")
    print("="*60)
    
    if report_data:
        findings_count = len(report_data.get('findings', []))
        executions_count = len(report_data.get('tool_executions', []))
        
        print(f"✓ Findings stored in database: {findings_count}")
        print(f"✓ Tool executions stored: {executions_count}")
        
        semgrep_findings = len([f for f in report_data.get('findings', []) if f.get('tool_name') == 'semgrep'])
        print(f"✓ Semgrep findings in database: {semgrep_findings}")
        
        if semgrep_findings > 0:
            print("\n✅ SUCCESS: Semgrep scan completed and findings stored in database!")
        else:
            print("\n⚠️  WARNING: No Semgrep findings found in database")
    else:
        print("✗ Could not verify database storage (report not available)")
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()

