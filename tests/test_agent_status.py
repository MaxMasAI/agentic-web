"""
test_agent_status.py - Test Suite for agent_status.py module.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import agentlist
from core.agent_status import init_agent_status, set_agent_state, get_all_agent_status, reset_all_workers_to_free

class TestAgentStatus(unittest.TestCase):

    def setUp(self):
        self.agents = agentlist.list_all_active_agents()
        init_agent_status(self.agents)

    def test_init_agent_status(self):
        """Verify all agents are initialized with leader/free states."""
        status = get_all_agent_status()
        self.assertEqual(len(status), len(self.agents))
        self.assertEqual(status["gemini"]["state"], "LEADER")
        self.assertEqual(status["deepseek"]["state"], "FREE")
        self.assertEqual(status["chatgpt"]["state"], "FREE")

    def test_set_agent_state_busy_and_free(self):
        """Verify transitioning an agent from FREE to BUSY and back to FREE."""
        set_agent_state("deepseek", "BUSY", "Generating code")
        status = get_all_agent_status()
        self.assertEqual(status["deepseek"]["state"], "BUSY")
        self.assertEqual(status["deepseek"]["current_task"], "Generating code")

        set_agent_state("deepseek", "FREE")
        status = get_all_agent_status()
        self.assertEqual(status["deepseek"]["state"], "FREE")

    def test_reset_all_workers_to_free(self):
        """Verify reset_all_workers_to_free resets all workers."""
        set_agent_state("chatgpt", "BUSY", "Writing copy")
        set_agent_state("claude", "BUSY", "Auditing tone")
        
        reset_all_workers_to_free(self.agents)
        status = get_all_agent_status()
        self.assertEqual(status["chatgpt"]["state"], "FREE")
        self.assertEqual(status["claude"]["state"], "FREE")

if __name__ == "__main__":
    unittest.main()
