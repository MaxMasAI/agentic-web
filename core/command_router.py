"""
core/command_router.py - Forwarding shim to core.workflows.command_router
"""
from core.workflows.command_router import *
import core.workflows.command_router as _impl

__all__ = [name for name in dir(_impl) if not name.startswith("__")]
