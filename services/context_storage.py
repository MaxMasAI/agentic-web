"""
services/context_storage.py - Long & Short-Term SQLite Context & Memory Storage
Manages continuous conversation contexts, auto-summarization/titling, text file exports,
and multiple thread switching.
"""

import os
import sqlite3
import time
import json
import re
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite")
TXT_EXPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "chats")
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "settings.json")


def is_context_enabled() -> bool:
    """Checks Config -> Settings -> Use context setting."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return bool(data.get("use_context", True))
        except Exception:
            pass
    return True


def set_context_enabled(enabled: bool):
    """Sets Config -> Settings -> Use context setting."""
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass
    data["use_context"] = bool(enabled)
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class ContextDatabase:
    """Manages SQLite storage for chat contexts and multi-turn message history."""
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        if self.db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contexts (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT,
                    model_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    model_tag TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (context_id) REFERENCES contexts(id) ON DELETE CASCADE
                )
            """)
            conn.commit()

    def create_context(self, context_id: str, title: str = "New Conversation", model_id: str = "") -> str:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO contexts (id, title, summary, model_id, created_at, updated_at) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))",
                (context_id, title, "", model_id)
            )
            conn.commit()
        self._export_to_txt(context_id)
        return context_id

    def list_contexts(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, summary, model_id, created_at, updated_at FROM contexts ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_context(self, context_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, summary, model_id, created_at, updated_at FROM contexts WHERE id = ?", (context_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_title(self, context_id: str, title: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE contexts SET title = ?, updated_at = datetime('now') WHERE id = ?", (title, context_id))
            conn.commit()
        self._export_to_txt(context_id)

    def delete_context(self, context_id: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE context_id = ?", (context_id,))
            cursor.execute("DELETE FROM contexts WHERE id = ?", (context_id,))
            conn.commit()

    def clear_all_history(self):
        """Clears all conversation memory and contexts (File -> Clear history...)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages")
            cursor.execute("DELETE FROM contexts")
            conn.commit()

        # Clean txt files
        if os.path.exists(TXT_EXPORT_DIR):
            for fname in os.listdir(TXT_EXPORT_DIR):
                if fname.endswith(".txt"):
                    try:
                        os.remove(os.path.join(TXT_EXPORT_DIR, fname))
                    except Exception:
                        pass

    def add_message(self, context_id: str, role: str, content: str, model_tag: str = "") -> int:
        # If context doesn't exist, create it
        if not self.get_context(context_id):
            initial_title = self.generate_title_from_text(content) if role == "user" else "New Conversation"
            self.create_context(context_id, title=initial_title, model_id=model_tag)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (context_id, role, content, model_tag, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (context_id, role, content, model_tag)
            )
            cursor.execute("UPDATE contexts SET updated_at = datetime('now') WHERE id = ?", (context_id,))
            msg_id = cursor.lastrowid
            conn.commit()

        # Check if we should update default title on first user message
        msgs = self.get_messages(context_id)
        if len(msgs) == 1 and role == "user":
            ctx = self.get_context(context_id)
            if ctx and (ctx["title"] == "New Conversation" or not ctx["title"]):
                new_title = self.generate_title_from_text(content)
                self.update_title(context_id, new_title)

        self._export_to_txt(context_id)
        return msg_id

    def get_messages(self, context_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, context_id, role, content, model_tag, created_at FROM messages WHERE context_id = ? ORDER BY id ASC", (context_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def generate_title_from_text(self, text: str) -> str:
        """Generates a concise ChatGPT-style thread title from the initial user prompt."""
        cleaned = re.sub(r"[#*_`\n\r]+", " ", text).strip()
        words = cleaned.split()
        if not words:
            return "New Conversation"

        # Truncate to first 5-7 meaningful words
        title = " ".join(words[:6])
        if len(title) > 40:
            title = title[:37] + "..."
        return title.capitalize()

    def _export_to_txt(self, context_id: str):
        """Saves a clean, human-readable .txt copy of the conversation."""
        if self.db_path == ":memory:":
            return
        os.makedirs(TXT_EXPORT_DIR, exist_ok=True)
        ctx = self.get_context(context_id)
        if not ctx:
            return

        title_safe = re.sub(r'[\/:*?"<>|]', '_', ctx["title"]).strip() or "conversation"
        file_path = os.path.join(TXT_EXPORT_DIR, f"{context_id[:8]}_{title_safe}.txt")

        messages = self.get_messages(context_id)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"=====================================================\n")
                f.write(f"Thread Title: {ctx['title']}\n")
                f.write(f"Context ID  : {context_id}\n")
                f.write(f"Created     : {ctx.get('created_at', '')}\n")
                f.write(f"Updated     : {ctx.get('updated_at', '')}\n")
                f.write(f"=====================================================\n\n")
                for m in messages:
                    role_name = "USER" if m["role"] == "user" else f"ASSISTANT ({m.get('model_tag', 'AI')})"
                    f.write(f"[{role_name}] ({m.get('created_at', '')}):\n")
                    f.write(f"{m['content']}\n\n")
                    f.write("-" * 45 + "\n\n")
        except Exception:
            pass


# Global Context Database Instance
_db_instance: Optional[ContextDatabase] = None

def get_context_db() -> ContextDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = ContextDatabase()
    return _db_instance
