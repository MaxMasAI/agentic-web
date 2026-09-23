"""
core/plugin_base.py - Extensible Custom Plugin Engine & Lifecycle Framework
Allows developers and users to create custom plugins, LLM wrappers, vector stores,
audio providers, tools, and agents with event-driven lifecycle hooks.
"""

import os
import sys
import json
import shutil
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable


class PluginEvent:
    USER_PROMPT = "user_prompt"
    PRE_MODEL_CALL = "pre_model_call"
    POST_MODEL_CALL = "post_model_call"
    PREPARE_SYS_PROMPT = "prepare_sys_prompt"
    EXECUTE_COMMAND = "execute_command"
    RENDER_UI = "render_ui"


class BasePlugin:
    """
    Base class for all custom plugins.
    Subclass this class to create custom extensions.
    """
    id: str = "base_plugin"
    name: str = "Base Plugin"
    description: str = "Base plugin class."
    version: str = "1.0.0"
    author: str = "Developer"

    def __init__(self):
        self.options: Dict[str, Any] = {}
        self.enabled: bool = True
        self.setup_options()

    def setup_options(self):
        """Define configurable options for this plugin."""
        pass

    def add_option(self, key: str, option_type: str, value: Any, label: str, description: str = ""):
        """Helper to register a plugin option."""
        self.options[key] = {
            "type": option_type,  # bool, int, float, str, select, text
            "value": value,
            "label": label,
            "description": description
        }

    def get_option(self, key: str, default: Any = None) -> Any:
        opt = self.options.get(key)
        return opt["value"] if opt else default

    def set_option(self, key: str, value: Any):
        if key in self.options:
            self.options[key]["value"] = value

    def handle_event(self, event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Lifecycle hook invoked on system events.
        Override to intercept prompts, system instructions, or tool executions.
        """
        return data

    def attach_tools(self) -> List[Dict[str, Any]]:
        """
        Returns list of custom tool definitions published to AI models.
        """
        return []

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a registered tool.
        """
        return {"success": False, "error": f"Tool '{tool_name}' not implemented."}


class GenericAdapterPlugin(BasePlugin):
    """Wraps generic function-based or class-based dynamic plugins."""
    def __init__(self, plugin_id: str, name: str, version: str, description: str, author: str, instance: Any = None):
        self.id = plugin_id
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.raw_instance = instance
        super().__init__()

    def handle_event(self, event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        if self.raw_instance and hasattr(self.raw_instance, "handle_event"):
            try:
                return self.raw_instance.handle_event(event_name, data)
            except Exception:
                pass
        return data

    def attach_tools(self) -> List[Dict[str, Any]]:
        if self.raw_instance and hasattr(self.raw_instance, "attach_tools"):
            try:
                return self.raw_instance.attach_tools()
            except Exception:
                pass
        return []

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if self.raw_instance and hasattr(self.raw_instance, "execute_tool"):
            try:
                return self.raw_instance.execute_tool(tool_name, arguments)
            except Exception as e:
                return {"success": False, "error": str(e)}
        return super().execute_tool(tool_name, arguments)


class PluginManager:
    """
    Manages custom plugin loading, discovery, persistence, and event dispatching.
    Supports both standalone .py plugins and directory-based plugins with plugin.json manifests.
    """
    def __init__(self, plugins_dir: Optional[str] = None, app_context: Optional[Any] = None):
        self.plugins_dir = Path(plugins_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins"))
        self.app_context = app_context
        self.plugins: Dict[str, BasePlugin] = {}
        self.plugin_metadata: Dict[str, Dict[str, Any]] = {}
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.load_builtin_plugins()
        self.discover_custom_plugins()

    def register_plugin(self, plugin_instance: BasePlugin, metadata: Optional[Dict[str, Any]] = None):
        self.plugins[plugin_instance.id] = plugin_instance
        self.plugin_metadata[plugin_instance.id] = metadata or {
            "id": plugin_instance.id,
            "name": plugin_instance.name,
            "version": plugin_instance.version,
            "description": plugin_instance.description,
            "author": plugin_instance.author,
            "path": str(self.plugins_dir),
            "enabled": plugin_instance.enabled
        }

    def load_builtin_plugins(self):
        """Registers built-in service plugins."""
        pass

    def discover_custom_plugins(self):
        """Dynamically imports and registers all plugins from the plugins/ directory."""
        if not self.plugins_dir.exists():
            return

        for entry in self.plugins_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith((".", "__")):
                manifest_file = entry / "plugin.json"
                if manifest_file.is_file():
                    self.load_single_plugin(entry)

            elif entry.is_file() and entry.suffix == ".py" and not entry.name.startswith("__"):
                # Skip installer helper scripts if in plugins directory
                if entry.name in ("plugin_installer.py", "plugin_manager.py", "plugin_installer_dialog.py"):
                    continue
                self.load_standalone_file(entry)

    def load_single_plugin(self, plugin_dir: Path) -> Tuple[bool, str]:
        """Loads a directory-based plugin with a plugin.json manifest."""
        manifest_file = plugin_dir / "plugin.json"
        if not manifest_file.is_file():
            return False, f"Manifest not found in {plugin_dir}"

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            plugin_id = manifest.get("id")
            if not plugin_id:
                return False, "Manifest missing 'id' field."

            ep_file = manifest.get("entrypoint", "plugin.py")
            ep_path = plugin_dir / ep_file
            if not ep_path.is_file():
                return False, f"Entrypoint '{ep_file}' not found."

            plugin_dir_str = str(plugin_dir.resolve())
            if plugin_dir_str not in sys.path:
                sys.path.insert(0, plugin_dir_str)

            mod_name = f"installed_plugins_{plugin_id}"
            spec = importlib.util.spec_from_file_location(mod_name, str(ep_path))
            if not spec or not spec.loader:
                return False, f"Could not create module spec for {ep_path}"

            module = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = module
            spec.loader.exec_module(module)

            # 1. Look for BasePlugin subclass
            instance = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr not in (BasePlugin, GenericAdapterPlugin):
                    instance = attr()
                    break

            # 2. Look for register/init hook
            if instance is None:
                for hook_name in ("register", "init_plugin", "setup", "main"):
                    if hasattr(module, hook_name) and callable(getattr(module, hook_name)):
                        hook_fn = getattr(module, hook_name)
                        try:
                            raw_inst = hook_fn(self.app_context)
                        except TypeError:
                            raw_inst = hook_fn()

                        instance = GenericAdapterPlugin(
                            plugin_id=plugin_id,
                            name=manifest.get("name", plugin_id),
                            version=manifest.get("version", "1.0.0"),
                            description=manifest.get("description", ""),
                            author=manifest.get("author", "Unknown"),
                            instance=raw_inst
                        )
                        break

            if instance:
                meta = {
                    "id": plugin_id,
                    "name": manifest.get("name", plugin_id),
                    "version": manifest.get("version", "1.0.0"),
                    "description": manifest.get("description", ""),
                    "author": manifest.get("author", "Unknown"),
                    "entrypoint": ep_file,
                    "path": str(plugin_dir),
                    "enabled": True
                }
                self.register_plugin(instance, meta)
                return True, "Plugin loaded successfully."

            return False, "No valid BasePlugin class or register() hook found in entrypoint."
        except Exception as e:
            return False, f"Error loading plugin: {e}"

    def load_standalone_file(self, script_path: Path) -> Tuple[bool, str]:
        """Loads a standalone .py plugin."""
        fname = script_path.name
        mod_name = f"custom_plugin_{fname[:-3]}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, str(script_path))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr not in (BasePlugin, GenericAdapterPlugin):
                        instance = attr()
                        meta = {
                            "id": instance.id,
                            "name": instance.name,
                            "version": instance.version,
                            "description": instance.description,
                            "author": instance.author,
                            "path": str(script_path),
                            "enabled": instance.enabled
                        }
                        self.register_plugin(instance, meta)
                        return True, "Standalone plugin loaded."
            return False, "No BasePlugin class found."
        except Exception as e:
            return False, f"Failed to load file: {e}"

    def uninstall_plugin(self, plugin_id: str) -> Tuple[bool, str]:
        """Unregisters plugin and removes its directory from plugins/ folder."""
        meta = self.plugin_metadata.get(plugin_id)
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
        if plugin_id in self.plugin_metadata:
            del self.plugin_metadata[plugin_id]

        target_dir = self.plugins_dir / plugin_id
        if target_dir.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
            return True, f"Plugin '{plugin_id}' uninstalled successfully."

        if meta and meta.get("path") and os.path.exists(meta["path"]):
            p = meta["path"]
            if os.path.isdir(p):
                shutil.rmtree(p, ignore_errors=True)
            else:
                os.remove(p)
            return True, f"Plugin '{plugin_id}' deleted."

        return True, f"Plugin '{plugin_id}' unregistered."

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Returns list of all active loaded plugins with metadata."""
        out = []
        for pid, p in self.plugins.items():
            meta = self.plugin_metadata.get(pid, {})
            out.append({
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "version": p.version,
                "author": p.author,
                "enabled": p.enabled,
                "options": p.options,
                "path": meta.get("path", str(self.plugins_dir))
            })
        return out

    def dispatch_event(self, event_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an event through all enabled plugins."""
        current_data = data
        for p in self.plugins.values():
            if p.enabled:
                try:
                    current_data = p.handle_event(event_name, current_data)
                except Exception:
                    pass
        return current_data

    def get_all_attached_tools(self) -> List[Dict[str, Any]]:
        tools = []
        for p in self.plugins.values():
            if p.enabled:
                try:
                    p_tools = p.attach_tools()
                    for t in p_tools:
                        t["plugin_id"] = p.id
                        tools.append(t)
                except Exception:
                    pass
        return tools

    def evaluate_plugin_laya_contract(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Evaluates plugin tool call using LAYA System 1 Decision Contract."""
        try:
            from core.laya_engine import LayaDecisionEngine, DEFAULT_PLUGIN_CONTRACT
            engine = LayaDecisionEngine.get_instance()
            state = engine.normalize_state(
                raw_payload=f"plugin_tool_call:{tool_name}",
                context_attributes={"tool_name": tool_name, "arguments": arguments}
            )
            return engine.evaluate_contract(state, DEFAULT_PLUGIN_CONTRACT)
        except Exception:
            return None

    def call_plugin_tool(self, tool_name: str, arguments: Dict[str, Any], enforce_laya_gating: bool = True) -> Dict[str, Any]:
        """
        Executes a registered tool with LAYA System 1 gatekeeping and security isolation.
        """
        laya_result = None
        if enforce_laya_gating:
            laya_result = self.evaluate_plugin_laya_contract(tool_name, arguments)

        for p in self.plugins.values():
            if p.enabled:
                tools = p.attach_tools()
                if any(t.get("name") == tool_name for t in tools):
                    res = p.execute_tool(tool_name, arguments)
                    if isinstance(res, dict) and laya_result is not None:
                        res["laya_telemetry"] = {
                            "latency_ms": laya_result.latency_ms,
                            "privilege_level": laya_result.urgency_tier,
                            "requires_sandbox": laya_result.decisions.get("requires_sandbox_isolation", False),
                            "is_security_sensitive": laya_result.is_security_sensitive,
                            "fast_path_eligible": laya_result.fast_path_eligible
                        }
                    return res
        return {"success": False, "error": f"No active plugin found for tool '{tool_name}'."}


# Global Singleton
_plugin_manager: Optional[PluginManager] = None

def get_plugin_manager(app_context: Optional[Any] = None) -> PluginManager:
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager(app_context=app_context)
    elif app_context and _plugin_manager.app_context is None:
        _plugin_manager.app_context = app_context
    return _plugin_manager
