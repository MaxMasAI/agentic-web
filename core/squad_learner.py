"""
core/squad_learner.py - Forwarding shim to core.agents.squad_learner
"""
from core.agents.squad_learner import *
import core.agents.squad_learner as _impl

__all__ = [name for name in dir(_impl) if not name.startswith("__")]
