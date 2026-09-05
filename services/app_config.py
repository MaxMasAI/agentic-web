"""
services/app_config.py - Centralized Application Configuration & Settings Manager
Maintains and persists all layout, syntax, file attachment, context, and tool configurations.
"""

import os
import json
from typing import Any, Dict

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "json", "app_config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    # Layout Settings
    "layout.style.chat": "chatgpt",
    "layout.chat_zoom": 1.0,
    "layout.font_size.chat": 12,
    "layout.font_size.input": 12,
    "layout.font_size.ctx_list": 12,
    "layout.font_size.toolbox": 12,
    "layout.density": 0,
    "layout.dpi_factor": 1.0,
    "layout.dpi_scaling": True,
    "layout.auto_collapse_user_msg_px": 1500,
    "layout.display_tips": True,
    "layout.store_dialog_positions": True,

    # Code Syntax Settings
    "syntax.theme": "github-dark",
    "syntax.disabled": False,
    "syntax.stream_highlight_every_n_lines": 50,
    "syntax.stream_highlight_every_n_chars": 300,
    "syntax.stream_max_lines": 300,
    "syntax.static_max_lines": 1500,
    "syntax.static_max_chars": 350000,

    # Files and Attachments Settings
    "attachments.store_in_workdir_upload": True,
    "attachments.prefer_native_upload": False,
    "attachments.store_in_data_dir": False,
    "attachments.allow_images_as_context": False,
    "attachments.append_mode": "always",
    "attachments.append_only_once": False,
    "attachments.model_summary": "gpt-4o-mini",
    "rag.model_query": "gpt-4o-mini",
    "rag.use_history": True,
    "rag.history_limit": 5,
    "downloads.dir": "download",

    # Context Settings
    "context.per_load": 1000,
    "context.model_auto_summary": "gpt-4o-mini",
    "context.auto_summary": True,
    "context.show_projects_on_top": False,
    "context.show_date_separators": True,
    "context.show_date_separators_in_projects": True,
    "context.show_date_separators_in_pinned": False,
    "context.use_context": True,
    "context.store_history": True,
    "context.store_time_in_history": True,
    "context.lock_incompatible_modes": True,
    "context.search_content": False,
    "context.show_llamaindex_sources": True,
    "context.show_reasoning_realtime": True,
    "context.hide_reasoning_after_response": True,
    "context.use_extra_context_output": True,
    "browser.open_urls_in_builtin": True,

    # Remote Tools Settings
    "tools.remote_enabled": True
}


class ConfigManager:
    """Manages application-wide persistent preferences and configuration state."""
    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.config: Dict[str, Any] = {}
        self.load()

    def load(self) -> Dict[str, Any]:
        """Loads configuration from JSON, seeding defaults if missing."""
        self.config = dict(DEFAULT_CONFIG)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.config.update(data)
            except Exception as e:
                print(f"[ConfigManager] Error reading config file: {e}")
        else:
            self.save()
        return self.config

    def save(self) -> bool:
        """Persists current configuration dictionary to disk."""
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
            return True
        except Exception as e:
            print(f"[ConfigManager] Error saving config file: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value by dot-notated key."""
        return self.config.get(key, DEFAULT_CONFIG.get(key, default))

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """Sets a configuration value and optionally writes to disk."""
        self.config[key] = value
        if auto_save:
            self.save()

    def reset_to_defaults(self) -> None:
        """Restores all configuration parameters back to their factory defaults."""
        self.config = dict(DEFAULT_CONFIG)
        self.save()


# Singleton Instance
config = ConfigManager()
