"""
tests/test_token_manager.py - Test suite for Token Manager, Free Quotas & Chart Analytics.
"""

import sys
import os
import unittest
import tempfile
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.token_manager import TokenManager, MODEL_QUOTAS_CATALOG


class TestTokenManager(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_tokens.sqlite")
        self.mgr = TokenManager(db_path=self.db_path)

    def tearDown(self):
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_model_quotas_catalog(self):
        """Verify knowledge base of model free quotas."""
        self.assertIn("gemini-2.0-flash", MODEL_QUOTAS_CATALOG)
        gemini = MODEL_QUOTAS_CATALOG["gemini-2.0-flash"]
        self.assertEqual(gemini["daily_requests_limit"], 1500)
        self.assertEqual(gemini["rpm_limit"], 15)

        self.assertIn("deepseek-v3", MODEL_QUOTAS_CATALOG)
        self.assertIn("gpt-4o-mini", MODEL_QUOTAS_CATALOG)
        self.assertIn("groq-llama-3.3", MODEL_QUOTAS_CATALOG)

    def test_record_usage_and_lifetime_summary(self):
        """Verify recording token events and calculating lifetime metrics."""
        self.mgr.record_usage(
            provider="Google Gemini",
            model="gemini-2.0-flash",
            prompt_tokens=10000,
            completion_tokens=4000,
            task_id="task-1"
        )
        self.mgr.record_usage(
            provider="DeepSeek",
            model="deepseek-v3",
            prompt_tokens=5000,
            completion_tokens=2000,
            task_id="task-2"
        )

        summary = self.mgr.get_lifetime_summary()
        self.assertGreaterEqual(summary["total_tokens"], 21000)
        self.assertGreaterEqual(summary["total_prompt_tokens"], 15000)
        self.assertGreaterEqual(summary["total_completion_tokens"], 6000)
        self.assertGreaterEqual(summary["total_requests"], 2)

    def test_today_summary_and_reset_countdown(self):
        """Verify today's usage calculations and UTC reset countdown."""
        today = self.mgr.get_today_summary()
        self.assertIn("today_tokens", today)
        self.assertIn("usage_percent", today)
        self.assertIn("seconds_until_reset", today)
        self.assertGreater(today["seconds_until_reset"], 0)
        self.assertLessEqual(today["seconds_until_reset"], 86400)

    def test_daily_history_for_graphs(self):
        """Verify daily aggregated history structure for visual trend charts."""
        history = self.mgr.get_daily_history(days=7)
        self.assertIsInstance(history, list)
        self.assertGreater(len(history), 0)
        first = history[0]
        self.assertIn("date", first)
        self.assertIn("total_tokens", first)
        self.assertIn("label", first)

    def test_model_distribution_for_donut_chart(self):
        """Verify model percentage share breakdown."""
        dist = self.mgr.get_model_distribution()
        self.assertIsInstance(dist, list)
        self.assertGreater(len(dist), 0)
        for item in dist:
            self.assertIn("percent", item)
            self.assertIn("tokens", item)
            self.assertIn("color", item)


if __name__ == "__main__":
    unittest.main()
