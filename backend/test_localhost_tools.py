#!/usr/bin/env python3
"""
Verify AddressSanitizer and Ghauri work and produce output.
Run from backend dir or: docker exec security_scanner_backend python test_localhost_tools.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_addresssanitizer():
    """Run AddressSanitizer (demo mode) and assert it returns output."""
    from app.docker.tools import AddressSanitizerTool

    print("=" * 60)
    print("TEST 1: AddressSanitizer (demo mode)")
    print("=" * 60)
    tool = AddressSanitizerTool()
    result = tool.run(source_path=None)

    assert "status" in result, "AddressSanitizer must return 'status'"
    assert "raw_output" in result, "AddressSanitizer must return 'raw_output'"
    assert result["status"] in ("success", "completed_with_issues", "failed"), f"Bad status: {result['status']}"

    raw = result.get("raw_output") or ""
    assert len(raw) > 0, "AddressSanitizer must produce non-empty output (raw_output)"
    assert result.get("tool") == "addresssanitizer", "Wrong tool name"
    # Demo mode intentionally triggers overflow -> exit_code 1 is expected; we still get full ASan report in raw_output
    if result.get("status") == "completed_with_issues" and result.get("error_count", 0) > 0:
        print("  (demo correctly detected stack-buffer-overflow)")

    print(f"  status: {result['status']}")
    print(f"  exit_code: {result.get('exit_code')}")
    print(f"  error_count: {result.get('error_count', 0)}")
    print(f"  raw_output length: {len(raw)} chars")
    print(f"  output preview: {raw[:300].strip()}...")
    if result.get("error"):
        print(f"  error: {result['error'][:200]}")
    print("  OK: AddressSanitizer produced output.\n")
    return True


def test_ghauri():
    """Run Ghauri against a URL and assert it returns output.
    Use a URL that matches SQL injection testing pattern (query param or path).
    Reference: GET /api/products/<string> e.g. /api/products/men for path-based SQLi.
    """
    from app.docker.tools import GhauriTool

    print("=" * 60)
    print("TEST 2: Ghauri (localhost URL - SQL injection)")
    print("=" * 60)
    tool = GhauriTool()
    # URL with query param for SQLi testing; matches reference pattern
    url = "http://localhost:8000/api/products/men"  # or http://localhost:8000/item?id=1
    result = tool.run(target_url=url, is_localhost=True)

    assert "status" in result, "Ghauri must return 'status'"
    assert "raw_output" in result or "error" in result, "Ghauri must return raw_output or error"
    assert result["status"] in ("success", "completed_with_issues", "failed"), f"Bad status: {result['status']}"

    raw = result.get("raw_output") or ""
    assert len(raw) > 0, "Ghauri must produce non-empty output (raw_output)"
    assert result.get("tool") == "ghauri", "Wrong tool name"

    print(f"  status: {result['status']}")
    print(f"  vulnerable: {result.get('vulnerable')}")
    print(f"  raw_output length: {len(raw)} chars")
    print(f"  output preview: {raw[:300].strip()}...")
    if result.get("error"):
        print(f"  error: {result['error'][:200]}")
    print("  OK: Ghauri produced output.\n")
    return True


def test_addresssanitizer_with_source():
    """Run AddressSanitizer on test_vulnerable_code/cpp_stack (buffer overflow)."""
    from app.docker.tools import AddressSanitizerTool

    # Resolve path to test_vulnerable_code/cpp_stack
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(backend_dir)
    cpp_stack = os.path.join(repo_root, "test_vulnerable_code", "cpp_stack")
    if not os.path.isdir(cpp_stack):
        print("TEST 3: AddressSanitizer (source path) - SKIP (test_vulnerable_code/cpp_stack not found)\n")
        return True

    print("=" * 60)
    print("TEST 3: AddressSanitizer (source path: cpp_stack)")
    print("=" * 60)
    tool = AddressSanitizerTool()
    result = tool.run(source_path=cpp_stack)

    raw = result.get("raw_output") or ""
    assert len(raw) > 0, "AddressSanitizer must produce non-empty output"
    assert result.get("tool") == "addresssanitizer"
    if result.get("status") == "completed_with_issues" and result.get("error_count", 0) > 0:
        print("  (detected stack-buffer-overflow in overflow.cpp)")
    print(f"  status: {result['status']}, error_count: {result.get('error_count', 0)}, output: {len(raw)} chars")
    print("  OK: AddressSanitizer with source path produced output.\n")
    return True


def main():
    errors = []
    try:
        test_addresssanitizer()
    except Exception as e:
        errors.append(f"AddressSanitizer: {e}")
        print(f"  FAIL: {e}\n")

    try:
        test_ghauri()
    except Exception as e:
        errors.append(f"Ghauri: {e}")
        print(f"  FAIL: {e}\n")

    try:
        test_addresssanitizer_with_source()
    except Exception as e:
        errors.append(f"AddressSanitizer (source): {e}")
        print(f"  FAIL: {e}\n")

    if errors:
        print("=" * 60)
        print("SUMMARY: FAILED")
        for e in errors:
            print(f"  - {e}")
        return 1
    print("=" * 60)
    print("SUMMARY: AddressSanitizer and Ghauri work and produce output.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
