"""
plugins/example_custom_plugin.py - Example Custom Plugin Implementation
Demonstrates how to build, configure, and register a custom plugin with options,
lifecycle hooks, and callable tools.
"""

from core.plugin_base import BasePlugin, PluginEvent
from typing import Dict, List, Any


class CustomExamplePlugin(BasePlugin):
    id = "custom_example_plugin"
    name = "Custom Example Plugin"
    description = "Demonstrates how to create custom plugins with options and tool execution."
    version = "1.0.0"
    author = "Agentic Developer"

    def setup_options(self):
        """Define options that appear in plugin configuration."""
        self.add_option(
            key="enable_uppercase_override",
            option_type="bool",
            value=False,
            label="Uppercase Response Override",
            description="Forces assistant responses into uppercase format."
        )
        self.add_option(
            key="custom_signature",
            option_type="text",
            value="— Sent via Custom Agentic Plugin",
            label="Response Signature",
            description="Appended to assistant responses."
        )

    def handle_event(self, event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intercepts system events.
        """
        if event_name == PluginEvent.PREPARE_SYS_PROMPT:
            # Append custom directive
            current_prompt = data.get("prompt", "")
            data["prompt"] = current_prompt + "\n[Custom Directive: Respond with precision and elegance.]"

        elif event_name == PluginEvent.POST_MODEL_CALL:
            # Modify or sign model response
            content = data.get("content", "")
            if self.get_option("enable_uppercase_override"):
                content = content.upper()
            sig = self.get_option("custom_signature")
            if sig:
                content = f"{content}\n\n*{sig}*"
            data["content"] = content

        return data

    def attach_tools(self) -> List[Dict[str, Any]]:
        """
        Exposes callable tools to the AI models.
        """
        return [
            {
                "name": "calculate_custom_metric",
                "description": "Calculates a custom mathematical metric based on inputs.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "number", "description": "First number"},
                        "y": {"type": "number", "description": "Second number"},
                        "operation": {"type": "string", "enum": ["add", "multiply", "power"], "description": "Operation"}
                    },
                    "required": ["x", "y", "operation"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handles execution of the attached tool.
        """
        if tool_name == "calculate_custom_metric":
            x = arguments.get("x", 0)
            y = arguments.get("y", 0)
            op = arguments.get("operation", "add")

            if op == "add":
                val = x + y
            elif op == "multiply":
                val = x * y
            elif op == "power":
                val = x ** y
            else:
                val = x + y

            return {"success": True, "result": val, "operation": op, "inputs": (x, y)}

        return {"success": False, "error": f"Unknown tool '{tool_name}'"}
