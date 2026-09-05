"""
squad_learner.py - Pattern Detection & Autonomous Reusable Squad Learning Engine
Analyzes completed tasks in tasks/ to detect repeated mission patterns and automatically
synthesizes specialized, reusable Agent Squads for future one-click deployment.
"""

import os
import json
import re
import glob
import time
from collections import Counter

TASKS_DIR = "tasks"
SUBAGENTS_FILE = os.path.join("json", "subagents.json")

# Core domain keyword categories for pattern recognition
DOMAIN_PATTERNS = {
    "web_ecommerce": {
        "keywords": ["ecommerce", "e-commerce", "shop", "cart", "store", "flipkart", "amazon", "product", "checkout"],
        "name": "⚡ Auto-Learned: E-Commerce & Web Prototyping Squad",
        "desc": "Auto-created from repeated e-commerce & storefront web missions",
        "agents": ["gemini", "deepseek", "chatgpt", "dalle"]
    },
    "web_frontend": {
        "keywords": ["website", "landing page", "html", "css", "javascript", "frontend", "ui", "ux", "responsive", "portfolio"],
        "name": "🎨 Auto-Learned: Rapid UI/UX & Frontend Strike Team",
        "desc": "Auto-created from repeated web design, UI styling & frontend engineering tasks",
        "agents": ["gemini", "deepseek", "chatgpt", "dalle"]
    },
    "security_audit": {
        "keywords": ["security", "audit", "vulnerability", "auth", "token", "penetration", "safe", "zero-trust", "review"],
        "name": "🛡️ Auto-Learned: Zero-Trust Security & QA Audit Team",
        "desc": "Auto-created from repeated security, compliance & architectural critique missions",
        "agents": ["gemini", "claude", "deepseek", "perplexity"]
    },
    "data_compute": {
        "keywords": ["python", "data", "algorithm", "benchmark", "compute", "gpu", "latency", "scale", "performance", "math"],
        "name": "🏎️ Auto-Learned: High-Performance Compute & Algorithmic Squad",
        "desc": "Auto-created from repeated algorithmic, data processing & compute optimization tasks",
        "agents": ["gemini", "nvidia_ai", "deepseek", "perplexity"]
    },
    "growth_marketing": {
        "keywords": ["viral", "marketing", "social", "campaign", "tweet", "hashtag", "post", "audience", "brand", "growth"],
        "name": "📈 Auto-Learned: Viral Growth & Multi-Platform Marketing Hub",
        "desc": "Auto-created from repeated social media copywriting & viral marketing tasks",
        "agents": ["gemini", "chatgpt", "meta_ai", "dalle"]
    },
    "enterprise_docs": {
        "keywords": ["translate", "multilingual", "documentation", "enterprise", "excel", "sheet", "macro", "german", "french", "spanish"],
        "name": "🌐 Auto-Learned: Enterprise Localization & Workflow Team",
        "desc": "Auto-created from repeated enterprise documentation & translation workflows",
        "agents": ["gemini", "mistral", "copilot", "chatgpt"]
    }
}

def load_subagents() -> list:
    if os.path.exists(SUBAGENTS_FILE):
        try:
            with open(SUBAGENTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []

def save_subagents(subs: list):
    os.makedirs(os.path.dirname(SUBAGENTS_FILE), exist_ok=True)
    with open(SUBAGENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, indent=2)

def detect_and_create_repeated_pattern_squads(min_repetition_threshold: int = 2) -> list:
    """
    Scans all completed task reports, counts domain pattern frequencies,
    and automatically registers new reusable squads if a domain has >= threshold tasks.
    """
    task_files = glob.glob(os.path.join(TASKS_DIR, "task_*.txt"))
    if not task_files:
        return []

    # Read all task descriptions
    task_texts = []
    for tf in task_files:
        try:
            with open(tf, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                # Extract first line / Task line
                for line in content.splitlines()[:5]:
                    if line.startswith("Task:"):
                        task_texts.append(line[5:].strip().lower())
                        break
        except Exception:
            continue

    if not task_texts:
        return []

    # Count domain frequency
    domain_counts = Counter()
    domain_examples = {}
    for task_str in task_texts:
        for dom_key, dom_data in DOMAIN_PATTERNS.items():
            if any(kw in task_str for kw in dom_data["keywords"]):
                domain_counts[dom_key] += 1
                if dom_key not in domain_examples:
                    domain_examples[dom_key] = task_str

    existing_subs = load_subagents()
    existing_names = {s.get("name") for s in existing_subs}

    created_squads = []
    for dom_key, count in domain_counts.items():
        if count >= min_repetition_threshold:
            dom_data = DOMAIN_PATTERNS[dom_key]
            if dom_data["name"] not in existing_names:
                new_squad = {
                    "name": dom_data["name"],
                    "task": f"Autonomous execution for repeated {dom_key.replace('_', ' ')} tasks (e.g. {domain_examples.get(dom_key, 'general mission')})",
                    "desc": f"{dom_data['desc']} (Triggered by {count} similar missions)",
                    "agents": dom_data["agents"],
                    "auto_learned": True,
                    "repetition_count": count,
                    "created": time.strftime("%Y-%m-%d %H:%M")
                }
                existing_subs.append(new_squad)
                created_squads.append(new_squad)

    if created_squads:
        save_subagents(existing_subs)

    return created_squads
