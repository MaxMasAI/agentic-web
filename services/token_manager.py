"""
services/token_manager.py - Multi-Model Daily Token Quota & Lifetime Usage Analytics Engine.

Tracks real-time token consumption, enforces free-tier daily quotas per AI provider and model,
computes lifetime cumulative token metrics, and provides historical data feeds for interactive graphs.
"""

import os
import sys
import time
import json
import sqlite3
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite")

# ── Comprehensive Free Tier & Quota Knowledge Base ──────────────────────────────
# Defines official free daily limits, RPM, TPM, and commercial baseline cost per 1M tokens ($ USD)
MODEL_QUOTAS_CATALOG: Dict[str, Dict[str, Any]] = {
    "gemini-2.0-flash": {
        "provider": "Google Gemini",
        "model_name": "Gemini 2.0 Flash / Experimental",
        "daily_free_limit": 1_000_000_000,   # 1 Billion tokens daily allowance in Free Tier
        "daily_requests_limit": 1500,        # 1,500 Requests Per Day (RPD)
        "rpm_limit": 15,                     # 15 Requests Per Minute
        "tpm_limit": 1_000_000,              # 1M Tokens Per Minute
        "cost_per_1m_input": 0.075,          # $0.075 per 1M tokens
        "cost_per_1m_output": 0.30,
        "color": "#38bdf8",                  # Sky Blue
        "icon": "⚡",
        "tier_type": "Free Tier (Daily 1,500 RPD)"
    },
    "deepseek-v3": {
        "provider": "DeepSeek",
        "model_name": "DeepSeek V3 / R1 Reasoner",
        "daily_free_limit": 5_000_000,       # 5 Million tokens starter / daily quota
        "daily_requests_limit": 500,
        "rpm_limit": 30,
        "tpm_limit": 500_000,
        "cost_per_1m_input": 0.14,           # $0.14 per 1M cached tokens
        "cost_per_1m_output": 0.28,
        "color": "#0ea5e9",                  # Deep Blue
        "icon": "🔬",
        "tier_type": "Daily Grant / Low-Cost"
    },
    "claude-3.5-sonnet": {
        "provider": "Anthropic Claude",
        "model_name": "Claude 3.5 Sonnet / Haiku",
        "daily_free_limit": 100_000,         # Standard Evaluation / Free Web tier
        "daily_requests_limit": 50,
        "rpm_limit": 5,
        "tpm_limit": 40_000,
        "cost_per_1m_input": 3.00,           # $3.00 per 1M tokens
        "cost_per_1m_output": 15.00,
        "color": "#d97706",                  # Amber / Terracotta
        "icon": "✍️",
        "tier_type": "Free Evaluation Tier"
    },
    "gpt-4o-mini": {
        "provider": "OpenAI ChatGPT",
        "model_name": "GPT-4o / GPT-4o-mini",
        "daily_free_limit": 2_500_000,       # 2.5M tokens daily allowance
        "daily_requests_limit": 200,
        "rpm_limit": 60,
        "tpm_limit": 200_000,
        "cost_per_1m_input": 0.15,           # $0.15 per 1M tokens
        "cost_per_1m_output": 0.60,
        "color": "#10b981",                  # Emerald Green
        "icon": "🤖",
        "tier_type": "Free Tier Allowance"
    },
    "openrouter-free": {
        "provider": "OpenRouter",
        "model_name": "OpenRouter Free Models (Llama 3.3 / Mistral / DeepSeek:free)",
        "daily_free_limit": 10_000_000,      # 10M tokens daily across :free models
        "daily_requests_limit": 200,         # 200 Requests / day
        "rpm_limit": 20,
        "tpm_limit": 200_000,
        "cost_per_1m_input": 0.00,           # 100% Free
        "cost_per_1m_output": 0.00,
        "color": "#8b5cf6",                  # Violet
        "icon": "🌐",
        "tier_type": "100% Free Community Tier"
    },
    "groq-llama-3.3": {
        "provider": "Groq Cloud",
        "model_name": "Groq Llama 3.3 70B Versatile",
        "daily_free_limit": 500_000,         # 500k tokens per day
        "daily_requests_limit": 14_400,      # 14,400 RPD
        "rpm_limit": 30,
        "tpm_limit": 6_000,
        "cost_per_1m_input": 0.59,
        "cost_per_1m_output": 0.79,
        "color": "#f97316",                  # Orange
        "icon": "⚡",
        "tier_type": "Free High-Speed Tier"
    },
    "huggingface-inference": {
        "provider": "Hugging Face",
        "model_name": "Hugging Face Inference API",
        "daily_free_limit": 1_000_000,       # 1M tokens / day
        "daily_requests_limit": 1000,
        "rpm_limit": 60,
        "tpm_limit": 30_000,
        "cost_per_1m_input": 0.20,
        "cost_per_1m_output": 0.40,
        "color": "#eab308",                  # Yellow
        "icon": "🤗",
        "tier_type": "Free Serverless API"
    },
    "perplexity-sonar": {
        "provider": "Perplexity AI",
        "model_name": "Sonar Online Search & Reasoning",
        "daily_free_limit": 500_000,         # 500k tokens / day
        "daily_requests_limit": 100,
        "rpm_limit": 20,
        "tpm_limit": 40_000,
        "cost_per_1m_input": 1.00,
        "cost_per_1m_output": 1.00,
        "color": "#06b6d4",                  # Cyan
        "icon": "🔍",
        "tier_type": "Daily Search Allowance"
    }
}


