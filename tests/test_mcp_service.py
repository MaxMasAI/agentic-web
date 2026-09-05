"""
test_mcp_service.py - Test Suite for MCP Service Engine (Agent Skills + CitroLabs Ego-Lite).
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.mcp_service import list_mcp_servers, list_mcp_tools, call_mcp_tool, load_mcp_config

class TestMCPService(unittest.TestCase):

    def test_load_mcp_config_and_servers(self):
        """Verify MCP server configurations load correctly."""
        servers = list_mcp_servers()
        self.assertGreaterEqual(len(servers), 2)
        server_ids = [s["id"] for s in servers]
        self.assertIn("agent_skills", server_ids)
        self.assertIn("ego_lite_browser", server_ids)

    def test_list_ego_lite_tools(self):
        """Verify dynamic MCP tools catalog exposes Ego-Lite browser tools."""
        tools = list_mcp_tools()
        tool_ids = [t["tool_id"] for t in tools]
        self.assertIn("mcp__ego_lite__create_space", tool_ids)
        self.assertIn("mcp__ego_lite__navigate_and_extract", tool_ids)
        self.assertIn("mcp__ego_lite__capture_snapshot", tool_ids)
        self.assertIn("mcp__ego_lite__execute_script", tool_ids)

    def test_call_ego_lite_create_space(self):
        """Verify executing mcp__ego_lite__create_space returns active isolated space session."""
        res = call_mcp_tool("mcp__ego_lite__create_space", {"space_name": "marketing-research"})
        self.assertEqual(res["status"], "success")
        self.assertIn("ego-space", res["result"]["space_id"])
        self.assertEqual(res["result"]["cdp_port"], 9222)

    def test_call_ego_lite_navigate(self):
        """Verify navigating to URL within Ego-Lite space."""
        res = call_mcp_tool("mcp__ego_lite__navigate_and_extract", {"url": "https://example.com"})
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"]["navigation_status"], "200_OK")

if __name__ == "__main__":
    unittest.main()
