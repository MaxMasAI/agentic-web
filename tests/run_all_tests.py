"""
run_all_tests.py - Clean Test Runner for all project test suites.
"""

import unittest
import sys
import os
import io

# Initialize Virtual Terminal for Windows color rendering
os.system("")

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

def run_all():
    print(f"\n{CYAN}{'='*60}{RESET}")
    print(f"{CYAN}{BOLD}   RUNNING MULTI-AGENT SYSTEM TEST SUITE (12 TESTS)   {RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")

    # Discover all tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(__file__)
    suite = loader.discover(start_dir=start_dir, pattern="test_*.py")

    # Collect tests list
    test_list = []
    def extract_tests(s):
        for item in s:
            if isinstance(item, unittest.TestSuite):
                extract_tests(item)
            else:
                test_list.append(item)
    extract_tests(suite)

    passed = 0
    failed = 0
    errors = 0

    for idx, test in enumerate(test_list, 1):
        test_name = f"{test.__class__.__name__}.{test._testMethodName}"
        doc = test._testMethodDoc or ""
        doc = doc.strip().split("\n")[0] if doc else ""

        # Suppress inner stdout during test execution for clean reporting
        captured_out = io.StringIO()
        orig_stdout = sys.stdout
        sys.stdout = captured_out

        result = unittest.TestResult()
        test.run(result)

        sys.stdout = orig_stdout

        if result.wasSuccessful():
            passed += 1
            status = f"{GREEN}[OK]{RESET}"
            print(f" {status} {idx:02d}. {CYAN}{test_name:<40}{RESET} - {doc}")
        elif result.errors:
            errors += 1
            status = f"{RED}[ERROR]{RESET}"
            print(f" {status} {idx:02d}. {CYAN}{test_name:<40}{RESET} - {doc}")
            for _, err in result.errors:
                print(f"{RED}{err}{RESET}")
        else:
            failed += 1
            status = f"{RED}[FAIL]{RESET}"
            print(f" {status} {idx:02d}. {CYAN}{test_name:<40}{RESET} - {doc}")
            for _, fail in result.failures:
                print(f"{RED}{fail}{RESET}")

    print(f"\n{CYAN}{'='*60}{RESET}")
    if failed == 0 and errors == 0:
        print(f"{GREEN}{BOLD}  [PASS] ALL {passed}/12 TESTS RETURNED OK!{RESET}")
    else:
        print(f"{RED}{BOLD}  [FAIL] {passed} Passed, {failed} Failed, {errors} Errors{RESET}")
    print(f"{CYAN}{'='*60}{RESET}\n")

    return 0 if (failed == 0 and errors == 0) else 1

if __name__ == "__main__":
    sys.exit(run_all())
