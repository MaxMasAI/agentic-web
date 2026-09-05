"""
tests/test_mouse_keyboard_service.py - Unit tests for Mouse and Keyboard Control Service
"""

import unittest
from services.mouse_keyboard_service import MouseKeyboardService


class TestMouseKeyboardService(unittest.TestCase):
    def setUp(self):
        self.service = MouseKeyboardService()

    def test_get_and_move_mouse(self):
        pos = self.service.get_mouse_position()
        self.assertTrue(pos["success"])
        self.assertIn("x", pos)
        self.assertIn("y", pos)

        move_res = self.service.move_mouse(300, 300)
        self.assertTrue(move_res["success"])
        self.assertEqual(move_res["x"], 300)
        self.assertEqual(move_res["y"], 300)

    def test_mouse_clicks_and_scroll(self):
        click_res = self.service.mouse_click(300, 300, button="left")
        self.assertTrue(click_res["success"])

        scroll_res = self.service.mouse_scroll(clicks=2)
        self.assertTrue(scroll_res["success"])

    def test_keyboard_typing_and_keys(self):
        type_res = self.service.type_text("test_agent_input")
        self.assertTrue(type_res["success"])

        key_res = self.service.press_key("ctrl+c")
        self.assertTrue(key_res["success"])


if __name__ == "__main__":
    unittest.main()