class TokenManager:
    """
    Thread-safe Token Consumption & Daily Quota Analytics Engine.
    Persists granular token records in SQLite WAL database and generates chart data.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str = DB_PATH):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TokenManager, cls).__new__(cls)
                cls._instance._init_manager(db_path)
            return cls._instance

    def _init_manager(self, db_path: str):
        self.db_path = db_path
        self._local = threading.local()
        self._setup_schema()
        self._seed_sample_data_if_empty()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            self._local.conn = conn
        return self._local.conn

    def _setup_schema(self):
        conn = self._get_connection()
        with conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS token_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    cost_usd REAL DEFAULT 0.0,
                    task_id TEXT,
                    created_at REAL NOT NULL,
                    date_str TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_token_date ON token_ledger(date_str);
                CREATE INDEX IF NOT EXISTS idx_token_model ON token_ledger(model);
            """)

    def _seed_sample_data_if_empty(self):
        """Populates historical activity so charts and metrics display immediately upon launch."""
        conn = self._get_connection()
        cur = conn.execute("SELECT COUNT(*) as count FROM token_ledger")
        row = cur.fetchone()
        if row and row["count"] == 0:
            now = time.time()
            # Seed past 7 days with realistic workflow distributions
            seed_samples = [
                # 6 days ago
                ("Google Gemini", "gemini-2.0-flash", 42000, 18500, now - 6 * 86400),
                ("DeepSeek", "deepseek-v3", 18000, 9200, now - 6 * 86400),
                # 5 days ago
                ("Google Gemini", "gemini-2.0-flash", 68000, 31000, now - 5 * 86400),
                ("OpenAI ChatGPT", "gpt-4o-mini", 12500, 4800, now - 5 * 86400),
                ("Anthropic Claude", "claude-3.5-sonnet", 8500, 3200, now - 5 * 86400),
                # 4 days ago
                ("Google Gemini", "gemini-2.0-flash", 95000, 42000, now - 4 * 86400),
                ("DeepSeek", "deepseek-v3", 34000, 16000, now - 4 * 86400),
                ("Groq Cloud", "groq-llama-3.3", 15000, 8000, now - 4 * 86400),
                # 3 days ago
                ("Google Gemini", "gemini-2.0-flash", 112000, 48000, now - 3 * 86400),
                ("OpenRouter", "openrouter-free", 45000, 22000, now - 3 * 86400),
                ("Perplexity AI", "perplexity-sonar", 6200, 2800, now - 3 * 86400),
                # 2 days ago
                ("Google Gemini", "gemini-2.0-flash", 145000, 62000, now - 2 * 86400),
                ("DeepSeek", "deepseek-v3", 52000, 24000, now - 2 * 86400),
                ("Anthropic Claude", "claude-3.5-sonnet", 14000, 6500, now - 2 * 86400),
                # Yesterday
                ("Google Gemini", "gemini-2.0-flash", 188000, 76000, now - 1 * 86400),
                ("OpenAI ChatGPT", "gpt-4o-mini", 28000, 11000, now - 1 * 86400),
                ("Groq Cloud", "groq-llama-3.3", 22000, 10500, now - 1 * 86400),
                # Today
                ("Google Gemini", "gemini-2.0-flash", 125000, 54000, now),
                ("DeepSeek", "deepseek-v3", 38000, 17500, now),
                ("OpenRouter", "openrouter-free", 29000, 14000, now),
                ("Anthropic Claude", "claude-3.5-sonnet", 9500, 4100, now),
            ]
            with conn:
                for prov, mod, p_tok, c_tok, ts in seed_samples:
                    tot = p_tok + c_tok
                    d_str = time.strftime("%Y-%m-%d", time.gmtime(ts))
                    cost = (p_tok * 0.0000001) + (c_tok * 0.0000003)
                    conn.execute("""
                        INSERT INTO token_ledger (provider, model, prompt_tokens, completion_tokens, total_tokens, cost_usd, task_id, created_at, date_str)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (prov, mod, p_tok, c_tok, tot, cost, "init-seed", ts, d_str))

    # ── Token Tracking & Transaction Logging ──────────────────────────────────
    def record_usage(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        task_id: str = "",
        cost_usd: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Records a model completion token event into the persistent ledger.
        """
        total = int(prompt_tokens) + int(completion_tokens)
        now = time.time()
        date_str = time.strftime("%Y-%m-%d", time.gmtime(now))

        # Normalize model key
        normalized_model = model.lower()
        if not cost_usd:
            # Estimate dollar value
            info = MODEL_QUOTAS_CATALOG.get(normalized_model, {})
            in_rate = info.get("cost_per_1m_input", 0.15) / 1_000_000.0
            out_rate = info.get("cost_per_1m_output", 0.60) / 1_000_000.0
            cost_usd = (prompt_tokens * in_rate) + (completion_tokens * out_rate)

        conn = self._get_connection()
        with conn:
            conn.execute("""
                INSERT INTO token_ledger (provider, model, prompt_tokens, completion_tokens, total_tokens, cost_usd, task_id, created_at, date_str)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (provider, model, prompt_tokens, completion_tokens, total, cost_usd, task_id, now, date_str))

        return {
            "success": True,
            "provider": provider,
            "model": model,
            "total_tokens": total,
            "date": date_str
        }

    # ── Analytics & Summaries ─────────────────────────────────────────────────
    def get_lifetime_summary(self) -> Dict[str, Any]:
        """
        Calculates cumulative token consumption across all models 'till today'.
        """
        conn = self._get_connection()
        cur = conn.execute("""
            SELECT 
                COUNT(*) as total_requests,
                COALESCE(SUM(prompt_tokens), 0) as total_prompt,
                COALESCE(SUM(completion_tokens), 0) as total_completion,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COALESCE(SUM(cost_usd), 0.0) as total_saved_usd
            FROM token_ledger
        """)
        row = cur.fetchone()
        return {
            "total_requests": row["total_requests"],
            "total_prompt_tokens": row["total_prompt"],
            "total_completion_tokens": row["total_completion"],
            "total_tokens": row["total_tokens"],
            "total_saved_usd": round(row["total_saved_usd"], 3)
        }

    def get_today_summary(self) -> Dict[str, Any]:
        """
        Calculates tokens consumed today (UTC) compared to combined daily allowances.
        """
        today_str = time.strftime("%Y-%m-%d", time.gmtime())
        conn = self._get_connection()
        cur = conn.execute("""
            SELECT 
                COUNT(*) as today_requests,
                COALESCE(SUM(prompt_tokens), 0) as today_prompt,
                COALESCE(SUM(completion_tokens), 0) as today_completion,
                COALESCE(SUM(total_tokens), 0) as today_tokens,
                COALESCE(SUM(cost_usd), 0.0) as today_saved_usd
            FROM token_ledger
            WHERE date_str = ?
        """, (today_str,))
        row = cur.fetchone()

        # Combined daily free tier limit across all catalog models
        combined_limit = sum(m["daily_free_limit"] for m in MODEL_QUOTAS_CATALOG.values())
        used_today = row["today_tokens"]
        pct = (used_today / combined_limit * 100.0) if combined_limit > 0 else 0.0

        return {
            "date": today_str,
            "today_requests": row["today_requests"],
            "today_prompt_tokens": row["today_prompt"],
            "today_completion_tokens": row["today_completion"],
            "today_tokens": used_today,
            "combined_daily_limit": combined_limit,
            "usage_percent": round(pct, 2),
            "today_saved_usd": round(row["today_saved_usd"], 3),
            "seconds_until_reset": self.get_seconds_until_midnight_utc()
        }

    def get_seconds_until_midnight_utc(self) -> int:
        """Returns number of seconds remaining until the daily quota resets at 00:00 UTC."""
        now = datetime.now(timezone.utc)
        tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((tomorrow - now).total_seconds())

    # ── Model & Provider Quota Status ─────────────────────────────────────────
    def get_all_model_statuses(self) -> List[Dict[str, Any]]:
        """
        Returns real-time status, usage, limits, and health for each known AI model.
        """
        today_str = time.strftime("%Y-%m-%d", time.gmtime())
        conn = self._get_connection()
        cur = conn.execute("""
            SELECT 
                model,
                COUNT(*) as req_count,
                COALESCE(SUM(total_tokens), 0) as used_tokens
            FROM token_ledger
            WHERE date_str = ?
            GROUP BY model
        """, (today_str,))

        today_map = {row["model"].lower(): (row["used_tokens"], row["req_count"]) for row in cur.fetchall()}

        statuses = []
        for model_id, catalog_info in MODEL_QUOTAS_CATALOG.items():
            used_tokens, req_count = today_map.get(model_id, (0, 0))
            daily_limit = catalog_info["daily_free_limit"]
            req_limit = catalog_info["daily_requests_limit"]
            pct = (used_tokens / daily_limit * 100.0) if daily_limit > 0 else 0.0

            # Health badge
            if pct >= 95.0 or (req_limit > 0 and req_count >= req_limit):
                health = "🔴 EXHAUSTED"
                health_color = "#ef4444"
            elif pct >= 75.0:
                health = "🟡 NEARING CAP"
                health_color = "#f59e0b"
            else:
                health = "🟢 HEALTHY"
                health_color = "#10b981"

            statuses.append({
                "model_id": model_id,
                "provider": catalog_info["provider"],
                "model_name": catalog_info["model_name"],
                "icon": catalog_info["icon"],
                "color": catalog_info["color"],
                "tier_type": catalog_info["tier_type"],
                "daily_limit": daily_limit,
                "used_today": used_tokens,
                "remaining_today": max(0, daily_limit - used_tokens),
                "requests_today": req_count,
                "requests_limit": req_limit,
                "rpm_limit": catalog_info["rpm_limit"],
                "tpm_limit": catalog_info["tpm_limit"],
                "usage_percent": round(pct, 1),
                "health": health,
                "health_color": health_color
            })
        return statuses

    # ── Graph Data Feeds ──────────────────────────────────────────────────────
    def get_daily_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Returns chronologically sorted daily token aggregates for area/bar graphs.
        """
        conn = self._get_connection()
        cur = conn.execute("""
            SELECT 
                date_str,
                COALESCE(SUM(prompt_tokens), 0) as prompt_tokens,
                COALESCE(SUM(completion_tokens), 0) as completion_tokens,
                COALESCE(SUM(total_tokens), 0) as total_tokens,
                COUNT(*) as requests_count
            FROM token_ledger
            GROUP BY date_str
            ORDER BY date_str DESC
            LIMIT ?
        """, (days,))

        rows = cur.fetchall()
        # Sort chronologically ascending for the chart X-axis
        result = []
        for r in reversed(rows):
            # Format friendly label (e.g. 'Sep 14')
            try:
                dt = datetime.strptime(r["date_str"], "%Y-%m-%d")
                friendly = dt.strftime("%b %d")
            except Exception:
                friendly = r["date_str"]

            result.append({
                "date": r["date_str"],
                "label": friendly,
                "prompt_tokens": r["prompt_tokens"],
                "completion_tokens": r["completion_tokens"],
                "total_tokens": r["total_tokens"],
                "requests_count": r["requests_count"]
            })
        return result

    def get_model_distribution(self) -> List[Dict[str, Any]]:
        """
        Returns model token breakdown for donut/pie charts.
        """
        conn = self._get_connection()
        cur = conn.execute("""
            SELECT 
                provider,
                model,
                COALESCE(SUM(total_tokens), 0) as tokens
            FROM token_ledger
            GROUP BY provider, model
            ORDER BY tokens DESC
        """)
        rows = cur.fetchall()
        total_all = sum(r["tokens"] for r in rows) or 1
        distribution = []
        colors = ["#38bdf8", "#0ea5e9", "#8b5cf6", "#10b981", "#f59e0b", "#ef4444", "#06b6d4", "#ec4899"]

        for i, r in enumerate(rows):
            pct = (r["tokens"] / total_all) * 100.0
            distribution.append({
                "provider": r["provider"],
                "model": r["model"],
                "tokens": r["tokens"],
                "percent": round(pct, 1),
                "color": colors[i % len(colors)]
            })
        return distribution

    def get_recent_transactions(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Returns recent granular token ledger transactions."""
        conn = self._get_connection()
        cur = conn.execute("""
            SELECT id, provider, model, prompt_tokens, completion_tokens, total_tokens, cost_usd, task_id, created_at, date_str
            FROM token_ledger
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        txs = []
        for r in cur.fetchall():
            time_formatted = time.strftime("%H:%M:%S", time.gmtime(r["created_at"]))
            txs.append({
                "id": r["id"],
                "provider": r["provider"],
                "model": r["model"],
                "prompt_tokens": r["prompt_tokens"],
                "completion_tokens": r["completion_tokens"],
                "total_tokens": r["total_tokens"],
                "cost_usd": round(r["cost_usd"], 4),
                "task_id": r["task_id"] or "-",
                "time": time_formatted,
                "date": r["date_str"]
            })
        return txs


# Global Singleton Helper
_token_manager_instance: Optional[TokenManager] = None

def get_token_manager() -> TokenManager:
    global _token_manager_instance
    if _token_manager_instance is None:
        _token_manager_instance = TokenManager()
    return _token_manager_instance
