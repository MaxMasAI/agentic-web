"""
core/agency_agents_manager.py - Enterprise Agency Agents Integration & Orchestration Engine
Provides unified indexing, dynamic search, persona injection, and squad integration
for the 287+ Agency Agents catalog (across Engineering, Security, Design, Marketing,
Game Development, GIS, Healthcare, Product, Testing, and Specialized divisions).
"""

import os
import json
import re
from typing import Dict, List, Any, Optional, Tuple

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

    def _get_agent_squad_models(self, division: str) -> List[str]:
        div = (division or "").lower()
        if div in ["engineering", "testing", "game-development"]:
            return ["gemini", "deepseek", "claude"]
        elif div in ["security"]:
            return ["gemini", "claude", "deepseek"]
        elif div in ["design", "spatial-computing"]:
            return ["gemini", "dalle", "chatgpt"]
        elif div in ["marketing", "paid-media", "sales"]:
            return ["gemini", "meta_ai", "chatgpt"]
        elif div in ["research", "academic", "healthcare", "gis"]:
            return ["gemini", "perplexity", "claude"]
        elif div in ["finance", "project-management", "support", "strategy"]:
            return ["gemini", "copilot", "mistral"]
        else:
            return ["gemini", "deepseek", "chatgpt"]

    def register_all_agents_as_squads(self) -> Tuple[int, int]:
        """
        Registers all 287+ agency agents as squads in json/subagents.json.
        Returns (newly_added_count, total_count).
        """
        import time
        subagents_path = os.path.join(JSON_DIR, "subagents.json")
        existing_squads = []
        if os.path.exists(subagents_path):
            try:
                with open(subagents_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        existing_squads = data
            except Exception:
                existing_squads = []

        existing_names = {s.get("name", "").strip().lower() for s in existing_squads}
        added_count = 0
        now_str = time.strftime("%Y-%m-%d %H:%M")

        for agent in self.catalog:
            name = agent.get("name", "Agent")
            emoji = agent.get("emoji", "🤖")
            squad_name = f"{emoji} {name} Strike Squad"
            if squad_name.lower() in existing_names or f"{emoji} {name}".lower() in existing_names or name.lower() in existing_names:
                continue

            div_label = agent.get("division_label", "Specialist")
            vibe = agent.get("vibe", "")
            desc = agent.get("description", "")
            models = self._get_agent_squad_models(agent.get("division", ""))

            squad = {
                "name": squad_name,
                "agency_id": agent.get("id"),
                "division": agent.get("division"),
                "task": (
                    f"Act as senior specialist: {name} ({div_label}).\n"
                    f"Directive: {vibe}\n"
                    f"Deliverable: {desc}\n"
                    f"Execute specialized domain task adhering to production-grade quality."
                ),
                "desc": f"[{div_label}] {vibe or desc[:80]}",
                "agents": models,
                "created": now_str,
                "agency_agent": True
            }
            existing_squads.append(squad)
            existing_names.add(squad_name.lower())
            added_count += 1

        os.makedirs(JSON_DIR, exist_ok=True)
        with open(subagents_path, "w", encoding="utf-8") as f:
            json.dump(existing_squads, f, indent=2)

        return added_count, len(existing_squads)

    def ingest_all_agents_as_skills(self) -> Tuple[int, int]:
        """
        Ingests all 287+ agency agents into skills/ directory as structured skill packages (SKILL.md).
        Returns (newly_created_count, total_count).
        """
        from core.skills_manager import skills_manager
        skills_dir = os.path.join(PROJECT_ROOT, "skills")
        os.makedirs(skills_dir, exist_ok=True)

        added_count = 0
        for agent in self.catalog:
            aid = agent.get("id")
            if not aid:
                continue
            skill_folder_name = f"agency-{aid}"
            skill_dir = os.path.join(skills_dir, skill_folder_name)
            skill_file = os.path.join(skill_dir, "SKILL.md")

            if os.path.exists(skill_file):
                continue

            os.makedirs(skill_dir, exist_ok=True)
            full_md = self.get_full_agent_markdown(aid) or agent.get("system_prompt", "")
            name = agent.get("name", aid)
            emoji = agent.get("emoji", "🤖")
            div = agent.get("division", "general")
            div_label = agent.get("division_label", div.title())
            raw_desc = (agent.get("description") or agent.get("vibe") or f"{name} specialist")
            desc = raw_desc.replace('"', "'").replace("\n", " ")
            vibe = agent.get("vibe", "")

            frontmatter = (
                f"---\n"
                f'name: "{emoji} {name}"\n'
                f'description: "{desc[:160]}"\n'
                f'category: "{div}"\n'
                f'tags: ["agency", "{div}", "{aid}"]\n'
                f'triggers: ["{aid}", "{name.lower()}"]\n'
                f'author: "The Agency"\n'
                f"---\n\n"
            )

            body_content = (
                f"# {emoji} {name} ({div_label})\n\n"
                f"> **Directive / Vibe**: {vibe}\n\n"
                f"{full_md}\n"
            )

            with open(skill_file, "w", encoding="utf-8") as f:
                f.write(frontmatter + body_content)
            added_count += 1

        skills_manager.scan_and_index_skills()
        return added_count, len(skills_manager.list_all_skills())


# Singleton instance
agency_manager = AgencyAgentsManager()

