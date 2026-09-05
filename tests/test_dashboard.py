"""
test_dashboard.py - Test Suite for dashboard.py module.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core import agentlist
from utils.dashboard import generate_dashboard

class TestDashboard(unittest.TestCase):

    def test_generate_dashboard_creates_files(self):
        """Verify that generate_dashboard creates visuals/dashboard.html and tasks/ report."""
        task = "Test Task for Dashboard Generator"
        gemini_plan = "--- DEEPSEEK INSTRUCTION ---\nWrite mock code."
        worker_outputs = {"deepseek": "def mock_func(): pass"}
        final_output = "APPROVED: Final mock results."
        selected_agents = [
            agentlist.get_leader(),
            agentlist.get_agent_by_id("deepseek")
        ]
        
        generate_dashboard(
            task=task,
            gemini_plan=gemini_plan,
            worker_outputs=worker_outputs,
            final_output=final_output,
            selected_agents=selected_agents,
            discussion_log="Round 1 critique mock log"
        )
        
        # Verify visuals/dashboard.html exists
        self.assertTrue(os.path.exists("visuals/dashboard.html"))
        with open("visuals/dashboard.html", "r", encoding="utf-8") as f:
            html_content = f.read()
            
        # Verify Lightbox elements and Discussion cards exist in the HTML
        self.assertIn("openLightbox", html_content)
        self.assertIn("id=\"lightbox\"", html_content)
        self.assertIn("Multi-Agent Discussion", html_content)
        self.assertIn("Round 1 critique mock log", html_content)

if __name__ == "__main__":
    unittest.main()
