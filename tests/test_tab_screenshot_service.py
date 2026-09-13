"""
tests/test_tab_screenshot_service.py - Test suite for multi-tab screenshot engine
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.tab_screenshot_service import sanitize_tab_filename, DEFAULT_IMAGES_DIR

class TestTabScreenshotService(unittest.TestCase):

    def test_sanitize_tab_filename(self):
        self.assertEqual(
            sanitize_tab_filename("● Google Gemini • Agent | Studio"),
            "Google_Gemini_Agent_Studio"
        )
        self.assertEqual(
            sanitize_tab_filename("● DeepSeek • Agent | Chat"),
            "DeepSeek_Agent_Chat"
        )
        self.assertEqual(
            sanitize_tab_filename("ChatGPT - 2026 Tech Discussion?"),
            "ChatGPT_2026_Tech_Discussion"
        )
        self.assertEqual(
            sanitize_tab_filename("YouTube: Lofi Beats (Live)"),
            "YouTube_Lofi_Beats_Live"
        )
        self.assertTrue(len(sanitize_tab_filename("a" * 100)) <= 60)

    def test_images_directory_path(self):
        self.assertTrue(os.path.isabs(DEFAULT_IMAGES_DIR))
        self.assertTrue(DEFAULT_IMAGES_DIR.endswith("images"))

if __name__ == "__main__":
    unittest.main()
