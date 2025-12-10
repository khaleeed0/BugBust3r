"""Test Semgrep tool directly"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.docker.tools import SemgrepTool

print("Testing Semgrep Tool...")
print("=" * 60)

tool = SemgrepTool()
result = tool.run(target_url='http://localhost:3000')

print(f"Status: {result['status']}")
print(f"Findings count: {result['count']}")
print(f"Exit code: {result.get('exit_code', 'N/A')}")
print(f"Error: {result.get('error', 'None')}")
print(f"\nRaw output (first 1000 chars):")
print(result.get('raw_output', '')[:1000])
print("\n" + "=" * 60)
print(f"Findings: {result.get('findings', [])}")

