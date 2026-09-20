"""
core/computer_use.py - Forwarding shim to core.system.computer_use
"""
from core.system.computer_use import *
import core.system.computer_use as _impl

__all__ = [name for name in dir(_impl) if not name.startswith("__")]
