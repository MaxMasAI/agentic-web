"""
tests/test_system_os_service.py - Unit tests for System (OS) Plugin
"""

import unittest
import tempfile
import os
import shutil
from services.system_os_service import SystemOSService


class TestSystemOSService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "sys_os_config.json")
        self.service = SystemOSService(config_path=self.config_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_sys_exec_basic_command(self):
        # Python expression evaluation
        res = self.service.sys_exec('python -c "print(40 + 2)"')
        self.assertTrue(res["success"])
        self.assertEqual(res["returncode"], 0)
        self.assertIn("42", res["stdout"])
        self.assertTrue(res["auto_cwd"] if "auto_cwd" in res else bool(res.get("cwd")))

    def test_sys_exec_disabled_toggle(self):
        self.service.set_options(sys_exec_enabled=False)
        res = self.service.sys_exec('echo "Should not run"')
        self.assertFalse(res["success"])
        self.assertIn("disabled", res["error"])

    def test_auto_cwd_option(self):
        self.service.set_options(auto_cwd=True)
        res = self.service.sys_exec('python -c "import os; print(os.getcwd())"')
        self.assertTrue(res["success"])
        self.assertIn(os.getcwd(), res["stdout"].strip())


if __name__ == "__main__":
    unittest.main()
