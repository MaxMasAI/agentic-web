"""
core.harness - MaxMasAI Harness Developer Preview & Plugin Framework
"""

from core.harness import maxmasai_harness
from core.harness import plugin_base

# Re-export key classes and functions
from core.harness.maxmasai_harness import (
    MaxMasAIHarnessEngine,
    HarnessStep,
    HarnessResult,
    get_maxmasai_harness_engine,
)
from core.harness.plugin_base import (
    BasePlugin,
    PluginManager,
    PluginEvent,
    get_plugin_manager,
)

__all__ = [
    "maxmasai_harness",
    "plugin_base",
    "MaxMasAIHarnessEngine",
    "HarnessStep",
    "HarnessResult",
    "get_maxmasai_harness_engine",
    "BasePlugin",
    "PluginManager",
    "PluginEvent",
    "get_plugin_manager",
]
