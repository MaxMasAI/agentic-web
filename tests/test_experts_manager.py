"""
tests/test_experts_manager.py - Unit tests for Experts Co-op mode & isolated contexts
"""

import unittest
from unittest.mock import patch, MagicMock
from core.experts_manager import ExpertsManager, ExpertContext


class TestExpertsManager(unittest.TestCase):
    def setUp(self):
        self.manager = ExpertsManager(storage_path=":memory:")
        self.mock_llm_response = {
            "content": "Python expert response with code snippet.",
            "status": "success"
        }

    def test_default_experts_loaded(self):
        active = self.manager.list_active_experts()
        self.assertTrue(len(active) >= 5)
        ids = [e["id"] for e in active]
        self.assertIn("python_expert", ids)
        self.assertIn("web_dev_expert", ids)
        self.assertIn("data_analyst_expert", ids)

    def test_enable_disable_expert(self):
        self.assertTrue(self.manager.enable_expert("python_expert", False))
        active_ids = [e["id"] for e in self.manager.list_active_experts()]
        self.assertNotIn("python_expert", active_ids)

        self.assertTrue(self.manager.enable_expert("python_expert", True))
        active_ids = [e["id"] for e in self.manager.list_active_experts()]
        self.assertIn("python_expert", active_ids)

    def test_find_expert_by_reference(self):
        exp = self.manager.find_expert_by_reference("python")
        self.assertIsNotNone(exp)
        self.assertEqual(exp["id"], "python_expert")

        exp2 = self.manager.find_expert_by_reference("Full-Stack Web Architect")
        self.assertIsNotNone(exp2)
        self.assertEqual(exp2["id"], "web_dev_expert")

    @patch("core.experts_manager.generate_chat_response")
    def test_isolated_memory_context(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response

        # Interaction 1
        res1 = self.manager.call_expert("python_expert", "How to sort a dict?")
        self.assertTrue(res1["success"])
        ctx = self.manager.get_or_create_context("python_expert")
        self.assertEqual(len(ctx.messages), 2)

        # Interaction 2
        res2 = self.manager.call_expert("python_expert", "Show an example using operator.itemgetter")
        self.assertTrue(res2["success"])
        self.assertEqual(len(ctx.messages), 4)

        # Ensure other experts have empty contexts
        web_ctx = self.manager.get_or_create_context("web_dev_expert")
        self.assertEqual(len(web_ctx.messages), 0)

    @patch("core.experts_manager.generate_chat_response")
    def test_manager_turn_list_experts(self, mock_gen):
        result = self.manager.handle_manager_turn("Give me a list of active experts", [])
        self.assertIn("Active Experts in Co-op Mode", result["content"])

    @patch("core.experts_manager.generate_chat_response")
    def test_manager_turn_explicit_call(self, mock_gen):
        mock_gen.return_value = self.mock_llm_response
        result = self.manager.handle_manager_turn("Call the Python expert to reverse a string", [])
        self.assertIn("Python Programmer", result["content"])
        self.assertIn("Python expert response", result["content"])


if __name__ == "__main__":
    unittest.main()
