"""
core/experts_manager.py - Forwarding shim to core.agents.experts_manager
"""
from core.agents.experts_manager import *
import core.agents.experts_manager as _impl

__all__ = [name for name in dir(_impl) if not name.startswith("__")]
