"""
test_agent_skills_router.py - Test Suite for agent_skills_router.py module.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.agent_skills_router import get_agent_skills_directive, AGENT_SKILLS_MAP

class TestAgentSkillsRouter(unittest.TestCase):

    def test_all_agents_have_mapped_skills(self):
        """Verify all 10 agents have mapped Addy Osmani skills."""
        expected_agents = ["gemini", "deepseek", "chatgpt", "claude", "perplexity", "nvidia_ai", "dalle", "meta_ai", "copilot", "mistral"]
        for aid in expected_agents:
            self.assertIn(aid, AGENT_SKILLS_MAP)
            self.assertGreaterEqual(len(AGENT_SKILLS_MAP[aid]), 1)

    def test_gemini_directive(self):
        """Verify Gemini receives Spec-Driven Development and Atomic Task Breakdown."""
        directive = get_agent_skills_directive("gemini")
        self.assertIn("Spec-Driven Development", directive)
        self.assertIn("Atomic Task Breakdown", directive)
        self.assertIn("APPLIED SENIOR ENGINEERING SKILLS", directive)

    def test_deepseek_directive(self):
        """Verify DeepSeek receives TDD, Defensive Programming, and Code Simplifier."""
        directive = get_agent_skills_directive("deepseek")
        self.assertIn("Test-Driven Development", directive)
        self.assertIn("Defensive Programming", directive)
        self.assertIn("Code Simplifier", directive)

    def test_claude_directive(self):
        """Verify Claude receives Architectural Review, Security Audit, and A11y Review."""
        directive = get_agent_skills_directive("claude")
        self.assertIn("Security & Boundary Audit", directive)
        self.assertIn("Accessibility (A11y) Review", directive)

if __name__ == "__main__":
    unittest.main()
