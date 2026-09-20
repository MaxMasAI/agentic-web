"""
core/discussion.py - Forwarding shim to core.agents.discussion
"""
from core.agents.discussion import *
import core.agents.discussion as _impl

__all__ = [name for name in dir(_impl) if not name.startswith("__")]
