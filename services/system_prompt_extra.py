"""
services/system_prompt_extra.py - System Prompt Extra (append) Plugin Engine
Automatically appends extra system instructions and custom prompt directives to every system prompt.
"""

import os
import json
from typing import Dict, List, Any, Optional

EXTRAS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "system_prompt_extras.json")

DEFAULT_EXTRAS = [
    {
        "id": "code_style_guidelines",
        "name": "Production Code Quality & Type Annotations",
        "content": "Always produce clean, robust, modern, production-grade code with explicit type hints, error handling, and inline documentation.",
        "enabled": True,
        "priority": 1
    },
    {
        "id": "factual_grounding",
        "name": "Factual Grounding & Honest Limits",
        "content": "Provide direct, factual, and verified answers. If uncertain or lacking access to live data, clearly state limitations rather than guessing.",
        "enabled": True,
        "priority": 2
    },
    {
        "id": "structured_formatting",
        "name": "Structured Markdown & Ergonomics",
        "content": "Format complex technical explanations using structured markdown headers, bulleted lists, and language-tagged code blocks.",
        "enabled": True,
        "priority": 3
    }
]


class SystemPromptExtraService:
    """
    Manages custom system prompt extra directives and automatically
    appends active extra data to outgoing model system prompts.
    """
    def __init__(self, config_path: str = EXTRAS_FILE):
        self.config_path = config_path
        self.extras: Dict[str, Dict[str, Any]] = {}
        self.load_extras()

    def load_extras(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.extras = {e["id"]: e for e in data}
                    elif isinstance(data, dict):
                        self.extras = data
                    return
            except Exception:
                pass

        self.extras = {e["id"]: e for e in DEFAULT_EXTRAS}
        self.save_extras()

    def save_extras(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(list(self.extras.values()), f, indent=2)
        except Exception:
            pass

    def list_extras(self) -> List[Dict[str, Any]]:
        return sorted(list(self.extras.values()), key=lambda x: x.get("priority", 99))

    def add_extra(self, extra_id: str, name: str, content: str, enabled: bool = True, priority: int = 10) -> Dict[str, Any]:
        item = {
            "id": extra_id,
            "name": name,
            "content": content.strip(),
            "enabled": enabled,
            "priority": priority
        }
        self.extras[extra_id] = item
        self.save_extras()
        return item

    def update_extra(
        self,
        extra_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        enabled: Optional[bool] = None,
        priority: Optional[int] = None
    ) -> bool:
        if extra_id in self.extras:
            if name is not None:
                self.extras[extra_id]["name"] = name
            if content is not None:
                self.extras[extra_id]["content"] = content.strip()
            if enabled is not None:
                self.extras[extra_id]["enabled"] = enabled
            if priority is not None:
                self.extras[extra_id]["priority"] = priority
            self.save_extras()
            return True
        return False

    def toggle_extra(self, extra_id: str, enabled: bool) -> bool:
        return self.update_extra(extra_id, enabled=enabled)

    def delete_extra(self, extra_id: str) -> bool:
        if extra_id in self.extras:
            del self.extras[extra_id]
            self.save_extras()
            return True
        return False

    def build_extra_prompt_text(self) -> str:
        active_items = [e for e in self.list_extras() if e.get("enabled", True)]
        if not active_items:
            return ""

        lines = ["\n\n### Extra System Instructions & Directives:"]
        for idx, item in enumerate(active_items, 1):
            lines.append(f"{idx}. **{item['name']}**: {item['content']}")
        return "\n".join(lines)

    def apply_to_prompt(self, base_system_prompt: str) -> str:
        """
        Appends all active extra instructions to the base system prompt.
        """
        extra_text = self.build_extra_prompt_text()
        if not extra_text:
            return base_system_prompt or ""

        if not base_system_prompt or not base_system_prompt.strip():
            return "You are a helpful and intelligent AI assistant." + extra_text

        return base_system_prompt.strip() + extra_text


# Global Singleton Helper
_system_prompt_extra_service: Optional[SystemPromptExtraService] = None

def get_system_prompt_extra_service() -> SystemPromptExtraService:
    global _system_prompt_extra_service
    if _system_prompt_extra_service is None:
        _system_prompt_extra_service = SystemPromptExtraService()
    return _system_prompt_extra_service
