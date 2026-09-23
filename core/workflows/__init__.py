"""
core.workflows - Autonomous Workflows, Infinite Canvas Engine & Command Routing
"""

from core.workflows import agent_workflows
from core.workflows import canvas_engine
from core.workflows import command_router

# Re-export key classes and functions
from core.workflows.agent_workflows import (
    AgentWorkflowType,
    PRESETS,
    run_agent_workflow,
)
from core.workflows.canvas_engine import (
    CanvasEventBroker,
    AutonomousAgentWorker,
    CanvasNodeData,
    ConnectionEdgeData,
    ToolCallPayload,
    NodeContextStreamData,
    AgentTaskData,
)
from core.workflows.command_router import (
    AGENT_ALIASES,
    resolve_agent_id,
    parse_slash_task_command,
    route_task_with_laya,
)

__all__ = [
    "agent_workflows",
    "canvas_engine",
    "command_router",
    "AgentWorkflowType",
    "PRESETS",
    "run_agent_workflow",
    "CanvasEventBroker",
    "AutonomousAgentWorker",
    "CanvasNodeData",
    "ConnectionEdgeData",
    "ToolCallPayload",
    "NodeContextStreamData",
    "AgentTaskData",
    "AGENT_ALIASES",
    "resolve_agent_id",
    "parse_slash_task_command",
    "route_task_with_laya",
]

