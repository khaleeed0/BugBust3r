#!/usr/bin/env python3
"""Run multiple AddressSanitizer tests and verify buffer overflow detection."""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.docker.tools import AddressSanitizerTool

def run_test(name, source_path=None):
    """Run ASan and return (passed, details)."""
    asan = AddressSanitizerTool()
    result = asan.run(source_path=source_path)
    status = result.get('status')
    error_count = result.get('error_count', 0)
    raw = result.get('raw_output', '')
    has_asan_error = 'ERROR: AddressSanitizer' in raw
    
    # Pass if we got completed_with_issues with ASan errors, or success with no errors
    if source_path:
        passed = (status == 'completed_with_issues' and has_asan_error) or (status == 'success' and not has_asan_error)
    else:
        # Demo should always detect overflow
        passed = status == 'completed_with_issues' and has_asan_error and error_count > 0
    
    return passed, {
        'status': status,
        'error_count': error_count,
        'has_asan_error': has_asan_error,
        'snippet': raw[:300] if raw else '(no output)'
    }

def main():
    base = os.path.dirname(os.path.abspath(__file__))
    test_dir = os.path.join(base, 'test_vulnerable_code')
    
    results = []
    
    # Test 1: Demo mode (built-in vulnerable C) - run 2 times
    print("=" * 60)
    print("TEST 1: Demo mode (no source path) - 2 runs")
    print("=" * 60)
    for i in range(2):
        passed, d = run_test("demo", source_path=None)
        results.append(("Demo run " + str(i+1), passed))
        print(f"  Run {i+1}: {'PASS' if passed else 'FAIL'} - status={d['status']}, errors={d['error_count']}, ASan detected={d['has_asan_error']}")
    
    # Test 2: test_vulnerable_code/test.c (C with strcpy overflow)
    print("\n" + "=" * 60)
    print("TEST 2: test.c (C buffer overflow) - 2 runs")
    print("=" * 60)
    for i in range(2):
        passed, d = run_test("test.c", source_path=test_dir)
        results.append((f"test.c run {i+1}", passed))
        print(f"  Run {i+1}: {'PASS' if passed else 'FAIL'} - status={d['status']}, errors={d['error_count']}, ASan detected={d['has_asan_error']}")
    
    # Test 3: C++ stack overflow (cpp_stack/overflow.cpp)
    cpp_stack_dir = os.path.join(test_dir, 'cpp_stack')
    print("\n" + "=" * 60)
    print("TEST 3: C++ stack buffer overflow (overflow.cpp) - 2 runs")
    print("=" * 60)
    for i in range(2):
        passed, d = run_test("cpp_stack", source_path=cpp_stack_dir)
        results.append((f"cpp_stack run {i+1}", passed))
        print(f"  Run {i+1}: {'PASS' if passed else 'FAIL'} - status={d['status']}, errors={d['error_count']}, ASan detected={d['has_asan_error']}")
    
    # Test 4: C++ heap overflow (cpp_heap/heap.cpp)
    cpp_heap_dir = os.path.join(test_dir, 'cpp_heap')
    print("\n" + "=" * 60)
    print("TEST 4: C++ heap buffer overflow (heap.cpp) - 2 runs")
    print("=" * 60)
    for i in range(2):
        passed, d = run_test("cpp_heap", source_path=cpp_heap_dir)
        results.append((f"cpp_heap run {i+1}", passed))
        print(f"  Run {i+1}: {'PASS' if passed else 'FAIL'} - status={d['status']}, errors={d['error_count']}, ASan detected={d['has_asan_error']}")
    
    # Test 5: Run demo again to ensure consistency
    print("\n" + "=" * 60)
    print("TEST 5: Demo mode consistency - 1 run")
    print("=" * 60)
    passed, d = run_test("demo_again", source_path=None)
    results.append(("Demo again", passed))
    print(f"  Run 1: {'PASS' if passed else 'FAIL'} - status={d['status']}, errors={d['error_count']}")
    
    # Summary
    print("\n" + "=" * 60)
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    print(f"SUMMARY: {passed_count}/{total} tests PASSED")
    print("=" * 60)
    
    if passed_count < total:
        print("Failed tests:")
        for name, p in results:
            if not p:
                print(f"  - {name}")
        sys.exit(1)
    
    print("All AddressSanitizer tests passed.")
    sys.exit(0)

if __name__ == '__main__':
    main()
