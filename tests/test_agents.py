"""
test_agents.py - Test Suite for agents.py module.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.agents import AGENT_SELECTORS

class TestAgents(unittest.TestCase):

    def test_all_major_agents_have_selectors(self):
        """Ensure all primary agents have input and response selectors configured."""
        required_agents = ["gemini", "deepseek", "chatgpt", "dalle", "claude", "perplexity", "copilot"]
        for agent_id in required_agents:
            self.assertIn(agent_id, AGENT_SELECTORS, f"Missing selector mapping for {agent_id}")
            entry = AGENT_SELECTORS[agent_id]
            self.assertIn("input", entry)
            self.assertIn("response", entry)

    def test_input_selectors_are_lists(self):
        """Verify input selectors are priority-ordered lists to prevent comma-separated wait_for_selector errors."""
        for agent_id, selectors in AGENT_SELECTORS.items():
            input_sel = selectors["input"]
            self.assertIsInstance(input_sel, list, f"{agent_id} input selectors should be a list")
            self.assertGreater(len(input_sel), 0, f"{agent_id} must have at least one input selector")

    def test_perplexity_selector_is_updated(self):
        """Verify Perplexity uses div#ask-input instead of obsolete textarea."""
        perp_inputs = AGENT_SELECTORS["perplexity"]["input"]
        self.assertIn("div#ask-input", perp_inputs)

if __name__ == "__main__":
    unittest.main()
