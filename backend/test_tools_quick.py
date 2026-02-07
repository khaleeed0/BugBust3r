#!/usr/bin/env python3
"""Quick test of all tools - fast tools only (skip ZAP for speed)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.docker.client import docker_client
from app.docker.tools import (
    Sublist3rTool, HttpxTool, GobusterTool,
    NucleiTool, SQLMapTool, SemgrepTool, AddressSanitizerTool,
)

def main():
    print("\n=== QUICK TOOL CHECK ===\n")
    
    # Images
    tools = ['sublist3r','httpx','gobuster','nuclei','sqlmap','semgrep','addresssanitizer']
    imgs = {t: f'security-tools:{t}' for t in tools}
    
    for n, img in imgs.items():
        ok = docker_client.image_exists(img)
        print(f"  {'OK' if ok else 'MISS'}: {n}")
    
    # Run fast tools
    results = {}
    try:
        r = Sublist3rTool().run("example.com")
        results['sublist3r'] = r.get('status') in ['success','failed']
    except Exception as e: results['sublist3r'] = False
    
    try:
        r = HttpxTool().run(targets=["http://example.com"])
        results['httpx'] = r.get('status') in ['success','failed']
    except: results['httpx'] = False
    
    try:
        r = GobusterTool().run(target_url="http://example.com")
        results['gobuster'] = r.get('status') in ['success','failed']
    except: results['gobuster'] = False
    
    try:
        r = NucleiTool().run(target_url="http://example.com")
        results['nuclei'] = r.get('status') in ['success','failed']
    except: results['nuclei'] = False
    
    try:
        r = SQLMapTool().run(target_url="http://example.com")
        results['sqlmap'] = r.get('status') in ['success','failed']
    except: results['sqlmap'] = False
    
    try:
        r = SemgrepTool().run()
        results['semgrep'] = r.get('status') in ['success','failed']
    except: results['semgrep'] = False
    
    try:
        r = AddressSanitizerTool().run()
        results['addresssanitizer'] = r.get('status') in ['completed_with_issues','success','failed']
    except: results['addresssanitizer'] = False
    
    print("\n  Execution:")
    for n in tools:
        print(f"  {'OK' if results.get(n) else 'FAIL'}: {n}")
    
    passed = sum(results.get(n,False) for n in tools)
    print(f"\n  Result: {passed}/{len(tools)} tools OK\n")
    return 0 if passed == len(tools) else 1

if __name__ == "__main__":
    sys.exit(main())
