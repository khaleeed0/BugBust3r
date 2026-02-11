"""Quick test: Ghauri Docker tool runs and returns structured output (status, raw_output, vulnerable)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.docker.tools import GhauriTool

def main():
    print("Testing GhauriTool (security-tools:ghauri)...")
    tool = GhauriTool()
    # Localhost URL; tool will rewrite to host.docker.internal for Docker
    url = "http://localhost:8000/api/v1/scans"
    print(f"Target URL: {url} (is_localhost=True -> rewritten to host.docker.internal in container)")
    result = tool.run(target_url=url, is_localhost=True)
    print("\n--- Result keys ---")
    print(list(result.keys()))
    print("\n--- status ---")
    print(result.get("status"))
    print("\n--- vulnerable ---")
    print(result.get("vulnerable"))
    print("\n--- raw_output (first 1200 chars) ---")
    raw = result.get("raw_output") or ""
    print(raw[:1200])
    print("\n--- error (if any) ---")
    print(result.get("error"))
    assert "status" in result, "Missing status"
    assert "raw_output" in result or "error" in result, "Must have raw_output or error"
    print("\nOK: GhauriTool returns valid output.")
    return 0

if __name__ == "__main__":
    exit(main())
