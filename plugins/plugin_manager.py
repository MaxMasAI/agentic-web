"""
plugin_manager.py - Re-export from core/plugin_base.py.
All core plugin management logic is centralized in core/plugin_base.py.
"""
from core.plugin_base import BasePlugin, PluginEvent, PluginManager, get_plugin_manager

__all__ = ["BasePlugin", "PluginEvent", "PluginManager", "get_plugin_manager"]
