"""
core.system - Autonomous System Control, Computer Use & Main Orchestration Engine
"""

from core.system import computer_use
from core.system import main

# Re-export key classes and functions
from core.system.computer_use import (
    ComputerUseEngine,
    ComputerUseEnvironment,
    get_computer_use_engine,
)

__all__ = [
    "computer_use",
    "main",
    "ComputerUseEngine",
    "ComputerUseEnvironment",
    "get_computer_use_engine",
]
