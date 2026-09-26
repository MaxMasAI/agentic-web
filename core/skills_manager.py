"""
core/skills_manager.py - Claude AI-Style Dynamic Skills Ingestion & Management Engine
Supports importing and learning skills from:
- Any GitHub repository URL (e.g. https://github.com/addyosmani/agent-skills.git)
- Any local Markdown file (*.md / SKILL.md)
- Direct Markdown text input

All imported skills are stored permanently in the `skills/` (and `Skill/`) directory.
Maintains `json/skills_registry.json` for ultra-fast matching and prompt injection.
"""

import os
import re
import json
import shutil
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(PROJECT_ROOT, "skills")
SKILL_ALIAS_DIR = os.path.join(PROJECT_ROOT, "Skill")
JSON_DIR = os.path.join(PROJECT_ROOT, "json")
REGISTRY_FILE = os.path.join(JSON_DIR, "skills_registry.json")


def parse_skill_markdown(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parses a skill markdown file, extracting YAML frontmatter or Markdown headers,
    and returns (metadata_dict, clean_body).
    """
    metadata = {
        "name": "",
        "description": "",
        "category": "general",
        "triggers": [],
        "version": "1.0",
        "author": "custom",
        "tags": []
    }
    body = content

    # 1. Try YAML Frontmatter format:
    # ---
    # name: ...
    # description: ...
    # ---
    fm_match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n(.*)$", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        body = fm_match.group(2).strip()

        for line in fm_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lower()
                val = val.strip().strip("\"'")
                if key in ["tags", "triggers"]:
                    items = [t.strip().strip("\"'[]") for t in val.split(",") if t.strip()]
                    metadata[key] = items
                else:
                    metadata[key] = val

    # 2. Extract Title from # Header if name not in frontmatter
    if not metadata.get("name"):
        title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        if title_match:
            metadata["name"] = title_match.group(1).strip()
        else:
            metadata["name"] = "Untitled Skill"

    # 3. Extract description snippet if missing
    if not metadata.get("description"):
        lines = [line.strip() for line in body.splitlines() if line.strip() and not line.startswith("#")]
        if lines:
            metadata["description"] = lines[0][:180]

    return metadata, body


class SkillsManager:
    """Enterprise Skills Vault managing dynamic ingestion, indexing, and runtime injection."""

    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self.registry: List[Dict[str, Any]] = []
        os.makedirs(self.skills_dir, exist_ok=True)
        os.makedirs(JSON_DIR, exist_ok=True)
        self.scan_and_index_skills()

    def scan_and_index_skills(self) -> List[Dict[str, Any]]:
        """
        Scans `skills/` (and `Skill/`) for all `SKILL.md` and `*.md` files,
        updates the registry, and saves `json/skills_registry.json`.
        """
        scanned_skills = []

        # Scan both skills and Skill directories
        dirs_to_scan = [self.skills_dir]
        if os.path.exists(SKILL_ALIAS_DIR) and SKILL_ALIAS_DIR != self.skills_dir:
            dirs_to_scan.append(SKILL_ALIAS_DIR)

        for base_dir in dirs_to_scan:
            for root, dirs, files in os.walk(base_dir):
                for file in files:
                    if not file.endswith(".md"):
                        continue
                    if file.upper() in ["README.MD", "CONTRIBUTING.MD", "LICENSE.MD"]:
                        continue

                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, PROJECT_ROOT).replace("\\", "/")

                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        meta, body = parse_skill_markdown(content)
                        
                        # Generate unique skill ID
                        slug = os.path.splitext(file)[0].lower()
                        if slug == "skill":
                            # Use parent directory name
                            slug = os.path.basename(root).lower()
                        slug = re.sub(r"[^a-z0-9_-]", "-", slug)

                        skill_entry = {
                            "id": slug,
                            "name": meta.get("name") or slug.replace("-", " ").title(),
                            "description": meta.get("description", ""),
                            "category": meta.get("category", "engineering"),
                            "triggers": meta.get("triggers", []),
                            "tags": meta.get("tags", []),
                            "file_rel_path": rel_path,
                            "full_path": full_path,
                            "is_enabled": True,
                            "content_preview": body[:300],
                            "size_bytes": os.path.getsize(full_path)
                        }
                        scanned_skills.append(skill_entry)
                    except Exception as e:
                        print(f"[SkillsManager] Error reading skill at {full_path}: {e}")

        # Deduplicate by ID
        unique_skills = {}
        for s in scanned_skills:
            unique_skills[s["id"]] = s

        self.registry = list(unique_skills.values())
        self.save_registry()
        return self.registry

    def save_registry(self):
        """Persists the indexed skills registry to json/skills_registry.json."""
        try:
            with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "total": len(self.registry),
                    "skills": self.registry
                }, f, indent=2)
        except Exception as e:
            print(f"[SkillsManager] Failed to save registry: {e}")

    def list_all_skills(self) -> List[Dict[str, Any]]:
        return self.registry

    def get_skill_by_id(self, skill_id: str) -> Optional[Dict[str, Any]]:
        for s in self.registry:
            if s["id"] == skill_id:
                return s
        return None

    def get_skill_content(self, skill_id: str) -> Optional[str]:
        skill = self.get_skill_by_id(skill_id)
        if not skill or not os.path.exists(skill["full_path"]):
            return None
        try:
            with open(skill["full_path"], "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception as e:
            print(f"[SkillsManager] Error reading skill content {skill_id}: {e}")
            return None

    def import_from_markdown_text(self, name: str, content: str, category: str = "custom") -> Dict[str, Any]:
        """Saves raw markdown content as a new skill into skills/<slug>/SKILL.md."""
        slug = re.sub(r"[^a-z0-9_-]", "-", name.lower().strip()) or "custom-skill"
        target_dir = os.path.join(self.skills_dir, slug)
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, "SKILL.md")

        # Ensure content has basic header/frontmatter if missing
        if not content.startswith("---") and not content.startswith("#"):
            content = f"# {name}\n\n{content}"

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)

        self.scan_and_index_skills()
        return self.get_skill_by_id(slug) or {}

    def import_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Imports an existing local markdown file into the skills folder."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_name = os.path.basename(file_path)
        slug = os.path.splitext(file_name)[0].lower()
        slug = re.sub(r"[^a-z0-9_-]", "-", slug)

        target_dir = os.path.join(self.skills_dir, slug)
        os.makedirs(target_dir, exist_ok=True)
        target_file = os.path.join(target_dir, "SKILL.md")

        shutil.copy2(file_path, target_file)
        self.scan_and_index_skills()
        return self.get_skill_by_id(slug)

    def import_from_github(self, repo_url: str, branch: str = "main", subpath: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Clones or fetches any GitHub repository, discovers all `SKILL.md` and `*.md`
        skill definitions, and imports them permanently into `skills/`.
        """
        repo_url = repo_url.strip()
        if not repo_url.startswith("http"):
            repo_url = f"https://github.com/{repo_url}"
        if not repo_url.endswith(".git"):
            repo_url += ".git"

        temp_dir = tempfile.mkdtemp(prefix="agy_skills_clone_")
        imported_skills = []

        try:
            # 1. Run git clone with depth 1 for maximum speed
            clone_cmd = ["git", "clone", "--depth", "1", repo_url, temp_dir]
            res = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=60)
            if res.returncode != 0:
                # Retry without depth if specific ref failed
                res = subprocess.run(["git", "clone", repo_url, temp_dir], capture_output=True, text=True, timeout=90)
                if res.returncode != 0:
                    raise RuntimeError(f"Git clone failed: {res.stderr or res.stdout}")

            # 2. Scan cloned directory for markdown and SKILL.md files
            search_root = os.path.join(temp_dir, subpath) if subpath else temp_dir

            for root, dirs, files in os.walk(search_root):
                if ".git" in root or ".github" in root:
                    continue

                for file in files:
                    if not file.endswith(".md"):
                        continue
                    if file.upper() in ["README.MD", "CONTRIBUTING.MD", "LICENSE.MD", "SECURITY.MD"]:
                        continue

                    src_file = os.path.join(root, file)
                    rel_sub = os.path.relpath(src_file, search_root)

                    # Determine clean skill name / slug
                    slug = os.path.splitext(file)[0].lower()
                    if slug == "skill":
                        slug = os.path.basename(root).lower()
                    slug = re.sub(r"[^a-z0-9_-]", "-", slug)

                    target_skill_dir = os.path.join(self.skills_dir, slug)
                    os.makedirs(target_skill_dir, exist_ok=True)
                    target_skill_file = os.path.join(target_skill_dir, "SKILL.md")

                    shutil.copy2(src_file, target_skill_file)

            # 3. Refresh index
            self.scan_and_index_skills()
            return self.registry
        finally:
            # Cleanup temp clone
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def delete_skill(self, skill_id: str) -> bool:
        """Deletes a skill from disk and updates index."""
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            return False

        full_path = skill.get("full_path")
        if full_path and os.path.exists(full_path):
            parent_dir = os.path.dirname(full_path)
            # If inside its own subdirectory in skills/, remove folder
            if parent_dir != self.skills_dir and parent_dir.startswith(self.skills_dir):
                shutil.rmtree(parent_dir, ignore_errors=True)
            else:
                os.remove(full_path)

        self.scan_and_index_skills()
        return True

    def match_skills_for_task(self, task_prompt: str, max_skills: int = 3) -> List[Dict[str, Any]]:
        """
        Matches relevant skills based on user prompt tokens, triggers, and tags.
        """
        task_lower = task_prompt.lower()
        scored_skills = []

        for skill in self.registry:
            if not skill.get("is_enabled", True):
                continue

            score = 0
            # 1. Trigger word exact match
            for trigger in skill.get("triggers", []):
                if trigger.lower() in task_lower:
                    score += 5

            # 2. Tag match
            for tag in skill.get("tags", []):
                if tag.lower() in task_lower:
                    score += 3

            # 3. Name & Description keyword match
            name_tokens = skill.get("name", "").lower().split()
            for token in name_tokens:
                if len(token) > 3 and token in task_lower:
                    score += 2

            if score > 0:
                scored_skills.append((score, skill))

        scored_skills.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in scored_skills[:max_skills]]


# Global singleton instance
skills_manager = SkillsManager()
