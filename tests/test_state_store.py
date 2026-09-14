"""
tests/test_state_store.py - Test suite for SQLite WAL State Store.
"""

import sys
import os
import unittest
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from system.state_store import StateStore


class TestStateStore(unittest.TestCase):

    def setUp(self):
        StateStore.reset_instance()
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_state.sqlite")
        self.store = StateStore(db_path=self.db_path)

    def tearDown(self):
        self.store.close()
        StateStore.reset_instance()
        try:
            self.tmp_dir.cleanup()
        except Exception:
            pass

    def test_key_value_storage(self):
        """Test persistent key-value store."""
        self.store.set_kv("theme", "dark")
        self.store.set_kv("max_retries", 5)

        self.assertEqual(self.store.get_kv("theme"), "dark")
        self.assertEqual(self.store.get_kv("max_retries"), 5)
        self.assertIsNone(self.store.get_kv("non_existent"))

    def test_pid_registry(self):
        """Test active process registration and pruning."""
        self.store.register_pid(pid=99999, process_name="chrome.exe", port=9222)
        active = self.store.get_all_active_pids()
        self.assertIn(99999, active)

        self.store.mark_pid_terminated(pid=99999)
        active_after = self.store.get_all_active_pids()
        self.assertNotIn(99999, active_after)

    def test_task_state_lifecycle(self):
        """Test transactional task state tracking."""
        self.store.set_task_state(
            task_id="task-12345",
            title="Analyze web performance",
            status="PENDING",
            leader_plan="Step 1: Check CDP. Step 2: Audit."
        )

        task = self.store.get_task_state("task-12345")
        self.assertIsNotNone(task)
        self.assertEqual(task["status"], "PENDING")
        self.assertIn("CDP", task["leader_plan"])

        # Update status
        self.store.set_task_state(
            task_id="task-12345",
            title="Analyze web performance",
            status="COMPLETED",
            result="Speed index 98"
        )
        task_done = self.store.get_task_state("task-12345")
        self.assertEqual(task_done["status"], "COMPLETED")
        self.assertEqual(task_done["result"], "Speed index 98")


if __name__ == "__main__":
    unittest.main()
