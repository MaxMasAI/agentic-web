"""
chat_session_manager.py - Persistent Single Chat ID & Session Tracker.

Ensures all AI agents (Gemini, DeepSeek, ChatGPT, Claude, Perplexity, etc.)
always operate in a single dedicated persistent conversation thread named:
"Collaborative AI review framework assignment".

Captures the exact conversation URL / chat ID and automatically reopens and
reuses the same chat thread across all pipeline runs.
"""

import os
import json
import time
import re

SESSIONS_FILE = os.path.join("json", "chat_sessions.json")
UNIFIED_THREAD_TITLE = "Collaborative AI review framework assignment"

def load_chat_sessions() -> dict:
    """Loads the persisted chat session IDs for all agents."""
    if not os.path.exists(SESSIONS_FILE):
        return {
            "thread_title": UNIFIED_THREAD_TITLE,
            "sessions": {}
        }
    try:
        with open(SESSIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return {"thread_title": UNIFIED_THREAD_TITLE, "sessions": {}}
            data.setdefault("thread_title", UNIFIED_THREAD_TITLE)
            data.setdefault("sessions", {})
            return data
    except Exception:
        return {"thread_title": UNIFIED_THREAD_TITLE, "sessions": {}}


def save_agent_chat_url(agent_id: str, current_url: str):
    """
    Saves or updates the specific conversation URL / Chat ID for an agent.
    Filters out generic root URLs so only actual conversation IDs are stored.
    """
    if not current_url or not isinstance(current_url, str):
        return

    # Check if URL contains actual conversation identifiers
    has_chat_id = any(p in current_url for p in [
        "/c/", "/chat/", "/app/", "/s/", "/search/", "?model=", "/thread/"
    ])

    if not has_chat_id and current_url.endswith((".com", ".ai", ".com/", ".ai/")):
        # Generic homepage, skip until actual conversation ID is generated
        return

    data = load_chat_sessions()
    sessions = data.setdefault("sessions", {})

    old_url = sessions.get(agent_id, {}).get("chat_url", "")
    if old_url == current_url:
        return

    sessions[agent_id] = {
        "agent_id": agent_id,
        "chat_url": current_url,
        "thread_title": UNIFIED_THREAD_TITLE,
        "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        os.makedirs("json", exist_ok=True)
        with open(SESSIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\033[92m[Chat Tracker] Persisted unified chat ID for {agent_id.upper()} -> {current_url}\033[0m")
    except Exception:
        pass


def get_agent_chat_url(agent_id: str, default_url: str) -> str:
    """
    Returns the saved single chat ID URL for the agent if available;
    otherwise returns the default initial URL.
    """
    data = load_chat_sessions()
    saved = data.get("sessions", {}).get(agent_id, {}).get("chat_url", "")
    if saved and saved.startswith("http"):
        return saved
    return default_url


def get_thread_prefix_header() -> str:
    """Returns the unified conversation context header."""
    return f"[PROJECT THREAD: {UNIFIED_THREAD_TITLE}]\n"
