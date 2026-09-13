"""
plugin_installer_dialog.py - Re-export from plugins package for backward compatibility.
All core installer logic is located in plugins/plugin_installer.py.
"""
from plugins.plugin_installer import PluginInstallerDialog, GitCloneWorker

__all__ = ["PluginInstallerDialog", "GitCloneWorker"]
