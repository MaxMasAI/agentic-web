"""
tests/test_issue_reporter.py - Test suite for Autonomous GitHub Issue & Crash Reporter.
"""

import sys
import os
import unittest
import tempfile
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from system.issue_reporter import (
    sanitize_text,
    compute_traceback_fingerprint,
    CrashReport,
    GitHubIssueReporter,
    get_issue_reporter
)


class TestIssueReporter(unittest.TestCase):

    def test_sanitize_text_redacts_tokens(self):
        """Verify sensitive credentials are removed from traces."""
        raw_error = "Error connecting with ghp_1234567890abcdef1234567890 and AIzaSyDdummy1234567890123456789012345678"
        sanitized = sanitize_text(raw_error)
        self.assertNotIn("ghp_1234567890abcdef1234567890", sanitized)
        self.assertNotIn("AIzaSyDdummy1234567890123456789012345678", sanitized)
        self.assertIn("[GH_PAT_REDACTED]", sanitized)
        self.assertIn("[GEMINI_KEY_REDACTED]", sanitized)

    def test_traceback_fingerprint_stability(self):
        """Verify fingerprints match across machines regardless of specific line numbers."""
        tb1 = 'Traceback (most recent call last):\n  File "app.py", line 123, in main\n    run()\nValueError: Invalid agent'
        tb2 = 'Traceback (most recent call last):\n  File "app.py", line 456, in main\n    run()\nValueError: Invalid agent'

        fp1 = compute_traceback_fingerprint("ValueError", tb1)
        fp2 = compute_traceback_fingerprint("ValueError", tb2)
        self.assertEqual(fp1, fp2)
        self.assertTrue(len(fp1) >= 8)

    def test_crash_report_markdown_and_local_dump(self):
        """Verify crash report generates markdown issue and persists JSON dump."""
        report = CrashReport(
            exc_type="ZeroDivisionError",
            exc_value="division by zero in worker loop",
            tb_str="Traceback:\n  File 'worker.py', line 10\n    1/0\nZeroDivisionError: division by zero",
            extra_context={"agent": "gemini", "task_id": "test-task-1"}
        )

        title, body = report.to_markdown_issue("MaxMasAI", "agentic-web")
        self.assertIn("[Auto-Crash] ZeroDivisionError:", title)
        self.assertIn("### 🚨 Autonomous Application Crash Report", body)
        self.assertIn("https://github.com/MaxMasAI/agentic-web", body)
        self.assertIn(f"<!-- FP:{report.fingerprint} -->", body)

        dump_path = report.save_local_dump()
        self.assertTrue(os.path.exists(dump_path))
        with open(dump_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["exc_type"], "ZeroDivisionError")
            self.assertEqual(data["fingerprint"], report.fingerprint)

    def test_github_issue_reporter_offline_handling(self):
        """Verify reporter falls back gracefully and preserves report when no token exists."""
        reporter = GitHubIssueReporter(repo_owner="MaxMasAI", repo_name="agentic-web", token="")
        res = reporter.report_crash(
            exc_type="RuntimeError",
            exc_value="Simulated pipeline failure",
            tb_str="Traceback:\n  File 'test.py', line 1\nRuntimeError: Simulated pipeline failure",
            async_dispatch=False
        )
        self.assertIn("local_dump", res)
        self.assertTrue(os.path.exists(res["local_dump"]))


if __name__ == "__main__":
    unittest.main()
