"""
tests/test_internal_tools.py - Unit test for Universal Internal Tool Executor & Slash Router
"""

import unittest
from core.command_router import route_task_with_laya, parse_slash_task_command
from core.internal_tool_executor import InternalToolExecutor


class TestInternalToolsAndRouter(unittest.TestCase):
    def setUp(self):
        self.executor = InternalToolExecutor.get_instance()

    def test_slash_navigations(self):
        res = parse_slash_task_command("/tokens")
        self.assertEqual(res["type"], "navigate")
        self.assertEqual(res["target_page"], "tokens")

        res = parse_slash_task_command("/canvas")
        self.assertEqual(res["type"], "navigate")
        self.assertEqual(res["target_page"], "canvas_dev")

        res = parse_slash_task_command("/vscode")
        self.assertEqual(res["type"], "navigate")
        self.assertEqual(res["target_page"], "vscode")

    def test_slash_tool_commands(self):
        res = parse_slash_task_command("/mcp filesystem")
        self.assertEqual(res["type"], "mcp_tool")
        self.assertEqual(res["tool_name"], "filesystem")

        res = parse_slash_task_command("/memory search api keys")
        self.assertEqual(res["type"], "memory_tool")
        self.assertEqual(res["action"], "search")

        res = parse_slash_task_command("/file read project.yml")
        self.assertEqual(res["type"], "file_tool")
        self.assertEqual(res["operation"], "read")

        res = parse_slash_task_command("/wiki quantum computing")
        self.assertEqual(res["type"], "wiki_tool")

        res = parse_slash_task_command("/search latest ai models")
        self.assertEqual(res["type"], "web_tool")

        res = parse_slash_task_command("/system - dir")
        self.assertEqual(res["type"], "system_exec")

    def test_agent_slash_dispatch(self):
        res = parse_slash_task_command("/deepseek - refactor api endpoint")
        self.assertEqual(res["type"], "dispatch")
        self.assertEqual(res["agents"], "deepseek")

        res = parse_slash_task_command("/claude,chatgpt - security review")
        self.assertEqual(res["type"], "dispatch")
        self.assertEqual(res["agents"], "claude,chatgpt")

        res = parse_slash_task_command("/all - full architectural plan")
        self.assertEqual(res["type"], "dispatch")
        self.assertEqual(res["agents"], "all")

    def test_internal_tool_file_io(self):
        res = self.executor.execute_file_operation("read", "project.yml")
        self.assertTrue(res["success"])
        self.assertIn("name", res["output"])

    def test_internal_tool_os_exec(self):
        res = self.executor.execute_os_command("echo TOOL_OK")
        self.assertTrue(res["success"])
        self.assertIn("TOOL_OK", res["output"])

    def test_autonomous_tool_detection(self):
        auto_res = self.executor.detect_and_auto_execute_tools("search the web for deepmind")
        self.assertIsNotNone(auto_res)
        self.assertEqual(auto_res["tool"], "web_search")

        auto_file = self.executor.detect_and_auto_execute_tools("read file project.yml")
        self.assertIsNotNone(auto_file)
        self.assertEqual(auto_file["tool"], "file_io")

    def test_split_multi_tasks(self):
        from core.command_router import split_multi_task_prompt
        # Chained slash commands
        res1 = split_multi_task_prompt("/deepseek - build frontend ; /claude - audit security")
        self.assertEqual(len(res1), 2)
        self.assertEqual(res1[0]["agents"], "deepseek")
        self.assertEqual(res1[1]["agents"], "claude")

        # Numbered list
        res2 = split_multi_task_prompt("1. Scrape stock data\n2. Summarize findings with ChatGPT\n3. Generate visual chart")
        self.assertEqual(len(res2), 3)
        self.assertEqual(res2[0]["subtask_index"], 1)
        self.assertEqual(res2[1]["subtask_index"], 2)
        self.assertEqual(res2[2]["subtask_index"], 3)

        # Single task fallback
        res3 = split_multi_task_prompt("Single straightforward coding prompt")
        self.assertEqual(len(res3), 1)


if __name__ == "__main__":
    unittest.main()
