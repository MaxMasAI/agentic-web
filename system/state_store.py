"""
system/state_store.py - ACID-Compliant SQLite WAL State & Concurrency Manager.

Replaces volatile flat JSON files with a persistent, thread-safe, process-safe
SQLite database running in Write-Ahead Logging (WAL) mode for atomic concurrency,
PID registries, and task lifecycle tracking.
"""

import os
import sys
import time
import json
import sqlite3
import threading
from typing import Dict, List, Any, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite")


class StateStore:
    """
    Thread-safe ACID SQLite State Manager using Write-Ahead Logging (WAL).
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = DB_PATH):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StateStore, cls).__new__(cls)
                cls._instance._init_db(db_path)
            return cls._instance

    def _init_db(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._setup_schema()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for high concurrency
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            self._local.conn = conn
        return self._local.conn

    def _setup_schema(self):
        conn = self._get_connection()
        with conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS pid_registry (
                    pid INTEGER PRIMARY KEY,
                    ppid INTEGER,
                    process_name TEXT,
                    port INTEGER,
                    created_at REAL,
                    status TEXT DEFAULT 'active'
                );

                CREATE TABLE IF NOT EXISTS task_state (
                    task_id TEXT PRIMARY KEY,
                    title TEXT,
                    status TEXT DEFAULT 'PENDING',
                    leader_plan TEXT,
                    result TEXT,
                    created_at REAL,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS agent_status (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT,
                    state TEXT DEFAULT 'FREE',
                    current_action TEXT,
                    updated_at REAL
                );

                CREATE TABLE IF NOT EXISTS command_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT,
                    allowed INTEGER,
                    sandbox_type TEXT,
                    timestamp REAL
                );

                CREATE TABLE IF NOT EXISTS kv_state (
                    key TEXT PRIMARY KEY,
                    value_json TEXT,
                    updated_at REAL
                );
            """)

    # ── PID Registry Methods ──────────────────────────────────────────────────
    def register_pid(self, pid: int, process_name: str = "chrome.exe", port: Optional[int] = 9222):
        if not pid or pid <= 0:
            return
        conn = self._get_connection()
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO pid_registry (pid, process_name, port, created_at, status)
                VALUES (?, ?, ?, ?, 'active')
            """, (pid, process_name, port, time.time()))

    def get_all_active_pids(self) -> List[int]:
        conn = self._get_connection()
        cur = conn.execute("SELECT pid FROM pid_registry WHERE status = 'active'")
        return [row["pid"] for row in cur.fetchall()]

    def mark_pid_terminated(self, pid: int):
        conn = self._get_connection()
        with conn:
            conn.execute("UPDATE pid_registry SET status = 'terminated' WHERE pid = ?", (pid,))

    def clear_all_pids(self):
        conn = self._get_connection()
        with conn:
            conn.execute("DELETE FROM pid_registry")

    def close(self):
        """Close thread-local database connection to release file handles."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None

    @classmethod
    def reset_instance(cls):
        with cls._lock:
            if cls._instance:
                try:
                    cls._instance.close()
                except Exception:
                    pass
                cls._instance = None

    # ── Agent State Methods ───────────────────────────────────────────────────
    def set_agent_state(self, agent_id: str, state: str, action: str = "", name: str = ""):
        conn = self._get_connection()
        with conn:
            conn.execute("""
                INSERT INTO agent_status (agent_id, name, state, current_action, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    state = excluded.state,
                    current_action = excluded.current_action,
                    updated_at = excluded.updated_at
            """, (agent_id, name or agent_id.title(), state, action, time.time()))

    def get_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.execute("SELECT * FROM agent_status WHERE agent_id = ?", (agent_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    # ── Task State Lifecycle Methods ──────────────────────────────────────────
    def set_task_state(self, task_id: str, title: str, status: str = "PENDING", leader_plan: str = "", result: str = ""):
        conn = self._get_connection()
        now = time.time()
        with conn:
            conn.execute("""
                INSERT INTO task_state (task_id, title, status, leader_plan, result, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(task_id) DO UPDATE SET
                    title = excluded.title,
                    status = excluded.status,
                    leader_plan = excluded.leader_plan,
                    result = excluded.result,
                    updated_at = excluded.updated_at
            """, (task_id, title, status, leader_plan, result, now, now))

    def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cur = conn.execute("SELECT * FROM task_state WHERE task_id = ?", (task_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    # ── Command Audit Logging ─────────────────────────────────────────────────
    def log_command_execution(self, command: str, allowed: bool, sandbox_type: str = "subprocess"):
        conn = self._get_connection()
        with conn:
            conn.execute("""
                INSERT INTO command_audit_log (command, allowed, sandbox_type, timestamp)
                VALUES (?, ?, ?, ?)
            """, (command, 1 if allowed else 0, sandbox_type, time.time()))

    # ── Key-Value State ───────────────────────────────────────────────────────
    def set_kv(self, key: str, value: Any):
        conn = self._get_connection()
        with conn:
            conn.execute("""
                INSERT OR REPLACE INTO kv_state (key, value_json, updated_at)
                VALUES (?, ?, ?)
            """, (key, json.dumps(value), time.time()))

    def get_kv(self, key: str, default: Any = None) -> Any:
        conn = self._get_connection()
        cur = conn.execute("SELECT value_json FROM kv_state WHERE key = ?", (key,))
        row = cur.fetchone()
        if row:
            try:
                return json.loads(row["value_json"])
            except Exception:
                return row["value_json"]
        return default


# Global State Store Helper
def get_state_store() -> StateStore:
    return StateStore()
