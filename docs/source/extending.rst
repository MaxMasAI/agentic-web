Extending & Custom Plugins
==========================

Developers can build and register custom plugins by subclassing `BasePlugin` in `core/plugin_base.py`.

Lifecycle Hooks
---------------
* `PREPARE_SYS_PROMPT`: Modify or prepend system prompt instructions.
* `PRE_MODEL_CALL`: Inspect or alter outgoing prompt payloads.
* `POST_MODEL_CALL`: Intercept model outputs or execute post-processing actions.
* `EXEC_TOOL`: Handle custom tool calls and return JSON responses.

Example Plugin
--------------
See `plugins/example_custom_plugin.py` for a complete reference implementation.
