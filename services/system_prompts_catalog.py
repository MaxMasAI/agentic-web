"""
services/system_prompts_catalog.py - Dynamic System Prompts Catalog & Task Router
Provides access to curated system prompts for Claude, Cursor, OpenAI, Devin, Perplexity, v0, Gemini, etc.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional

PROMPTS_CATALOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "system_prompts_catalog.json"
)


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
        """
        Analyzes task description and selects the optimal specialized system prompt.
        """
        task_lower = task_description.lower()

        # 1. UI / Frontend / Design
        if any(w in task_lower for w in ["ui", "ux", "css", "theme", "layout", "design", "frontend", "html", "style", "widget", "dialog", "pyside6", "react"]):
            return self.prompts.get("v0_bolt_ui_architect") or self._default_prompt()

        # 2. Bug fixing / Diagnostics / Testing / Regression
        if any(w in task_lower for w in ["bug", "fix", "issue", "error", "traceback", "crash", "reproduce", "test", "patch", "fails"]):
            return self.prompts.get("swe_bench_devin_bug_fixer") or self._default_prompt()

        # 3. Security / Audit / Vulnerability / Auth
        if any(w in task_lower for w in ["security", "audit", "vulnerability", "auth", "token", "sanitize", "leak", "penetration", "owasp"]):
            return self.prompts.get("cybersecurity_qa_auditor") or self._default_prompt()

        # 4. Research / Web search / Facts / Deep dive
        if any(w in task_lower for w in ["research", "search", "investigate", "sources", "summary", "analyze", "trends", "wikipedia", "facts"]):
            return self.prompts.get("perplexity_deep_research") or self._default_prompt()

        # 5. Multimodal / Vision / Live / Voice
        if any(w in task_lower for w in ["image", "screenshot", "video", "visual", "vision", "voice", "audio", "mic"]):
            return self.prompts.get("gemini_multimodal_live_agent") or self._default_prompt()

        # 6. Deep Reasoning / Math / Strategy / Planning
        if any(w in task_lower for w in ["plan", "strategy", "math", "proof", "logic", "algorithm", "architecture", "deconstruct", "complex"]):
            return self.prompts.get("openai_o_series_deep_reasoning") or self._default_prompt()

        # 7. IDE / Subprocess / Local files
        if any(w in task_lower for w in ["file", "directory", "folder", "ide", "command", "bash", "git", "install"]):
            return self.prompts.get("cursor_windsurf_agentic_ide") or self._default_prompt()

        # Default to Claude Senior Coding Architect
        return self.prompts.get("claude_coding_architect") or self._default_prompt()

    def _default_prompt(self) -> Dict[str, Any]:
        if self.prompts:
            return next(iter(self.prompts.values()))
        return {
            "id": "default",
            "name": "Default Assistant",
            "prompt": "You are a professional, intelligent, and accurate AI assistant."
        }


# Singleton Helper
_catalog_instance: Optional[SystemPromptsCatalog] = None

def get_system_prompts_catalog() -> SystemPromptsCatalog:
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = SystemPromptsCatalog()
    return _catalog_instance
