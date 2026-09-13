"""
plugins/__init__.py - Custom Plugins, Extensions & Dynamic Git Installer Package
"""
from core.plugin_base import BasePlugin, PluginEvent, get_plugin_manager, PluginManager
from plugins.plugin_installer import PluginInstallerDialog, GitCloneWorker

__all__ = [
    "BasePlugin",
    "PluginEvent",
    "PluginManager",
    "get_plugin_manager",
    "PluginInstallerDialog",
    "GitCloneWorker",
]
