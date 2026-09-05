"""
test_agentlist.py - Test Suite for agentlist.py module.
"""

import sys
import os
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import agentlist

class TestAgentList(unittest.TestCase):

    def test_leader_agent_structure(self):
        """Verify the master orchestrator (Gemini) has required metadata."""
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

if __name__ == "__main__":
    unittest.main()
