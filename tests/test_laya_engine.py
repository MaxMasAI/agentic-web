"""
tests/test_laya_engine.py - Unit tests for LAYA System 1 Decision Engine
Verifies typed decision primitives (choice, score, noul), state normalization,
calibrated probability gating, sub-40ms latency, and plugin tool security boundaries.
"""

import unittest
import time
from core.laya_engine import (
    LayaDecisionEngine,
    LayaQuestionType,
    LayaContract,
    LayaQuestion,
    DEFAULT_INGRESS_CONTRACT,
    DEFAULT_PLUGIN_CONTRACT,
)
from core.command_router import parse_slash_task_command, route_task_with_laya
from core.harness.plugin_base import BasePlugin, PluginManager


class TestLayaDecisionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = LayaDecisionEngine.get_instance(confidence_threshold=0.85)

    def test_state_normalization(self):
        raw = "/deepseek - refactor user authentication in auth.py"
        state = self.engine.normalize_state(raw, {"workspace": "agentic-web"})

        self.assertEqual(state["command_token"], "deepseek")
        self.assertTrue(state["has_slash_prefix"])
        self.assertIn("py", state["detected_file_extensions"])
        self.assertFalse(state["contains_shell_keywords"])
        self.assertFalse(state["contains_web_urls"])
        self.assertEqual(state["context_attributes"]["workspace"], "agentic-web")

    def test_ingress_decision_primitives(self):
        # 1. Choice & Fast-Path for DeepSeek Coder
        state = self.engine.normalize_state("/deepseek - implement binary search tree in python")
        res = self.engine.evaluate_contract(state, DEFAULT_INGRESS_CONTRACT)

        self.assertEqual(res.decisions["target_specialist"], "deepseek_coder")
        self.assertGreaterEqual(res.primary_confidence, 0.85)
        self.assertTrue(res.fast_path_eligible)
        self.assertFalse(res.requires_system2_fallback)
        self.assertLess(res.latency_ms, 40.0)

        # 2. Choice for Claude Auditor
        state_claude = self.engine.normalize_state("/claude - audit sql injection vulnerability")
        res_claude = self.engine.evaluate_contract(state_claude, DEFAULT_INGRESS_CONTRACT)
        self.assertEqual(res_claude.decisions["target_specialist"], "claude_auditor")
        self.assertGreaterEqual(res_claude.primary_confidence, 0.85)

        # 3. Security gate check for dangerous shell command
        state_sec = self.engine.normalize_state("/system - rm -rf /tmp/data")
        res_sec = self.engine.evaluate_contract(state_sec, DEFAULT_INGRESS_CONTRACT)
        self.assertTrue(res_sec.is_security_sensitive)
        self.assertEqual(res_sec.urgency_tier, "critical_sandbox_required")

    def test_system2_fallback_on_ambiguous_prompt(self):
        # Short/ambiguous prompt without clear keywords or slash command
        state_ambiguous = self.engine.normalize_state("hi")
        res_ambiguous = self.engine.evaluate_contract(state_ambiguous, DEFAULT_INGRESS_CONTRACT)

        self.assertTrue(res_ambiguous.requires_system2_fallback)
        self.assertFalse(res_ambiguous.fast_path_eligible)

    def test_plugin_decision_contract(self):
        state_plugin = self.engine.normalize_state(
            raw_payload="plugin_tool_call:os_exec_command",
            context_attributes={"tool_name": "os_exec_command", "arguments": {"cmd": "dir"}}
        )
        res_plugin = self.engine.evaluate_contract(state_plugin, DEFAULT_PLUGIN_CONTRACT)

        self.assertEqual(res_plugin.decisions["tool_category"], "os_process")
        self.assertEqual(res_plugin.decisions["privilege_level"], "elevated_system")
        self.assertTrue(res_plugin.decisions["requires_sandbox_isolation"])
        self.assertTrue(res_plugin.is_security_sensitive)

    def test_command_router_laya_integration(self):
        info = route_task_with_laya("/deepseek - build rest api")
        self.assertIn("laya_decision", info)
        self.assertTrue(info.get("laya_fast_path"))
        self.assertEqual(info.get("laya_recommended_specialist"), "deepseek_coder")
        self.assertLess(info.get("laya_latency_ms"), 40.0)

    def test_sub_40ms_latency_guarantee(self):
        latencies = []
        for i in range(50):
            t0 = time.perf_counter()
            res = self.engine.route_with_laya(f"Task query iteration {i}: optimize database query")
            latencies.append((time.perf_counter() - t0) * 1000)
            self.assertLess(res.latency_ms, 40.0)

        avg_latency = sum(latencies) / len(latencies)
        self.assertLess(avg_latency, 5.0)  # Sub-5ms average on modern hardware


class MockTestPlugin(BasePlugin):
    id = "mock_test_plugin"
    name = "Mock Test Plugin"
    description = "Plugin for unit testing LAYA tool gatekeeping."

    def attach_tools(self):
        return [{
            "name": "mock_fs_read",
            "description": "Reads local test file",
            "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}
        }]

    def execute_tool(self, tool_name: str, arguments: dict):
        return {"success": True, "data": "test_content"}


class TestPluginLayaGatekeeping(unittest.TestCase):

    def test_plugin_tool_call_with_laya_telemetry(self):
        manager = PluginManager()
        plugin = MockTestPlugin()
        manager.register_plugin(plugin)

        res = manager.call_plugin_tool("mock_fs_read", {"path": "test.txt"}, enforce_laya_gating=True)
        self.assertTrue(res.get("success"))
        self.assertIn("laya_telemetry", res)
        telemetry = res["laya_telemetry"]
        self.assertLess(telemetry["latency_ms"], 40.0)
        self.assertIn("privilege_level", telemetry)


if __name__ == "__main__":
    unittest.main()
