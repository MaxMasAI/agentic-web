"""
core package - Modular Multi-Agent Engine, Orchestration, Workflows, Harness & System Architecture

Organized into dedicated subpackages:
- core.agents: Agent registry, profiles, squad learner, discussion & status
- core.workflows: Autonomous workflows, infinite canvas execution & command routing
- core.harness: MaxMasAI developer preview evaluation harness & hot-pluggable plugin ecosystem
- core.system: Computer Use automation & main engine loop
"""

# Sub-packages
from core import agents
from core import workflows
from core import harness
from core import system

# Re-export key modules for direct/legacy core namespace access
from core import agentlist
from core import agent_status
from core import agent_skills_router
from core import squad_learner
from core import discussion
from core import experts_manager
from core import agent_workflows
from core import canvas_engine
from core import command_router
from core import maxmasai_harness
from core import plugin_base
from core import computer_use

__all__ = [
    "agents",
    "workflows",
    "harness",
    "system",
    "agentlist",
    "agent_status",
    "agent_skills_router",
    "squad_learner",
    "discussion",
    "experts_manager",
    "agent_workflows",
    "canvas_engine",
    "command_router",
    "maxmasai_harness",
    "plugin_base",
    "computer_use",
]
