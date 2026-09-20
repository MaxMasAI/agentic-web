"""
tests/test_command_router.py - Test suite for slash command parsing and multi-agent routing.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.command_router import parse_slash_task_command, resolve_agent_id


class TestCommandRouter(unittest.TestCase):

    def test_single_agent_slash_syntax(self):
        """Verify single agent slash command format '/{name} - {task}'."""
        res = parse_slash_task_command("/deepseek - build a python web scraper")
        self.assertEqual(res["type"], "dispatch")
        self.assertEqual(res["agents"], "deepseek")
        self.assertEqual(res["task"], "build a python web scraper")

        res2 = parse_slash_task_command("/claude: in-depth security review")
        self.assertEqual(res2["type"], "dispatch")
        self.assertEqual(res2["agents"], "claude")
        self.assertEqual(res2["task"], "in-depth security review")

    def test_multi_agent_slash_syntax(self):
        """Verify multiple agents slash command format '/{agent1},{agent2} - {task}'."""
        res = parse_slash_task_command("/deepseek,chatgpt - draft and code documentation")
        self.assertEqual(res["type"], "dispatch")
        self.assertEqual(res["agents"], "deepseek,chatgpt")
        self.assertEqual(res["task"], "draft and code documentation")

    def test_all_agents_slash_syntax(self):
        """Verify '/all - {task}' syntax."""
        res = parse_slash_task_command("/all - execute collaborative multi-model sprint")
        self.assertEqual(res["type"], "dispatch")
        self.assertEqual(res["agents"], "all")
        self.assertEqual(res["task"], "execute collaborative multi-model sprint")

    def test_system_exec_syntax(self):
        """Verify '/system - {cmd}' OS execution syntax."""
        res = parse_slash_task_command("/system - open notepad")
        self.assertEqual(res["type"], "system_exec")
        self.assertEqual(res["task"], "open notepad")

    def test_utility_slash_commands(self):
        """Verify utility commands: /reset, /help, /inspect."""
        res_reset = parse_slash_task_command("/reset")
        self.assertEqual(res_reset["type"], "reset")

        res_help = parse_slash_task_command("/help")
        self.assertEqual(res_help["type"], "help")

        res_insp = parse_slash_task_command("/inspect deepseek")
        self.assertEqual(res_insp["type"], "inspect")
        self.assertEqual(res_insp["target_agent"], "deepseek")

    def test_regular_text_fallback(self):
        """Verify regular text without slash routes to auto."""
        res = parse_slash_task_command("Create a landing page for AI startup")
        self.assertEqual(res["type"], "dispatch")
        self.assertEqual(res["agents"], "auto")
        self.assertEqual(res["task"], "Create a landing page for AI startup")


if __name__ == "__main__":
    unittest.main()
