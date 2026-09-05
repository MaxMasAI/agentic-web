"""
test_downloader.py - Test Suite for downloader.py module.
"""

import sys
import os
import shutil
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from browser.downloader import make_task_folder

class TestDownloader(unittest.TestCase):

    def setUp(self):
        self.test_dirs = []

    def tearDown(self):
        for d in self.test_dirs:
            if os.path.exists(d):
                try:
                    shutil.rmtree(d)
                except Exception:
                    pass

    def test_make_task_folder_creates_directory(self):
        """Verify that make_task_folder sanitizes the task string and creates the folder."""
        task_name = "Create a Brand New AI Logo 2026!"
        folder = make_task_folder(task_name)
        self.test_dirs.append(folder)
        
        self.assertTrue(os.path.exists(folder))
        self.assertTrue(folder.startswith("downloads"))
        # Check sanitization: no special chars like '!'
        self.assertNotIn("!", folder)
        self.assertIn("brand_new_ai_logo", folder)

    def test_empty_task_fallback(self):
        """Verify empty task names fall back safely."""
        folder = make_task_folder("???")
        self.test_dirs.append(folder)
        self.assertTrue(os.path.exists(folder))
        self.assertTrue(folder.endswith("task"))

if __name__ == "__main__":
    unittest.main()
