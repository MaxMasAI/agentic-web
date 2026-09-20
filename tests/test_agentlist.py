"""
test_agentlist.py - Test Suite for agentlist.py module, Custom Leader Logic, and Dynamic Agent Cursors.
"""

import sys
import os
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import agentlist
from system.system_cursor import get_agent_cursor_template, AGENT_CURSOR_TEMPLATES

class TestAgentList(unittest.TestCase):

    def setUp(self):
        # Reload default state before each test
        agentlist.reload_agents()

    def tearDown(self):
        # Clean up any test custom agent if left behind
        agentlist.remove_custom_agent("test_agent")
        agentlist.remove_custom_agent("test_py_agent")
        agentlist.remove_custom_agent("qwen_coder")
        agentlist.remove_custom_agent("custom_lead_ai")
        agentlist.reload_agents()

    def test_leader_agent_structure(self):
        """Verify default master orchestrator (Gemini) has required metadata."""
        leader = agentlist.get_leader()
        self.assertIsNotNone(leader)
        self.assertEqual(leader["id"], "gemini")
        self.assertTrue(leader["is_leader"])
        self.assertIn("https://", leader["official_url"])
        self.assertTrue(len(leader["specialization"]) > 0)

    def test_list_all_active_agents(self):
        """Verify that list_all_active_agents returns Gemini first followed by specialists."""
        agents = agentlist.list_all_active_agents()
        self.assertGreaterEqual(len(agents), 3)
        self.assertEqual(agents[0]["id"], "gemini")
        
        # Verify uniqueness of agent IDs
        ids = [a["id"] for a in agents]
        self.assertEqual(len(ids), len(set(ids)), "Agent IDs must be strictly unique.")

    def test_get_agent_by_id(self):
        """Verify lookup by agent ID works for valid and invalid IDs."""
        gemini = agentlist.get_agent_by_id("gemini")
        self.assertIsNotNone(gemini)
        self.assertEqual(gemini["name"], "Google Gemini")

        deepseek = agentlist.get_agent_by_id("deepseek")
        self.assertIsNotNone(deepseek)
        self.assertEqual(deepseek["id"], "deepseek")

        # Invalid agent
        unknown = agentlist.get_agent_by_id("non_existent_ai")
        self.assertIsNone(unknown)

    def test_parse_json_text_format(self):
        """Verify parsing agent data from standard JSON text."""
        json_text = '''
        {
            "id": "test_agent",
            "name": "Test Model Agent",
            "role": "QA Test Engineer",
            "specialization": "Automated testing and validation.",
            "official_url": "https://test.ai",
            "is_leader": false,
            "routing_tag": "[SEND_TO: test_agent]"
        }
        '''
        parsed, err = agentlist.parse_agent_text_format(json_text)
        self.assertEqual(err, "")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["id"], "test_agent")
        self.assertEqual(parsed["name"], "Test Model Agent")
        self.assertEqual(parsed["role"], "QA Test Engineer")
        self.assertFalse(parsed["is_leader"])

    def test_parse_python_dict_text_format(self):
        """Verify parsing agent data from Python dictionary text format."""
        py_text = """
        {
            "id": "test_py_agent",
            "name": "Python Dict Agent",
            "role": "Python Specialist",
            "specialization": (
                "Specialized Python AST parsing, refactoring, "
                "and test generation."
            ),
            "official_url": "https://python.org",
            "is_leader": False,
            "routing_tag": "[SEND_TO: test_py_agent]"
        }
        """
        parsed, err = agentlist.parse_agent_text_format(py_text)
        self.assertEqual(err, "")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["id"], "test_py_agent")
        self.assertIn("Python AST parsing", parsed["specialization"])

    def test_custom_leader_moves_gemini_to_specialists(self):
        """
        Verify that if any custom model is registered as leader (is_leader: True):
        1. That model becomes the active LEAD_AGENT.
        2. Gemini moves to the specialist agents list as a normal specialist.
        3. When custom leader is removed, Gemini reverts back to LEAD_AGENT.
        """
        new_leader_data = {
            "id": "custom_lead_ai",
            "name": "Custom Supreme Commander",
            "role": "Master Orchestrator AI",
            "specialization": "Global multi-agent task planning.",
            "official_url": "https://commander.ai",
            "is_leader": True,
            "routing_tag": "[SEND_TO: custom_lead_ai]"
        }
        success, msg = agentlist.add_custom_agent(new_leader_data)
        self.assertTrue(success)

        # 1. Custom model is now LEAD_AGENT
        cur_leader = agentlist.get_leader()
        self.assertEqual(cur_leader["id"], "custom_lead_ai")
        self.assertEqual(cur_leader["name"], "Custom Supreme Commander")
        self.assertTrue(cur_leader["is_leader"])

        # 2. Gemini is now in SPECIALIST_AGENTS as a normal specialist
        gemini = agentlist.get_agent_by_id("gemini")
        self.assertIsNotNone(gemini)
        self.assertFalse(gemini["is_leader"])
        
        all_specialist_ids = [a["id"] for a in agentlist.SPECIALIST_AGENTS]
        self.assertIn("gemini", all_specialist_ids)

        # Active agents list has custom_lead_ai first, followed by Gemini and other specialists
        all_active = agentlist.list_all_active_agents()
        self.assertEqual(all_active[0]["id"], "custom_lead_ai")
        active_ids = [a["id"] for a in all_active]
        self.assertIn("gemini", active_ids)
        self.assertEqual(len(active_ids), len(set(active_ids)), "Active IDs must have zero duplicates.")

        # 3. Remove custom leader and verify Gemini returns as leader
        del_success, del_msg = agentlist.remove_custom_agent("custom_lead_ai")
        self.assertTrue(del_success)
        
        restored_leader = agentlist.get_leader()
        self.assertEqual(restored_leader["id"], "gemini")
        self.assertTrue(restored_leader["is_leader"])

    def test_add_agent_dialog_presets(self):
        """Verify quick preset templates in AddAgentDialog parse cleanly."""
        from gui.widgets.add_agent_dialog import (
            DEFAULT_TEMPLATE, LEADER_TEMPLATE, RESEARCH_TEMPLATE, LOCAL_OLLAMA_TEMPLATE
        )
        
        for name, tmpl in [
            ("Specialist", DEFAULT_TEMPLATE),
            ("Leader", LEADER_TEMPLATE),
            ("Researcher", RESEARCH_TEMPLATE),
            ("Ollama", LOCAL_OLLAMA_TEMPLATE)
        ]:
            parsed, err = agentlist.parse_agent_text_format(tmpl)
            self.assertIsNotNone(parsed, f"Preset '{name}' failed to parse: {err}")
            self.assertTrue(len(parsed["id"]) > 0)
            self.assertTrue(len(parsed["name"]) > 0)
            self.assertTrue(len(parsed["role"]) > 0)

    def test_dynamic_cursor_templates(self):
        """Verify dynamic cursor templates for built-in and custom models."""
        # Test Gemini template
        gemini_tmpl = get_agent_cursor_template("gemini")
        self.assertEqual(gemini_tmpl["id"], "gemini")
        self.assertEqual(gemini_tmpl["icon"], "✨")
        self.assertEqual(gemini_tmpl["color"], "#7c3aed")

        # Test DeepSeek template
        deepseek_tmpl = get_agent_cursor_template("deepseek")
        self.assertEqual(deepseek_tmpl["id"], "deepseek")
        self.assertEqual(deepseek_tmpl["icon"], "🐋")
        self.assertEqual(deepseek_tmpl["color"], "#2563eb")

        # Test Claude template
        claude_tmpl = get_agent_cursor_template("claude")
        self.assertEqual(claude_tmpl["id"], "claude")
        self.assertEqual(claude_tmpl["icon"], "✴️")

        # Test System cursor template
        system_tmpl = get_agent_cursor_template("system")
        self.assertEqual(system_tmpl["id"], "system")
        self.assertEqual(system_tmpl["name"], "System")
        self.assertEqual(system_tmpl["color"], "#ef4444")
        self.assertIn("#ef4444", system_tmpl["gradient"])

        # Test Custom / Unknown model template generation
        custom_tmpl = get_agent_cursor_template("qwen_coder")
        self.assertEqual(custom_tmpl["id"], "qwen_coder")
        self.assertIn("gradient", custom_tmpl)
        self.assertIn("dot_color", custom_tmpl)


if __name__ == "__main__":
    unittest.main()
