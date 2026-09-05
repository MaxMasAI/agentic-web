"""
test_pid_tracker.py - Test Suite for pid_tracker.py module.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.pid_tracker import register_pid, get_tracked_pids, kill_all_tracked_pids, _save_persisted_pids

class TestPIDTracker(unittest.TestCase):

    def setUp(self):
        _save_persisted_pids([])

    def tearDown(self):
        _save_persisted_pids([])

    def test_register_and_get_pids(self):
        """Verify that PIDs are registered into the queue without duplicates."""
        register_pid(12345)
        register_pid(67890)
        register_pid(12345)  # Duplicate should be ignored
        
        pids = get_tracked_pids()
        self.assertEqual(len(pids), 2)
        self.assertIn(12345, pids)
        self.assertIn(67890, pids)

    def test_kill_and_clear_queue(self):
        """Verify that kill_all_tracked_pids clears the queue completely."""
        register_pid(999999)  # Non-existent dummy PID
        self.assertEqual(len(get_tracked_pids()), 1)
        
        kill_all_tracked_pids()
        self.assertEqual(len(get_tracked_pids()), 0, "PID queue must be empty after cleanup.")

if __name__ == "__main__":
    unittest.main()
