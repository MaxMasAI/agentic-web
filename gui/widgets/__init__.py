"""
gui/widgets/__init__.py - Reusable GUI Widgets Suite
"""

from gui.widgets.metric_card import MetricCard
from gui.widgets.pool_monitor import PoolMonitor, AddAgentCard
from gui.widgets.add_agent_dialog import AddAgentDialog
from gui.widgets.terminal_view import TerminalView
from gui.widgets.lightbox import LightboxDialog
from gui.widgets.workflow_hud_widget import WorkflowHUDWidget, AgentWorkflowCard
from gui.widgets.custom_widget_registry import CustomWidgetRegistry, get_custom_widget_registry
from gui.widgets.custom_title_bar import CustomTitleBar

__all__ = [
    "MetricCard",
    "PoolMonitor",
    "AddAgentCard",
    "AddAgentDialog",
    "TerminalView",
    "LightboxDialog",
    "WorkflowHUDWidget",
    "AgentWorkflowCard",
    "CustomWidgetRegistry",
    "get_custom_widget_registry",
    "CustomTitleBar"
]
