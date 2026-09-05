"""
tests/test_mcp_client.py - Unit tests for Model Context Protocol (MCP) Client
"""

import unittest
import tempfile
import os
import shutil
from services.mcp_client import MCPClient, MCPTransportType


class TestMCPClient(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.test_dir, "mcp_config.json")
        self.client = MCPClient(config_path=self.config_path)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_add_and_list_servers(self):
        res = self.client.add_server(
            server_id="custom_server",
            name="Custom Remote Server",
            transport=MCPTransportType.STREAMABLE_HTTP,
            endpoint="https://mcp.example.com/rpc"
        )
        self.assertTrue(res["success"])
        servers = self.client.list_servers()
        ids = [s["id"] for s in servers]
        self.assertIn("custom_server", ids)

    def test_discover_and_publish_tools(self):
        tools = self.client.discover_tools(force_refresh=True)
        self.assertTrue(len(tools) >= 2)
        tool_ids = [t["tool_id"] for t in tools]
        self.assertIn("mcp__ego_lite_browser__create_space", tool_ids)

        published = self.client.publish_tools_for_model()
        self.assertTrue(len(published) >= 2)
        self.assertEqual(published[0]["type"], "function")
        self.assertIn("parameters", published[0]["function"])

    def test_whitelisting_filtering(self):
        # Update ego_lite_browser to only whitelist create_space
        self.client.add_server(
            server_id="ego_lite_browser",
            name="CitroLabs Ego-Lite Browser",
            transport=MCPTransportType.STDIO,
            whitelist=["create_space"]
        )
        tools = self.client.discover_tools(force_refresh=True)
        ego_tools = [t["name"] for t in tools if t["server_id"] == "ego_lite_browser"]
        self.assertEqual(ego_tools, ["create_space"])

    def test_call_tool(self):
        res = self.client.call_tool("mcp__ego_lite_browser__create_space", {"space_name": "test-space"})
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "success")
        self.assertIn("space_id", res["result"])


if __name__ == "__main__":
    unittest.main()
