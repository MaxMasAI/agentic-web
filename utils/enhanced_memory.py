"""
enhanced_memory.py - Advanced Structured Neural Memory & Semantic Retrieval System
Provides categorized memory storage, relevance retrieval for multi-agent prompts,
importance scoring, deduplication, and lifecycle analytics.
"""

import os
import json
import time
import uuid
import re

MEMORY_FILE = os.path.join("json", "memory.json")

MEMORY_CATEGORIES = {
    "architecture": "🏗️ Architecture & Tech Stack",
    "design_ui":    "🎨 UI/UX & Design Guidelines",
    "security_qa":  "🛡️ Security, QA & Defensive Rules",
    "performance":  "🏎️ Performance & Optimization",
    "user_pref":    "📋 User Preferences & Directives",
    "general":      "🧠 General Learnings"
}

CATEGORY_KEYWORDS = {
    "architecture": ["next.js", "react", "backend", "api", "database", "postgres", "redis", "schema", "architecture", "microservice"],
    "design_ui":    ["css", "html", "glassmorphism", "color", "typography", "responsive", "ui", "ux", "layout", "animation", "palette"],
    "security_qa":  ["security", "audit", "auth", "token", "zero-trust", "sanitization", "xss", "csrf", "defensive", "validation", "qa"],
    "performance":  ["latency", "speed", "cache", "gpu", "compute", "optimization", "scale", "profiling", "fast", "benchmark"],
    "user_pref":    ["user directive", "user wants", "strictly", "preference", "must be", "format", "rule", "guideline"]
}

def load_memories() -> list:
    """Loads all structured memories, migrating flat string lists if needed."""
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            if not isinstance(raw_data, list):
                return []
            
            # Auto-migrate legacy flat string memories to structured objects
            structured = []
            for item in raw_data:
                if isinstance(item, str):
                    cat = infer_category(item)
                    structured.append({
                        "id": str(uuid.uuid4())[:8],
                        "category": cat,
                        "content": item.strip(),
                        "source_mission": "Legacy Migration",
                        "importance": 3,
                        "access_count": 1,
                        "pinned": False,
                        "created_at": time.strftime("%Y-%m-%d %H:%M")
                    })
                elif isinstance(item, dict) and "content" in item:
                    # Ensure all standard fields exist
                    item.setdefault("id", str(uuid.uuid4())[:8])
                    item.setdefault("category", "general")
                    item.setdefault("importance", 3)
                    item.setdefault("access_count", 0)
                    item.setdefault("pinned", False)
                    item.setdefault("created_at", time.strftime("%Y-%m-%d %H:%M"))
                    structured.append(item)
            return structured
    except Exception:
        return []

def save_memories(memories: list):
    """Saves structured memories safely to disk."""
    os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=2, ensure_ascii=False)

def infer_category(text: str) -> str:
    """Infers the most appropriate category for a memory text."""
    lower = text.lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return cat
    return "general"

def add_memory_item(content: str, category: str = None, source_mission: str = "Manual Entry", importance: int = 3, pinned: bool = False) -> dict:
    """Adds a single categorized memory item."""
    if not content or not content.strip():
        return None
    content = content.strip()
    if not category or category not in MEMORY_CATEGORIES:
        category = infer_category(content)
        
    memories = load_memories()
    # Check if duplicate already exists
    for m in memories:
        if m["content"].lower() == content.lower():
            m["access_count"] += 1
            m["importance"] = max(m.get("importance", 3), importance)
            save_memories(memories)
            return m

    new_mem = {
        "id": str(uuid.uuid4())[:8],
        "category": category,
        "content": content,
        "source_mission": source_mission,
        "importance": max(1, min(5, importance)),
        "access_count": 1,
        "pinned": pinned,
        "created_at": time.strftime("%Y-%m-%d %H:%M")
    }
    memories.insert(0, new_mem)
    save_memories(memories)
    return new_mem

def batch_add_from_mission(mission_text: str, source_mission: str = "Autonomous Mission") -> int:
    """Extracts bullet points from agent outputs and saves categorized memories."""
    lines = mission_text.splitlines()
    added_count = 0
    for line in lines:
        cleaned = line.strip()
        if cleaned.startswith(("- ", "* ", "• ", "1. ", "2. ", "3. ")):
            item_text = re.sub(r"^[-*•\d.]+\s*", "", cleaned).strip()
            if len(item_text) > 15 and not item_text.startswith("```"):
                add_memory_item(item_text, source_mission=source_mission, importance=3)
                added_count += 1
    return added_count

def get_relevant_memories_for_task(task_prompt: str, max_items: int = 8) -> str:
    """
    Semantically retrieves the most relevant memories for a task prompt,
    prioritizing pinned items and domain-matched categories.
    """
    memories = load_memories()
    if not memories:
        return ""

    task_lower = task_prompt.lower()
    scored = []
    for m in memories:
        score = m.get("importance", 3)
        if m.get("pinned", False):
            score += 10  # Pinned items always prioritized

        # Match content keywords
        m_words = set(re.findall(r"\w+", m["content"].lower()))
        t_words = set(re.findall(r"\w+", task_lower))
        overlap = len(m_words.intersection(t_words))
        score += overlap * 2

        # Match category keywords
        cat = m.get("category", "general")
        if cat in CATEGORY_KEYWORDS:
            if any(kw in task_lower for kw in CATEGORY_KEYWORDS[cat]):
                score += 4

        m["access_count"] = m.get("access_count", 0) + 1
        scored.append((score, m))

    save_memories(memories)
    scored.sort(key=lambda x: x[0], reverse=True)
    top_items = [m for _, m in scored[:max_items]]

    if not top_items:
        return ""

    lines = ["=== RELEVANT PERSISTENT NEURAL MEMORIES & SYSTEM GUIDELINES ==="]
    for idx, item in enumerate(top_items, 1):
        cat_label = MEMORY_CATEGORIES.get(item.get("category"), "General")
        lines.append(f"{idx}. [{cat_label}] {item['content']}")
    return "\n".join(lines)

def deduplicate_and_consolidate_memories() -> int:
    """Removes redundant memory entries while preserving the highest importance and access counts."""
    memories = load_memories()
    if not memories:
        return 0

    unique_map = {}
    for m in memories:
        norm_key = re.sub(r"[^\w\s]", "", m["content"].lower()).strip()
        if norm_key not in unique_map:
            unique_map[norm_key] = m
        else:
            existing = unique_map[norm_key]
            existing["access_count"] += m.get("access_count", 1)
            existing["importance"] = max(existing.get("importance", 3), m.get("importance", 3))
            existing["pinned"] = existing.get("pinned", False) or m.get("pinned", False)

    consolidated = list(unique_map.values())
    removed_count = len(memories) - len(consolidated)
    save_memories(consolidated)
    return removed_count
