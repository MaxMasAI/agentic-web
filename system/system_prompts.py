"""
system/system_prompts.py - System Prompts Catalog & Extra Directives Manager.
Provides access to curated system prompts for Claude, Cursor, OpenAI, Devin, Perplexity, Gemini,
and manages automatic appending of system prompt extras.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional

PROMPTS_CATALOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "system_prompts_catalog.json"
)
EXTRAS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "system_prompt_extras.json"
)

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


class SystemPromptsCatalog:
    """
    Manages loading, searching, task-based matching, and dynamic injection
    of specialized system prompts into AI model execution pipelines.
    """
    def __init__(self, catalog_path: str = PROMPTS_CATALOG_FILE):
        self.catalog_path = catalog_path
        self.prompts: Dict[str, Dict[str, Any]] = {}
        self.load_catalog()

    def load_catalog(self):
        if os.path.exists(self.catalog_path):
            try:
                with open(self.catalog_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    prompt_list = data.get("prompts", [])
                    self.prompts = {p["id"]: p for p in prompt_list if "id" in p}
                    return
            except Exception:
                pass
        self.prompts = {}

    def get_prompt(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        return self.prompts.get(prompt_id)

    def get_prompt_text(self, prompt_id: str, default: str = "") -> str:
        p = self.get_prompt(prompt_id)
        return p.get("prompt", default) if p else default

    def list_all(self) -> List[Dict[str, Any]]:
        return list(self.prompts.values())

    def list_by_category(self, category: str) -> List[Dict[str, Any]]:
        return [p for p in self.prompts.values() if p.get("category") == category]

    def match_best_prompt_for_task(self, task_description: str) -> Dict[str, Any]:
        """Analyzes task description and selects optimal specialized system prompt."""
        task_lower = task_description.lower()

        if any(w in task_lower for w in ["ui", "ux", "css", "theme", "layout", "design", "frontend", "html", "style", "widget", "dialog", "pyside6", "react"]):
            return self.prompts.get("v0_bolt_ui_architect") or self._default_prompt()

        if any(w in task_lower for w in ["fix", "debug", "refactor", "bug", "traceback", "exception", "patch", "error"]):
            return self.prompts.get("cursor_fullstack_engineer") or self._default_prompt()

        if any(w in task_lower for w in ["build", "create app", "new project", "generate codebase", "scaffold"]):
            return self.prompts.get("devin_autonomous_software_engineer") or self._default_prompt()

        if any(w in task_lower for w in ["research", "paper", "investigate", "benchmark", "analysis", "compare", "latest news"]):
            return self.prompts.get("perplexity_deep_researcher") or self._default_prompt()

        if any(w in task_lower for w in ["reason", "architecture", "math", "proof", "logic", "algorithm"]):
            return self.prompts.get("claude_sonnet_architect") or self._default_prompt()

        return self.prompts.get("openai_standard_assistant") or self._default_prompt()

    def _default_prompt(self) -> Dict[str, Any]:
        return {
            "id": "gemini_orchestrator",
            "name": "Google Gemini Orchestrator",
            "prompt": "You are Google Gemini, the Master Orchestrator in an advanced multi-agent workstation.",
            "category": "General"
        }


class SystemPromptExtraService:
    """Manages custom system prompt extra directives and appends active extras."""
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

    def get_extra_prompt_text(self) -> str:
        active = [e for e in self.extras.values() if e.get("enabled", True)]
        active.sort(key=lambda x: x.get("priority", 99))
        if not active:
            return ""
        lines = ["\n\n--- EXTENDED SYSTEM DIRECTIVES ---"]
        for e in active:
            lines.append(f"• {e['name']}: {e['content']}")
        lines.append("----------------------------------")
        return "\n".join(lines)


_sys_catalog: Optional[SystemPromptsCatalog] = None
_sys_extra: Optional[SystemPromptExtraService] = None

def get_system_prompts_catalog() -> SystemPromptsCatalog:
    global _sys_catalog
    if _sys_catalog is None:
        _sys_catalog = SystemPromptsCatalog()
    return _sys_catalog

def get_system_prompt_extra_service() -> SystemPromptExtraService:
    global _sys_extra
    if _sys_extra is None:
        _sys_extra = SystemPromptExtraService()
    return _sys_extra
