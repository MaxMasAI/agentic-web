"""
gui/widgets/plugin_installer_dialog.py - Re-export for GUI subsystem from plugins package
"""
from plugins.plugin_installer import PluginInstallerDialog, GitCloneWorker

__all__ = ["PluginInstallerDialog", "GitCloneWorker"]
