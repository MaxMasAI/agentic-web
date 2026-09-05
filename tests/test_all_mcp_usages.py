"""
test_all_mcp_usages.py - Comprehensive End-to-End Test Suite for All MCP Servers & Agent Usages
Tests Addy Osmani Agent Skills, CitroLabs Ego-Lite Browser Tools, and Multi-Agent Skills Routing.
"""

import sys
import os
import unittest
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.mcp_service import list_mcp_servers, list_mcp_tools, call_mcp_tool, load_mcp_config, get_skills_count
from core.agent_skills_router import get_agent_skills_directive, AGENT_SKILLS_MAP
from core import agentlist

class TestAllMCPUsages(unittest.TestCase):

    def test_01_standardized_mcp_server_registry(self):
        """1. Verify all registered MCP servers conform to the 9-field schema."""
        cfg = load_mcp_config()
        servers = cfg.get("mcpServers", {})
        self.assertIn("agent_skills", servers)
        self.assertIn("ego_lite_browser", servers)

        required_fields = ["name", "repository", "api_endpoint", "raw_base_url", "version", "skills_count", "status", "type", "description"]
        for sid, sdata in servers.items():
            for field in required_fields:
                self.assertIn(field, sdata, f"Server '{sid}' missing required standard field '{field}'")

    def test_02_addy_osmani_skills_remote_mcp(self):
        """2. Verify Addy Osmani remote engineering skills can be listed, fetched, and applied."""
        # A. List remote skills
        res_list = call_mcp_tool("mcp__agent_skills__list_remote_skills")
        self.assertEqual(res_list["status"], "success")
        self.assertGreaterEqual(res_list["result"]["count"], 1)

        # B. Fetch raw markdown runbook
        res_fetch = call_mcp_tool("mcp__agent_skills__fetch_skill_md", {"skill_name": "spec-driven-development"})
        self.assertEqual(res_fetch["status"], "success")
        self.assertIn("spec-driven-development", res_fetch["result"]["skill_name"])
        self.assertTrue(len(res_fetch["result"]["skill_markdown"]) > 20)

        # C. Apply skill to concrete task
        res_apply = call_mcp_tool("mcp__agent_skills__apply_remote_skill", {
            "skill_name": "test-driven-development",
            "task_goal": "Implement responsive shopping cart checkout with tax calculations"
        })
        self.assertEqual(res_apply["status"], "success")
        self.assertEqual(res_apply["result"]["status"], "ready_for_pipeline")

    def test_03_citrolabs_ego_lite_browser_mcp(self):
        """3. Verify CitroLabs Ego-Lite parallel browser spaces, navigation, snapshot, and script execution."""
        # A. Create Space
        res_space = call_mcp_tool("mcp__ego_lite__create_space", {"space_name": "agentic-e2e-testing"})
        self.assertEqual(res_space["status"], "success")
        space_id = res_space["result"]["space_id"]

        # B. Navigate inside Space
        res_nav = call_mcp_tool("mcp__ego_lite__navigate_and_extract", {
            "url": "https://example.com",
            "space_id": space_id
        })
        self.assertEqual(res_nav["status"], "success")
        self.assertEqual(res_nav["result"]["navigation_status"], "200_OK")

        # C. Capture Snapshot
        res_snap = call_mcp_tool("mcp__ego_lite__capture_snapshot", {"space_id": space_id})
        self.assertEqual(res_snap["status"], "success")
        self.assertTrue(res_snap["result"]["accessibility_tree_ready"])

        # D. Execute JavaScript
        res_exec = call_mcp_tool("mcp__ego_lite__execute_script", {
            "script": "return document.querySelectorAll('button').length;",
            "space_id": space_id
        })
        self.assertEqual(res_exec["status"], "success")
        self.assertTrue(res_exec["result"]["success"])

    def test_04_agent_skills_router_coverage(self):
        """4. Verify that every active agent receives appropriate engineering skills."""
        active_agents = agentlist.list_all_active_agents()
        self.assertEqual(len(active_agents), 10)

        for agent in active_agents:
            aid = agent["id"]
            directive = get_agent_skills_directive(aid)
            self.assertTrue(len(directive) > 0, f"Agent '{aid}' did not receive any skills directive!")
            self.assertIn("APPLIED SENIOR ENGINEERING SKILLS", directive)

    def test_05_skills_count_telemetry(self):
        """5. Verify skills count returns active skill count."""
        count = get_skills_count()
        self.assertGreaterEqual(count, 10)

if __name__ == "__main__":
    unittest.main()
