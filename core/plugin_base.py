"""
core/plugin_base.py - Extensible Custom Plugin Engine & Lifecycle Framework
Allows developers and users to create custom plugins, LLM wrappers, vector stores,
audio providers, tools, and agents with event-driven lifecycle hooks.
"""

import os
import sys
import json
import importlib.util
from typing import Dict, List, Any, Optional, Callable


class PluginEvent:
    USER_PROMPT = "user_prompt"
    PRE_MODEL_CALL = "pre_model_call"
    POST_MODEL_CALL = "post_model_call"
    PREPARE_SYS_PROMPT = "prepare_sys_prompt"
    EXECUTE_COMMAND = "execute_command"
    RENDER_UI = "render_ui"


class BasePlugin:
    """
    Base class for all custom plugins.
    Subclass this class to create custom extensions.
    """
    id: str = "base_plugin"
    name: str = "Base Plugin"
    description: str = "Base plugin class."
    version: str = "1.0.0"
    author: str = "Developer"

    def __init__(self):
        self.options: Dict[str, Any] = {}
        self.enabled: bool = True
        self.setup_options()

    def setup_options(self):
        """Define configurable options for this plugin."""
        pass

    def add_option(self, key: str, option_type: str, value: Any, label: str, description: str = ""):
        """Helper to register a plugin option."""
        self.options[key] = {
            "type": option_type,  # bool, int, float, str, select, text
            "value": value,
            "label": label,
            "description": description
        }

    def get_option(self, key: str, default: Any = None) -> Any:
        opt = self.options.get(key)
        return opt["value"] if opt else default

    def set_option(self, key: str, value: Any):
        if key in self.options:
            self.options[key]["value"] = value

    def handle_event(self, event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lifecycle hook invoked on system events.
        Override to intercept prompts, system instructions, or tool executions.
        """
        return data

    def attach_tools(self) -> List[Dict[str, Any]]:
        """
        Returns list of custom tool definitions published to AI models.
        Example return:
        [
            {
                "name": "my_custom_tool",
                "description": "Performs custom calculation",
                "parameters": {"type": "object", "properties": {"val": {"type": "number"}}}
            }
        ]
        """
        return []

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a registered tool.
        """
        return {"success": False, "error": f"Tool '{tool_name}' not implemented."}


class PluginManager:
    """
    Manages custom plugin loading, discovery, persistence, and event dispatching.
    """
    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = plugins_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
        self.plugins: Dict[str, BasePlugin] = {}
        os.makedirs(self.plugins_dir, exist_ok=True)
        self.load_builtin_plugins()
        self.discover_custom_plugins()

    def register_plugin(self, plugin_instance: BasePlugin):
        self.plugins[plugin_instance.id] = plugin_instance

    def load_builtin_plugins(self):
        """Registers built-in service plugins."""
        pass

    def discover_custom_plugins(self):
        """Dynamically imports and registers plugins from the plugins/ directory."""
        if not os.path.exists(self.plugins_dir):
            return

        for fname in os.listdir(self.plugins_dir):
            if fname.endswith(".py") and not fname.startswith("__"):
                plugin_path = os.path.join(self.plugins_dir, fname)
                mod_name = f"custom_plugin_{fname[:-3]}"
                try:
                    spec = importlib.util.spec_from_file_location(mod_name, plugin_path)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        # Find BasePlugin subclasses
                        for attr_name in dir(mod):
                            attr = getattr(mod, attr_name)
                            if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                                instance = attr()
                                self.register_plugin(instance)
                except Exception:
                    pass

    def list_plugins(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "author": p.author,
                "enabled": p.enabled,
                "options": p.options
            }
            for p in self.plugins.values()
        ]

    def dispatch_event(self, event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an event through all enabled plugins."""
        current_data = data
        for p in self.plugins.values():
            if p.enabled:
                try:
                    current_data = p.handle_event(event_name, current_data)
                except Exception:
                    pass
        return current_data

    def get_all_attached_tools(self) -> List[Dict[str, Any]]:
        tools = []
        for p in self.plugins.values():
            if p.enabled:
                try:
                    p_tools = p.attach_tools()
                    for t in p_tools:
                        t["plugin_id"] = p.id
                        tools.append(t)
                except Exception:
                    pass
        return tools

    def call_plugin_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        for p in self.plugins.values():
            if p.enabled:
                tools = p.attach_tools()
                if any(t.get("name") == tool_name for t in tools):
                    return p.execute_tool(tool_name, arguments)
        return {"success": False, "error": f"No active plugin found for tool '{tool_name}'."}


# Global Singleton
_plugin_manager: Optional[PluginManager] = None

def get_plugin_manager() -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
