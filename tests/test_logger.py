"""
test_logger.py - Test Suite for logger.py module.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.logger import strip_ansi, setup_logging, close_logging

class TestLogger(unittest.TestCase):

    def test_strip_ansi(self):
        """Verify that ANSI color escape sequences are stripped completely from text."""
        colored_text = "\033[96m[Leader]\033[0m \033[92mSuccess!\033[0m"
        clean = strip_ansi(colored_text)
        self.assertEqual(clean, "[Leader] Success!")

    def test_setup_and_close_logging(self):
        """Verify that setup_logging creates the log file in logs/ and close_logging restores stdout."""
        log_file = setup_logging("test_unit_task")
        self.assertTrue(os.path.exists(log_file))
        self.assertTrue(log_file.startswith("logs"))
        
        # Test writing directly to sys.stdout (which is wrapped by logger)
        sys.stdout.write("Unit test log entry 12345\n")
        
        close_logging()
        
        # Read back log file content
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("MULTI-AGENT PIPELINE LOG", content)
        self.assertIn("Unit test log entry 12345", content)
        
        # Clean up test log file
        try:
            os.remove(log_file)
        except Exception:
            pass

if __name__ == "__main__":
    unittest.main()
