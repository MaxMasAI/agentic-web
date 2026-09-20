"""
tests/test_system_package.py - Test suite for system/ package modules.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from system.system_cursor import SYSTEM_CURSOR_COLOR, SYSTEM_CURSOR_JS
from system.system_app_launcher import is_system_app_task, clean_app_request
from system.system_os_service import SystemOSService
from system.mouse_keyboard_service import MouseKeyboardService
from system.pid_tracker import find_pid_on_port
from system.system_prompts import SystemPromptsCatalog, SystemPromptExtraService


class TestSystemPackage(unittest.TestCase):

    def test_system_cursor_constants(self):
        """Verify System Cursor styling parameters and red System cursor template."""
        self.assertEqual(SYSTEM_CURSOR_COLOR, "#7c3aed")
        self.assertIn("system-cursor-wrapper", SYSTEM_CURSOR_JS)
        from system.system_cursor import get_agent_cursor_template
        sys_tmpl = get_agent_cursor_template("system")
        self.assertEqual(sys_tmpl["id"], "system")
        self.assertEqual(sys_tmpl["name"], "System")
        self.assertEqual(sys_tmpl["color"], "#ef4444")
        self.assertIn("#ef4444", sys_tmpl["gradient"])

    def test_system_app_launcher_detection(self):
        """Verify native system application task classification."""
        self.assertTrue(is_system_app_task("open notepad"))
        self.assertTrue(is_system_app_task("launch task manager"))
        self.assertTrue(is_system_app_task("start calculator"))
        self.assertEqual(clean_app_request("open the notepad app"), "notepad")

    def test_system_os_service(self):
        """Verify SystemOSService initialization and execution."""
        svc = SystemOSService()
        self.assertTrue(svc.sys_exec_enabled)
        res = svc.sys_exec("echo Antigravity_System_Test")
        self.assertTrue(res["success"])
        self.assertIn("Antigravity_System_Test", res["stdout"])

    def test_mouse_keyboard_service(self):
        """Verify MouseKeyboardService resolution and mouse coordinates."""
        svc = MouseKeyboardService()
        pos = svc.get_mouse_position()
        self.assertTrue(pos["success"])
        self.assertIn("x", pos)
        self.assertIn("y", pos)

    def test_system_fancyzones(self):
        """Verify FancyZones engine in system package and fix_system_layout."""
        from system.fancyzones_manager import (
            calculate_3_columns_layout,
            calculate_zone_bounds,
            fix_system_layout
        )
        zones = calculate_3_columns_layout(1920, 1080, spacing=16)
        self.assertEqual(len(zones), 3)
        self.assertEqual(zones[0].x, 16)
        self.assertEqual(zones[1].x, 16 + zones[0].width + 16)

        fix_res = fix_system_layout(["Notepad", "Calculator"], layout_name="columns_2")
        self.assertTrue(fix_res["success"])
        self.assertEqual(len(fix_res["windows"]), 2)


if __name__ == "__main__":
    unittest.main()
