"""
tests/test_plugin_base.py - Unit tests for Custom Plugin Engine
"""

import unittest
from core.plugin_base import PluginManager, PluginEvent, BasePlugin
from plugins.example_custom_plugin import CustomExamplePlugin


class TestPluginBase(unittest.TestCase):
    def setUp(self):
        self.manager = PluginManager()

    def test_plugin_discovery_and_registration(self):
        plugins = self.manager.list_plugins()
        self.assertTrue(len(plugins) >= 1)
        ids = [p["id"] for p in plugins]
        self.assertIn("custom_example_plugin", ids)

    def test_plugin_options(self):
        plugin = self.manager.plugins.get("custom_example_plugin")
        self.assertIsNotNone(plugin)
        self.assertFalse(plugin.get_option("enable_uppercase_override"))

        plugin.set_option("enable_uppercase_override", True)
        self.assertTrue(plugin.get_option("enable_uppercase_override"))

    def test_event_dispatching(self):
        plugin = self.manager.plugins.get("custom_example_plugin")
        plugin.set_option("enable_uppercase_override", False)
        plugin.set_option("custom_signature", "Custom Test Signature")

        data = {"content": "Here is the response."}
        modified = self.manager.dispatch_event(PluginEvent.POST_MODEL_CALL, data)
        self.assertIn("Custom Test Signature", modified["content"])

    def test_tool_attachment_and_execution(self):
        tools = self.manager.get_all_attached_tools()
        names = [t["name"] for t in tools]
        self.assertIn("calculate_custom_metric", names)

        exec_res = self.manager.call_plugin_tool("calculate_custom_metric", {"x": 5, "y": 10, "operation": "multiply"})
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["result"], 50)


if __name__ == "__main__":
    unittest.main()
