"""
core/agent_skills_router.py - Forwarding shim to core.agents.agent_skills_router
"""
from core.agents.agent_skills_router import *
import core.agents.agent_skills_router as _impl

__all__ = [name for name in dir(_impl) if not name.startswith("__")]
