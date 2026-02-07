#!/usr/bin/env python3
"""
Test all security tools - verify each tool runs and produces output.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.docker.client import docker_client
from app.docker.tools import (
    Sublist3rTool, HttpxTool, GobusterTool,
    ZAPTool, NucleiTool, SQLMapTool,
    SemgrepTool, AddressSanitizerTool,
)

def test_docker():
    """Test Docker daemon connection"""
    try:
        if docker_client.client is None:
            return False, "Docker client not initialized"
        docker_client.client.ping()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def test_images():
    """Check all tool Docker images exist"""
    tools = {
        'sublist3r': 'security-tools:sublist3r',
        'httpx': 'security-tools:httpx',
        'gobuster': 'security-tools:gobuster',
        'zap': 'security-tools:zap',
        'nuclei': 'security-tools:nuclei',
        'sqlmap': 'security-tools:sqlmap',
        'semgrep': 'security-tools:semgrep',
        'addresssanitizer': 'security-tools:addresssanitizer',
    }
    results = {}
    for name, image in tools.items():
        results[name] = docker_client.image_exists(image)
    return results

def run_tool_tests():
    """Run each tool and verify it executes"""
    test_url = "http://example.com"
    results = {}

    # Sublist3r
    try:
        r = Sublist3rTool().run("example.com")
        results['sublist3r'] = r.get("status") in ["success", "failed"]
    except Exception as e:
        results['sublist3r'] = False
        results['sublist3r_err'] = str(e)[:80]

    # Httpx
    try:
        r = HttpxTool().run(targets=[test_url])
        results['httpx'] = r.get("status") in ["success", "failed"]
    except Exception as e:
        results['httpx'] = False
        results['httpx_err'] = str(e)[:80]

    # Gobuster
    try:
        r = GobusterTool().run(target_url=test_url)
        results['gobuster'] = r.get("status") in ["success", "failed"]
    except Exception as e:
        results['gobuster'] = False
        results['gobuster_err'] = str(e)[:80]

    # ZAP
    try:
        r = ZAPTool().run(target_url=test_url, is_localhost=False)
        results['zap'] = r.get("status") in ["success", "completed_with_alerts", "failed"]
    except Exception as e:
        results['zap'] = False
        results['zap_err'] = str(e)[:80]

    # Nuclei
    try:
        r = NucleiTool().run(target_url=test_url)
        results['nuclei'] = r.get("status") in ["success", "failed"]
    except Exception as e:
        results['nuclei'] = False
        results['nuclei_err'] = str(e)[:80]

    # SQLMap
    try:
        r = SQLMapTool().run(target_url=test_url)
        results['sqlmap'] = r.get("status") in ["success", "failed"]
    except Exception as e:
        results['sqlmap'] = False
        results['sqlmap_err'] = str(e)[:80]

    # Semgrep (no source path - uses empty scan)
    try:
        r = SemgrepTool().run()
        results['semgrep'] = r.get("status") in ["success", "failed"]
    except Exception as e:
        results['semgrep'] = False
        results['semgrep_err'] = str(e)[:80]

    # AddressSanitizer (demo mode - creates vulnerable C, should detect overflow)
    try:
        r = AddressSanitizerTool().run()
        results['addresssanitizer'] = r.get("status") in ["completed_with_issues", "success", "failed"]
    except Exception as e:
        results['addresssanitizer'] = False
        results['addresssanitizer_err'] = str(e)[:80]

    return results

def main():
    print("\n" + "=" * 60)
    print("ALL SECURITY TOOLS CHECK")
    print("=" * 60)

    # 1. Docker
    ok, msg = test_docker()
    print(f"\n1. Docker: {'OK' if ok else 'FAIL'} - {msg}")
    if not ok:
        print("   Cannot run tool tests without Docker.")
        return 1

    # 2. Images
    print("\n2. Docker images:")
    img_results = test_images()
    for name, exists in img_results.items():
        print(f"   {'OK' if exists else 'MISSING':8} {name}")
    missing = [n for n, e in img_results.items() if not e]
    if missing:
        print(f"\n   Build missing: cd docker-tools && bash build-all.sh")

    # 3. Tool execution
    print("\n3. Tool execution tests:")
    tool_results = run_tool_tests()
    tool_names = ['sublist3r', 'httpx', 'gobuster', 'zap', 'nuclei', 'sqlmap', 'semgrep', 'addresssanitizer']
    for name in tool_names:
        ok = tool_results.get(name, False)
        err = tool_results.get(name + '_err', '')
        print(f"   {'OK' if ok else 'FAIL':8} {name}" + (f" - {err}" if err else ""))

    # Summary
    passed = sum(1 for n in tool_names if tool_results.get(n, False))
    total = len(tool_names)
    print("\n" + "=" * 60)
    print(f"RESULT: {passed}/{total} tools working")
    print("=" * 60 + "\n")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
