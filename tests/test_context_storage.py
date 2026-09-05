"""
tests/test_context_storage.py - Unit tests for Context and Memory SQLite Storage
"""

import unittest
import os
from services.context_storage import ContextDatabase, is_context_enabled, set_context_enabled


class TestContextStorage(unittest.TestCase):
    def setUp(self):
        self.db = ContextDatabase(db_path=":memory:")

    def test_create_and_list_context(self):
        ctx_id = "test-ctx-1"
        self.db.create_context(ctx_id, title="Python Debugging", model_id="gemini-2.0-flash")
        contexts = self.db.list_contexts()
        self.assertEqual(len(contexts), 1)
        self.assertEqual(contexts[0]["title"], "Python Debugging")

    def test_add_messages_and_retrieval(self):
        ctx_id = "test-ctx-2"
        self.db.add_message(ctx_id, "user", "How do I reverse a list in Python?")
        self.db.add_message(ctx_id, "assistant", "You can use list.reverse() or slicing [::-1].", model_tag="Gemini")

        messages = self.db.get_messages(ctx_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")

    def test_auto_title_generation(self):
        ctx_id = "test-ctx-3"
        self.db.add_message(ctx_id, "user", "Analyze the architecture of distributed databases")
        ctx = self.db.get_context(ctx_id)
        self.assertIsNotNone(ctx)
        self.assertTrue(len(ctx["title"]) > 5)
        self.assertIn("Analyze", ctx["title"])

    def test_update_title(self):
        ctx_id = "test-ctx-4"
        self.db.create_context(ctx_id, title="Initial Title")
        self.db.update_title(ctx_id, "Updated Custom Title")
        ctx = self.db.get_context(ctx_id)
        self.assertEqual(ctx["title"], "Updated Custom Title")

    def test_delete_and_clear_history(self):
        ctx_id = "test-ctx-5"
        self.db.add_message(ctx_id, "user", "Hello world")
        self.assertEqual(len(self.db.list_contexts()), 1)

        self.db.clear_all_history()
        self.assertEqual(len(self.db.list_contexts()), 0)
        self.assertEqual(len(self.db.get_messages(ctx_id)), 0)


if __name__ == "__main__":
    unittest.main()
