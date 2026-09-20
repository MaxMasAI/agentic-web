"""
core/main.py - Forwarding shim to core.system.main
"""
from core.system.main import *
import core.system.main as _impl

__all__ = [name for name in dir(_impl) if not name.startswith("__")]

if __name__ == "__main__":
    main()
