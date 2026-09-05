"""
tests/test_computer_use.py - Unit tests for Autonomous Computer Use Engine
"""

import unittest
from unittest.mock import patch
from core.computer_use import ComputerUseEngine, ComputerUseEnvironment


class TestComputerUseEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ComputerUseEngine(environment=ComputerUseEnvironment.WINDOWS, use_sandbox=True)

    def test_screen_size_detection(self):
        w, h = self.engine.get_screen_size()
        self.assertGreater(w, 0)
        self.assertGreater(h, 0)

    def test_mouse_actions(self):
        res_move = self.engine.mouse_move(100, 100)
        self.assertTrue(res_move["success"])

        res_click = self.engine.mouse_click(100, 100, button="left")
        self.assertTrue(res_click["success"])

    def test_type_and_press(self):
        res_type = self.engine.type_text("test")
        self.assertTrue(res_type["success"])

        res_key = self.engine.press_key("enter")
        self.assertTrue(res_key["success"])

    def test_command_interpreter(self):
        res1 = self.engine.execute_command_string("mouse_click(250, 400)")
        self.assertTrue(res1["success"])

        res2 = self.engine.execute_command_string("type_text('Hello World')")
        self.assertTrue(res2["success"])

        res3 = self.engine.execute_command_string("Click on Start Menu and open Notepad")
        self.assertTrue(res3["success"])


if __name__ == "__main__":
    unittest.main()
