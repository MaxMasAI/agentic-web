"""
core/agency_agents_manager.py - Enterprise Agency Agents Integration & Orchestration Engine
Provides unified indexing, dynamic search, persona injection, and squad integration
for the 287+ Agency Agents catalog (across Engineering, Security, Design, Marketing,
Game Development, GIS, Healthcare, Product, Testing, and Specialized divisions).
"""

import os
import json
import re
from typing import Dict, List, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(PROJECT_ROOT, "json")
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "agency_agents")
CATALOG_FILE = os.path.join(JSON_DIR, "agency_agents_catalog.json")
DIVISIONS_FILE = os.path.join(JSON_DIR, "agency_divisions.json")


class AgencyAgentsManager:
    """Manages the full Agency Agents roster, divisions, search, and persona retrieval."""

    def __init__(self):
        self.catalog: List[Dict[str, Any]] = []
        self.divisions: Dict[str, Dict[str, Any]] = {}
        self.agent_map: Dict[str, Dict[str, Any]] = {}
        self.reload()

    def reload(self):
        """Reloads the catalog and division index from disk."""
        if os.path.exists(CATALOG_FILE):
            try:
                with open(CATALOG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.catalog = data.get("agents", [])
            except Exception as e:
                print(f"[AgencyAgentsManager] Error loading catalog: {e}")
                self.catalog = []
        else:
            self.catalog = []

        if os.path.exists(DIVISIONS_FILE):
            try:
                with open(DIVISIONS_FILE, "r", encoding="utf-8") as f:
                    self.divisions = json.load(f)
            except Exception as e:
                print(f"[AgencyAgentsManager] Error loading divisions: {e}")
                self.divisions = {}
        else:
            self.divisions = {}

        self.agent_map = {agent["id"]: agent for agent in self.catalog}

    def get_total_count(self) -> int:
        return len(self.catalog)

    def get_divisions(self) -> Dict[str, Dict[str, Any]]:
        """Returns all divisions with their metadata and agent count."""
        result = {}
        for div_key, div_info in self.divisions.items():
            count = sum(1 for a in self.catalog if a.get("division") == div_key)
            result[div_key] = {
                **div_info,
                "agent_count": count
            }
        return result

    def get_agents_by_division(self, division_key: str) -> List[Dict[str, Any]]:
        """Returns all agents belonging to a specific division."""
        return [a for a in self.catalog if a.get("division") == division_key]

    def get_agent_by_id(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Returns an agent by its unique identifier."""
        return self.agent_map.get(agent_id)

    def search_agents(self, query: str = "", division: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fuzzy search across agent names, descriptions, vibes, and divisions.
        """
        query = query.strip().lower()
        results = []

        for agent in self.catalog:
            if division and division != "all" and agent.get("division") != division:
                continue

            if not query:
                results.append(agent)
                continue

            name = agent.get("name", "").lower()
            desc = agent.get("description", "").lower()
            vibe = agent.get("vibe", "").lower()
            div = agent.get("division", "").lower()
            aid = agent.get("id", "").lower()

            if (query in name or query in desc or query in vibe or query in div or query in aid):
                results.append(agent)

        return results[:limit]

    def get_full_agent_markdown(self, agent_id: str) -> Optional[str]:
        """Reads the complete original Markdown persona file from the data folder."""
        agent = self.get_agent_by_id(agent_id)
        if not agent:
            return None

        file_rel = agent.get("file_rel_path")
        if not file_rel:
            return None

        full_path = os.path.join(DATA_DIR, file_rel.replace("/", os.sep))
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                print(f"[AgencyAgentsManager] Error reading agent markdown: {e}")
        return None

    def recommend_agents_for_goal(self, goal: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Recommends best-matching specialist agents for a user's task or goal.
        """
        tokens = set(re.findall(r"\w+", goal.lower()))
        scored_agents = []

        for agent in self.catalog:
            score = 0
            text = f"{agent.get('name', '')} {agent.get('description', '')} {agent.get('vibe', '')} {agent.get('division', '')}".lower()
            
            for token in tokens:
                if len(token) > 2 and token in text:
                    score += 1
            
            if score > 0:
                scored_agents.append((score, agent))

        scored_agents.sort(key=lambda x: x[0], reverse=True)
        return [agent for _, agent in scored_agents[:top_k]]


# Singleton instance
agency_manager = AgencyAgentsManager()
