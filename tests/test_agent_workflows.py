"""
tests/test_agent_workflows.py - Unit tests for all OpenAI Agent Workflows and Presets
"""

import unittest
from unittest.mock import patch
from core.agent_workflows import (
    AgentWorkflowType,
    PRESETS,
    run_agent_workflow
)


class TestAgentWorkflows(unittest.TestCase):
    def setUp(self):
        self.mock_llm_response = {
            "content": "Simulated genuine response from agent model.",
            "status": "success",
            "model": "test-model"
        }

    @patch("core.agent_workflows.generate_chat_response")
    def test_presets_structure(self, mock_gen):
        expected_presets = [
            "coder", "experts_agent", "planner", "research_bot",
            "simple_agent", "writer_feedback", "b2b", "supervisor_worker",
            "evolve", "autonomous"
        ]
        for p in expected_presets:
            self.assertIn(p, PRESETS)
            preset_data = PRESETS[p]
            self.assertIn("name", preset_data)
            self.assertIn("type", preset_data)
            self.assertIn("description", preset_data)
            self.assertIn("icon", preset_data)

    @patch("core.agent_workflows.generate_chat_response")
    def test_simple_agent_workflow(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        events = list(run_agent_workflow("Build a quick script", workflow_type=AgentWorkflowType.SIMPLE_AGENT))
        self.assertTrue(len(events) >= 2)
        self.assertTrue(any(e.get("is_final") for e in events))

    @patch("core.agent_workflows.generate_chat_response")
    def test_agent_feedback_workflow(self, mock_gen):
        mock_gen.return_value = {"content": "PASS - Draft is well structured.", "status": "success"}
        events = list(run_agent_workflow("Write an article", workflow_type=AgentWorkflowType.AGENT_FEEDBACK, max_iterations=2))
        self.assertTrue(len(events) >= 3)
        self.assertTrue(any(e.get("is_final") for e in events))

    @patch("core.agent_workflows.generate_chat_response")
    def test_agent_experts_workflow(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        events = list(run_agent_workflow("Design system architecture", workflow_type=AgentWorkflowType.AGENT_EXPERTS, preset_key="experts_agent"))
        self.assertTrue(len(events) >= 3)
        self.assertTrue(any(e.get("is_final") for e in events))

    @patch("core.agent_workflows.generate_chat_response")
    def test_planner_workflow(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        events = list(run_agent_workflow("Organize cloud migration", workflow_type=AgentWorkflowType.PLANNER))
        self.assertTrue(len(events) >= 4)
        self.assertTrue(any(e.get("is_final") for e in events))

    @patch("core.agent_workflows.generate_chat_response")
    def test_research_bot_workflow(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        events = list(run_agent_workflow("Analyze quantum computing trends", workflow_type=AgentWorkflowType.RESEARCH_BOT))
        self.assertTrue(len(events) >= 4)
        self.assertTrue(any(e.get("is_final") for e in events))

    @patch("core.agent_workflows.generate_chat_response")
    def test_b2b_workflow(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        events = list(run_agent_workflow("Debate microservices vs monolith", workflow_type=AgentWorkflowType.B2B, max_iterations=2))
        self.assertTrue(len(events) >= 4)
        self.assertTrue(any(e.get("is_final") for e in events))

    @patch("core.agent_workflows.generate_chat_response")
    def test_supervisor_worker_workflow(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        events = list(run_agent_workflow("Audit database schemas", workflow_type=AgentWorkflowType.SUPERVISOR_WORKER))
        self.assertTrue(len(events) >= 4)
        self.assertTrue(any(e.get("is_final") for e in events))

    @patch("core.agent_workflows.generate_chat_response")
    def test_evolve_workflow(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        events = list(run_agent_workflow("Optimize algorithm latency", workflow_type=AgentWorkflowType.EVOLVE))
        self.assertTrue(len(events) >= 4)
        self.assertTrue(any(e.get("is_final") for e in events))

    @patch("core.agent_workflows.generate_chat_response")
    def test_autonomous_workflow(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        events = list(run_agent_workflow("Autonomous task discovery", workflow_type=AgentWorkflowType.AUTONOMOUS, max_iterations=2))
        self.assertTrue(len(events) >= 4)
        self.assertTrue(any(e.get("is_final") for e in events))


if __name__ == "__main__":
    unittest.main()
