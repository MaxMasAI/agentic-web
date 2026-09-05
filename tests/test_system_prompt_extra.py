"""
tests/test_system_prompt_extra.py - Unit tests for System Prompt Extra (append) Plugin
"""

import unittest
import tempfile
import os
import shutil
from services.system_prompt_extra import SystemPromptExtraService


class TestSystemPromptExtraService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "prompt_extras.json")
        self.service = SystemPromptExtraService(config_path=self.config_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_default_extras_loaded(self):
        items = self.service.list_extras()
        self.assertTrue(len(items) >= 2)
        ids = [i["id"] for i in items]
        self.assertIn("code_style_guidelines", ids)

    def test_apply_to_prompt(self):
        base_prompt = "You are a specialized coding agent."
        enhanced = self.service.apply_to_prompt(base_prompt)
        self.assertIn(base_prompt, enhanced)
        self.assertIn("### Extra System Instructions & Directives:", enhanced)
        self.assertIn("Production Code Quality", enhanced)

    def test_add_and_toggle_extra(self):
        self.service.add_extra(
            extra_id="custom_directive",
            name="Always Return JSON",
            content="Output must be strictly valid JSON.",
            enabled=True
        )
        enhanced = self.service.apply_to_prompt("Base prompt")
        self.assertIn("Always Return JSON", enhanced)

        # Disable it
        self.service.toggle_extra("custom_directive", False)
        enhanced_disabled = self.service.apply_to_prompt("Base prompt")
        self.assertNotIn("Always Return JSON", enhanced_disabled)


if __name__ == "__main__":
    unittest.main()
