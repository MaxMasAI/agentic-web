"""
tests/test_system_app_launcher.py - Unit test suite for native system app launcher
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.system_app_launcher import is_system_app_task, clean_app_request, KNOWN_SYSTEM_APPS

class TestSystemAppLauncher(unittest.TestCase):

    def test_clean_app_request(self):
        self.assertEqual(clean_app_request("open taskmanger"), "taskmanger")
        self.assertEqual(clean_app_request("open task manager"), "task manager")
        self.assertEqual(clean_app_request("launch notepad app"), "notepad")
        self.assertEqual(clean_app_request("start calculator"), "calculator")
        self.assertEqual(clean_app_request("please open vscode on my pc"), "vscode")

    def test_is_system_app_task_positive(self):
        self.assertTrue(is_system_app_task("open taskmanger"))
        self.assertTrue(is_system_app_task("open task manager"))
        self.assertTrue(is_system_app_task("open notepad"))
        self.assertTrue(is_system_app_task("open calculator"))
        self.assertTrue(is_system_app_task("open vscode"))
        self.assertTrue(is_system_app_task("open settings"))
        self.assertTrue(is_system_app_task("open control panel"))

    def test_is_system_app_task_negative(self):
        self.assertFalse(is_system_app_task("write a script in python to calculate fibonacci"))
        self.assertFalse(is_system_app_task("open https://github.com/torvalds/linux"))
        self.assertFalse(is_system_app_task("search on google for latest AI news"))
        self.assertFalse(is_system_app_task("create a react website with dark mode"))

if __name__ == "__main__":
    unittest.main()
