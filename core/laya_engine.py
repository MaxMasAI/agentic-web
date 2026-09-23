"""
core/laya_engine.py - Forwarding shim to core.system.laya_engine
"""
from core.system.laya_engine import *
import core.system.laya_engine as _impl

__all__ = [name for name in dir(_impl) if not name.startswith("__")]
