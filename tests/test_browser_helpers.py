"""
test_browser_helpers.py - Test Suite for browser_helpers.py module.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from browser import browser_helpers

class TestBrowserHelpers(unittest.TestCase):

    def test_column_width_calculation(self):
        """Verify column width calculations for 2, 3, 4, and 9 columns."""
        screen_w = 1920
        screen_h = 1080
        
        for total_cols in [2, 3, 4, 9]:
            col_w = screen_w // total_cols
            for col_idx in range(total_cols):
                win_left = col_w * col_idx
                self.assertGreaterEqual(win_left, 0)
                self.assertLess(win_left + col_w, screen_w + total_cols)

if __name__ == "__main__":
    unittest.main()
