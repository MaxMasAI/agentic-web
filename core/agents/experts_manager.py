"""
core/experts_manager.py - Multi-Agent Experts Co-op Engine (Co-operation Mode)
Implements isolated expert contexts, persistent per-expert memory, orchestrator manager routing,
and inline/autonomous expert consultation.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from services.llm_provider import generate_chat_response

EXPERTS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "experts_presets.json")


DEFAULT_EXPERTS = [
    {
        "id": "python_expert",
        "name": "Python Programmer",
        "role": "Python Engineering & Scripting",
        "description": "Writes clean, robust, type-annotated, and idiomatic Python code.",
        "system_prompt": "You are a senior Python expert specializing in modern Python 3.12+, async programming, clean architecture, and optimization.",
        "enabled": True,
        "tools": ["python_exec", "file_io"]
    },
    {
        "id": "web_dev_expert",
        "name": "Full-Stack Web Architect",
        "role": "Frontend & Backend Web Technologies",
        "description": "Designs responsive modern UIs, APIs, REST, WebSockets, and state architectures.",
        "system_prompt": "You are a master Full-Stack Web Architect proficient in HTML5, CSS3, modern JavaScript/TypeScript, React/Next.js, FastAPI, and responsive design.",
        "enabled": True,
        "tools": ["web_browser", "css_validator"]
    },
    {
        "id": "data_analyst_expert",
        "name": "Data Scientist & Statistician",
        "role": "Data Science, Statistics & Visualization",
        "description": "Processes data, performs statistical analysis, mathematical modeling, and visualization.",
        "system_prompt": "You are a premier Data Scientist and Mathematical Modeler expert in NumPy, Pandas, statistical modeling, machine learning, and data visualization.",
        "enabled": True,
        "tools": ["data_analysis", "math_engine"]
    },
    {
        "id": "qa_security_expert",
        "name": "QA & Security Auditor",
        "role": "Code Auditing, Security, Vulnerabilities & QA",
        "description": "Audits code for edge cases, security flaws, performance bottlenecks, and test coverage.",
        "system_prompt": "You are a ruthless Principal QA and Cybersecurity Auditor identifying vulnerabilities, edge cases, test harnesses, and code quality issues.",
        "enabled": True,
        "tools": ["security_scanner", "linter"]
    },
    {
        "id": "copywriter_expert",
        "name": "Copywriter & Technical Writer",
        "role": "Documentation, Technical Copy & Communication",
        "description": "Crafts high-impact copy, documentation, technical specs, and executive summaries.",
        "system_prompt": "You are a professional Technical Writer and Editorial Strategist crafting concise, engaging, and structured documentation.",
        "enabled": True,
        "tools": ["grammar_check"]
    },
    {
        "id": "devops_expert",
        "name": "Cloud & DevOps Specialist",
        "role": "CI/CD, Docker, Cloud & Infrastructure",
        "description": "Designs CI/CD pipelines, Docker containers, Kubernetes, cloud architectures, and shell automation.",
        "system_prompt": "You are a Staff DevOps and Infrastructure Engineer expert in Docker, Linux, CI/CD pipelines, cloud deployment, and system orchestration.",
        "enabled": True,
        "tools": ["bash_exec", "docker_cli"]
    }
]


class ExpertContext:
    """Maintains isolated context and multi-turn memory for a specific expert."""
    def __init__(self, expert_id: str, name: str, system_prompt: str):
        self.expert_id = expert_id
        self.name = name
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, str]] = []

    def add_interaction(self, user_query: str, expert_response: str):
        self.messages.append({"role": "user", "content": user_query})
        self.messages.append({"role": "assistant", "content": expert_response})

    def clear_memory(self):
        self.messages.clear()


class ExpertsManager:
    """
    Manages expert presets, isolated per-expert memory contexts,
    and the main conversation orchestrator manager.
    """
    def __init__(self, storage_path: str = EXPERTS_FILE):
        self.storage_path = storage_path
        self.presets: Dict[str, Dict[str, Any]] = {}
        self.active_contexts: Dict[str, ExpertContext] = {}
        self.load_presets()

    def load_presets(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.presets = {e["id"]: e for e in data}
                    elif isinstance(data, dict):
                        self.presets = data
                    return
            except Exception:
                pass

        # Default fallback
        self.presets = {e["id"]: e for e in DEFAULT_EXPERTS}
        self.save_presets()

    def save_presets(self):
        if not self.storage_path or self.storage_path == ":memory:":
            return
        parent_dir = os.path.dirname(self.storage_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(list(self.presets.values()), f, indent=2)
        except Exception:
            pass

    def list_all_experts(self) -> List[Dict[str, Any]]:
        return list(self.presets.values())

    def list_active_experts(self) -> List[Dict[str, Any]]:
        return [e for e in self.presets.values() if e.get("enabled", True)]

    def import_agency_agent(self, agency_agent_id: str) -> Optional[Dict[str, Any]]:
        """Imports an agent persona from the 287+ Agency Agents catalog into active experts."""
        try:
            from core.agency_agents_manager import agency_manager
            agent = agency_manager.get_agent_by_id(agency_agent_id)
            if not agent:
                return None
            full_prompt = agency_manager.get_full_agent_markdown(agency_agent_id) or agent.get("system_prompt", "")
            
            preset_entry = {
                "id": agent["id"],
                "name": f"{agent.get('emoji', '🤖')} {agent['name']}",
                "role": f"{agent.get('division_label', 'Specialist')} - {agent.get('vibe', agent.get('name'))}",
                "description": agent.get("description", agent.get("vibe", "")),
                "system_prompt": full_prompt,
                "enabled": True,
                "tools": ["python_exec", "file_io", "web_browser"],
                "division": agent.get("division", "specialized"),
                "color": agent.get("color", "#3B82F6")
            }
            self.presets[agent["id"]] = preset_entry
            self.save_presets()
            return preset_entry
        except Exception as e:
            print(f"[ExpertsManager] Error importing agency agent {agency_agent_id}: {e}")
            return None

    def enable_expert(self, expert_id: str, enabled: bool = True) -> bool:
        if expert_id in self.presets:
            self.presets[expert_id]["enabled"] = enabled
            self.save_presets()
            return True
        return False

    def apply_catalog_prompt_to_expert(self, expert_id: str, prompt_id: str) -> bool:
        """Assigns a specialized prompt from the system prompts catalog to an expert."""
        try:
            from services.system_prompts_catalog import get_system_prompts_catalog
            prompt_data = get_system_prompts_catalog().get_prompt(prompt_id)
            if prompt_data and expert_id in self.presets:
                self.presets[expert_id]["system_prompt"] = prompt_data["prompt"]
                self.save_presets()
                if expert_id in self.active_contexts:
                    self.active_contexts[expert_id].system_prompt = prompt_data["prompt"]
                return True
        except Exception:
            pass
        return False

    def get_or_create_context(self, expert_id: str) -> Optional[ExpertContext]:
        if expert_id not in self.presets:
            return None
        if expert_id not in self.active_contexts:
            exp = self.presets[expert_id]
            self.active_contexts[expert_id] = ExpertContext(
                expert_id=exp["id"],
                name=exp["name"],
                system_prompt=exp.get("system_prompt", f"You are {exp['name']}.")
            )
        return self.active_contexts[expert_id]

    def find_expert_by_reference(self, ref: str) -> Optional[Dict[str, Any]]:
        """Finds an enabled expert matching an ID, name, or keyword."""
        ref_lower = ref.lower().strip()
        active = self.list_active_experts()
        
        # Exact ID match
        for exp in active:
            if exp["id"].lower() == ref_lower:
                return exp
        
        # Name match
        for exp in active:
            if exp["name"].lower() in ref_lower or ref_lower in exp["name"].lower():
                return exp
                
        # Role/keyword match
        for exp in active:
            if any(w in exp["role"].lower() for w in ref_lower.split()):
                return exp
                
        return None

    def call_expert(self, expert_ref: str, task: str, model_id: str = "gemini-2.0-flash") -> Dict[str, Any]:
        """
        Invokes an expert in their isolated context with their own memory history.
        """
        exp = self.find_expert_by_reference(expert_ref)
        if not exp:
            return {
                "success": False,
                "error": f"Expert '{expert_ref}' not found or is currently disabled.",
                "content": ""
            }

        ctx = self.get_or_create_context(exp["id"])
        
        # Build prompt history including the expert's isolated memory
        messages = list(ctx.messages)
        messages.append({"role": "user", "content": task})

        response = generate_chat_response(
            messages=messages,
            model_id=model_id,
            system_prompt=ctx.system_prompt
        )

        content = response.get("content", "")
        if response.get("status") == "success" or content:
            ctx.add_interaction(task, content)
            return {
                "success": True,
                "expert_id": exp["id"],
                "expert_name": exp["name"],
                "content": content,
                "memory_turns": len(ctx.messages) // 2
            }
        else:
            return {
                "success": False,
                "error": response.get("error", "Failed to generate response"),
                "content": ""
            }

    def handle_manager_turn(
        self,
        user_message: str,
        main_history: List[Dict[str, str]],
        model_id: str = "gemini-2.0-flash"
    ) -> Dict[str, Any]:
        """
        Main conversation manager:
        1. Checks for direct commands (e.g. 'Give me a list of active experts', 'Call the Python expert to...')
        2. Detects if task requires expert delegation
        3. Coordinates background consultations and returns consolidated response.
        """
        msg_lower = user_message.lower().strip()

        # 1. Direct command: List active experts
        if any(p in msg_lower for p in ["list of active experts", "list active experts", "list experts", "show experts"]):
            active = self.list_active_experts()
            formatted = "\n".join([f"- **{e['name']}** (`{e['id']}`): {e['role']} — {e['description']}" for e in active])
            reply = f"### 🧠 Active Experts in Co-op Mode ({len(active)} Available)\n\n{formatted}\n\n*You can consult any expert by asking directly (e.g. 'Call the Python expert to write a script').*"
            return {
                "role": "manager",
                "content": reply,
                "consulted_experts": []
            }

        # 2. Explicit expert invocation pattern: "Call the [expert] to [task]" / "Ask [expert] to [task]"
        call_match = re.search(r"(?:call|ask|consult)\s+(?:the\s+)?([a-zA-Z0-9_\s]+?)\s+(?:expert\s+)?to\s+(.+)", user_message, re.IGNORECASE)
        if call_match:
            exp_ref = call_match.group(1).strip()
            sub_task = call_match.group(2).strip()
            exp = self.find_expert_by_reference(exp_ref)
            if exp:
                result = self.call_expert(exp["id"], sub_task, model_id=model_id)
                if result.get("success"):
                    content = result["content"]
                    formatted = f"**[Consulted Expert: {exp['name']}]**\n\n{content}"
                    return {
                        "role": "manager",
                        "content": formatted,
                        "consulted_experts": [exp["name"]]
                    }

        # 3. Standard conversation or manager orchestration
        # Manager analyzes if an expert is specifically well suited
        consulted = []
        for exp in self.list_active_experts():
            keywords = exp["role"].lower().replace(",", " ").split()
            if any(k in msg_lower for k in keywords if len(k) > 3):
                # Consult expert in background
                res = self.call_expert(exp["id"], user_message, model_id=model_id)
                if res.get("success"):
                    consulted.append({"expert": exp["name"], "content": res["content"]})
                break

        if consulted:
            exp_info = consulted[0]
            synth_prompt = (
                f"User Question: {user_message}\n\n"
                f"Specialist Report ({exp_info['expert']}):\n{exp_info['content']}\n\n"
                f"As the Lead Manager in Co-op mode, integrate the specialist's insights into a clear, comprehensive, and complete response."
            )
            synth_res = generate_chat_response(
                [{"role": "user", "content": synth_prompt}],
                model_id=model_id,
                system_prompt="You are the Lead Co-op Manager coordinating specialized expert consultations."
            )
            return {
                "role": "manager",
                "content": synth_res.get("content", exp_info["content"]),
                "consulted_experts": [c["expert"] for c in consulted]
            }

        # Regular manager answer
        normal_res = generate_chat_response(
            messages=main_history + [{"role": "user", "content": user_message}],
            model_id=model_id,
            system_prompt="You are a versatile AI orchestrator operating in Co-op Expert mode."
        )
        return {
            "role": "manager",
            "content": normal_res.get("content", ""),
            "consulted_experts": []
        }

    def reset_all_memories(self):
        """Clears isolated memory contexts for all experts."""
        self.active_contexts.clear()


# Global Singleton Instance
_experts_manager_instance: Optional[ExpertsManager] = None

def get_experts_manager() -> ExpertsManager:
    global _experts_manager_instance
    if _experts_manager_instance is None:
        _experts_manager_instance = ExpertsManager()
    return _experts_manager_instance
