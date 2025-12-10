#!/usr/bin/env python3
"""
Test script to verify all security tools are working correctly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.docker.tools import (
    Sublist3rTool, HttpxTool, GobusterTool, 
    ZAPTool, NucleiTool, SQLMapTool
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sublist3r():
    """Test Sublist3r tool"""
    print("\n" + "="*80)
    print("Testing Sublist3r")
    print("="*80)
    tool = Sublist3rTool()
    result = tool.run("example.com")
    print(f"Status: {result.get('status')}")
    print(f"Exit code: {result.get('exit_code')}")
    print(f"Subdomains found: {result.get('count', 0)}")
    if result.get('error'):
        print(f"Error: {result.get('error')[:200]}")
    return result.get('status') == 'success' or result.get('count', 0) > 0

def test_httpx():
    """Test Httpx tool"""
    print("\n" + "="*80)
    print("Testing Httpx")
    print("="*80)
    tool = HttpxTool()
    result = tool.run(["http://example.com"])
    print(f"Status: {result.get('status')}")
    print(f"Exit code: {result.get('exit_code')}")
    print(f"Results found: {result.get('count', 0)}")
    if result.get('error'):
        print(f"Error: {result.get('error')[:200]}")
    return result.get('status') == 'success' or result.get('count', 0) > 0

def test_gobuster():
    """Test Gobuster tool"""
    print("\n" + "="*80)
    print("Testing Gobuster")
    print("="*80)
    tool = GobusterTool()
    result = tool.run("http://testphp.vulnweb.com")
    print(f"Status: {result.get('status')}")
    print(f"Exit code: {result.get('exit_code')}")
    print(f"Results found: {result.get('count', 0)}")
    if result.get('error'):
        print(f"Error: {result.get('error')[:200]}")
    return result.get('status') == 'success' or result.get('count', 0) > 0

def test_zap():
    """Test ZAP tool"""
    print("\n" + "="*80)
    print("Testing OWASP ZAP")
    print("="*80)
    tool = ZAPTool()
    result = tool.run("http://testphp.vulnweb.com", is_localhost=False)
    print(f"Status: {result.get('status')}")
    print(f"Exit code: {result.get('exit_code')}")
    print(f"Alerts found: {result.get('alert_count', 0)}")
    if result.get('error'):
        print(f"Error: {result.get('error')[:200]}")
    return result.get('status') in ['success', 'completed_with_alerts'] or result.get('alert_count', 0) > 0

def test_nuclei():
    """Test Nuclei tool"""
    print("\n" + "="*80)
    print("Testing Nuclei")
    print("="*80)
    tool = NucleiTool()
    result = tool.run("http://testphp.vulnweb.com")
    print(f"Status: {result.get('status')}")
    print(f"Exit code: {result.get('exit_code')}")
    print(f"Findings found: {result.get('count', 0)}")
    if result.get('error'):
        print(f"Error: {result.get('error')[:200]}")
    return result.get('status') == 'success' or result.get('count', 0) > 0

def test_sqlmap():
    """Test SQLMap tool"""
    print("\n" + "="*80)
    print("Testing SQLMap")
    print("="*80)
    tool = SQLMapTool()
    result = tool.run("http://testphp.vulnweb.com/listproducts.php?cat=1")
    print(f"Status: {result.get('status')}")
    print(f"Exit code: {result.get('exit_code')}")
    print(f"Vulnerable: {result.get('vulnerable', False)}")
    if result.get('error'):
        print(f"Error: {result.get('error')[:200]}")
    return result.get('status') == 'success'

def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SECURITY TOOLS TEST SUITE")
    print("="*80)
    
    results = {}
    results['Sublist3r'] = test_sublist3r()
    results['Httpx'] = test_httpx()
    results['Gobuster'] = test_gobuster()
    results['ZAP'] = test_zap()
    results['Nuclei'] = test_nuclei()
    results['SQLMap'] = test_sqlmap()
    
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    for tool, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {tool}")
    
    all_passed = all(results.values())
    print("\n" + "="*80)
    if all_passed:
        print("✅ All tools are working correctly!")
    else:
        print("⚠️  Some tools have issues. Check errors above.")
    print("="*80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

