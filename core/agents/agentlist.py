"""
agentlist.py - AI Agent Directory & Metadata
Configured for multi-agent browser and workflow automation.
Supports dynamic leader assignment: If any model is saved as leader, Gemini automatically
moves into the specialist agents list and acts as a normal specialist.
Supports dynamic addition, updating, and deletion of custom user agents via GUI Settings / JSON / text format.
"""

import os
import json
import ast
import re
from typing import Dict, Any, List, Optional, Tuple

# Path to persistent custom agents storage
JSON_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "json"))
CUSTOM_AGENTS_FILE = os.path.join(JSON_DIR, "custom_agents.json")
AGENT_STATUS_FILE = os.path.join(JSON_DIR, "agent_status.json")

# Master Leader / Orchestrator Agent (Default Gemini definition)
DEFAULT_LEAD_AGENT: Dict[str, Any] = {
    "id": "gemini",
    "name": "Google Gemini",
    "icon": "✨",
    "role": "Master Orchestrator & Leadership Lead",
    "specialization": (
        "Project orchestration, multimodal asset evaluation, strict design quality audits, "
        "repetition filtering, prompt engineering refinement, and workflow direction."
    ),
    "official_url": "https://gemini.google.com",
    "is_leader": True,
    "routing_tag": "[SEND_TO: gemini]"
}

# Subordinate Specialist Agents (Default)
DEFAULT_SPECIALIST_AGENTS: List[Dict[str, Any]] = [
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "icon": "🐋",
        "role": "Creative Ideator & Deep Researcher",
        "specialization": (
            "Trend research, rapid concept brainstorming, cross-cultural aesthetic synthesis, "
            "and technical reasoning for fresh design ideation."
        ),
        "official_url": "https://chat.deepseek.com",
        "is_leader": False,
        "routing_tag": "[SEND_TO: deepseek]"
    },
    {
        "id": "chatgpt",
        "name": "OpenAI ChatGPT",
        "icon": "✳️",
        "role": "Campaign Synthesizer & Client Dispatcher",
        "specialization": (
            "Final copy production, campaign aggregation, social media marketing text, "
            "hashtag generation, and formatted client-facing deliverables."
        ),
        "official_url": "https://chatgpt.com",
        "is_leader": False,
        "routing_tag": "[SEND_TO: chatgpt]"
    },
    {
        "id": "claude",
        "name": "Anthropic Claude",
        "icon": "✴️",
        "role": "Editorial & Nuance Reviewer",
        "specialization": (
            "In-depth editorial critique, long-form content structuring, tone refinement, "
            "and adherence to complex narrative constraints."
        ),
        "official_url": "https://claude.ai",
        "is_leader": False,
        "routing_tag": "[SEND_TO: claude]"
    },
    {
        "id": "meta_ai",
        "name": "Meta AI",
        "icon": "♾️",
        "role": "Social Trends & Viral Formatting Agent",
        "specialization": (
            "Platform-specific social media hooks, viral pattern evaluation, and rapid "
            "audience engagement tactics."
        ),
        "official_url": "https://www.meta.ai",
        "is_leader": False,
        "routing_tag": "[SEND_TO: meta_ai]"
    },
    {
        "id": "dalle",
        "name": "OpenAI DALL-E 3 Specialist",
        "icon": "🎨",
        "role": "Graphic Asset Descriptor & Visual Prompt Designer",
        "specialization": (
            "Detailed text-to-image prompt styling, aspect ratio calculations, visual asset layout planning, "
            "and aesthetic style translation."
        ),
        "official_url": "https://chatgpt.com/?model=dall-e-3",
        "is_leader": False,
        "routing_tag": "[SEND_TO: dalle]"
    },
    {
        "id": "perplexity",
        "name": "Perplexity AI",
        "icon": "🔍",
        "role": "Real-Time Fact Checker & Citations Specialist",
        "specialization": (
            "Live web searching, source verification, comparative data auditing, "
            "and academic citation gathering."
        ),
        "official_url": "https://www.perplexity.ai",
        "is_leader": False,
        "routing_tag": "[SEND_TO: perplexity]"
    },
    {
        "id": "copilot",
        "name": "Microsoft Copilot",
        "icon": "🪟",
        "role": "Office Suite & Enterprise Integration Specialist",
        "specialization": (
            "Enterprise workflow coordination, formatting guidelines, office documentation outline structures, "
            "and macro/data table automation formulas."
        ),
        "official_url": "https://copilot.microsoft.com",
        "is_leader": False,
        "routing_tag": "[SEND_TO: copilot]"
    },
    {
        "id": "nvidia_ai",
        "name": "Nvidia NIM AI",
        "icon": "🟩",
        "role": "High-Performance GPU Compute & Optimization Advisor",
        "specialization": (
            "Technical scaling, performance profiling recommendations, API compute efficiency, "
            "and deep math/scientific calculation auditing."
        ),
        "official_url": "https://build.nvidia.com",
        "is_leader": False,
        "routing_tag": "[SEND_TO: nvidia_ai]"
    },
    {
        "id": "mistral",
        "name": "Mistral Le Chat",
        "icon": "🌪️",
        "role": "European Multilingual & Open-Weights Specialist",
        "specialization": (
            "Fluent translation across multiple European languages, light-weight utility scripts coding, "
            "and cost-effective task delegation."
        ),
        "official_url": "https://chat.mistral.ai",
        "is_leader": False,
        "routing_tag": "[SEND_TO: mistral]"
    },
    {
        "id": "web_agent",
        "name": "Web-Agent",
        "icon": "🖥️",
        "role": "Full-Screen Autonomous Browser & Screen Overseer",
        "specialization": (
            "Full-screen computer use, whole-page visual inspection, multi-window layout coordination, "
            "direct web navigation, interactive clicking, and overarching screen management."
        ),
        "official_url": "https://google.com",
        "is_leader": False,
        "routing_tag": "[SEND_TO: web_agent]"
    },
    {
        "id": "grok",
        "name": "xAI Grok",
        "icon": "⚡",
        "role": "Real-Time Deep Search & Unhinged Truth Specialist",
        "specialization": (
            "Real-time knowledge retrieval, maximum truth-seeking, razor-sharp witty analysis, "
            "spicy/humorous critical perspective, and advanced deep-thinking breakdowns."
        ),
        "official_url": "https://grok.x.ai",
        "is_leader": False,
        "routing_tag": "[SEND_TO: grok]"
    }
]

LEAD_AGENT: Dict[str, Any] = dict(DEFAULT_LEAD_AGENT)
SPECIALIST_AGENTS: List[Dict[str, Any]] = [dict(a) for a in DEFAULT_SPECIALIST_AGENTS]
CUSTOM_AGENTS: List[Dict[str, Any]] = []
ALL_AGENTS: Dict[str, Dict[str, Any]] = {}


def load_custom_agents_from_disk() -> List[Dict[str, Any]]:
    """Loads custom user-added agents from json/custom_agents.json."""
    if not os.path.exists(CUSTOM_AGENTS_FILE):
        return []
    try:
        with open(CUSTOM_AGENTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return list(data.values())
    except Exception as e:
        print(f"[AgentList] Error loading custom agents: {e}")
    return []


def save_custom_agents_to_disk(agents: List[Dict[str, Any]]) -> bool:
    """Saves custom user-added agents to json/custom_agents.json."""
    try:
        os.makedirs(JSON_DIR, exist_ok=True)
        with open(CUSTOM_AGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(agents, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[AgentList] Error saving custom agents: {e}")
        return False


def sync_agent_status_file():
    """Ensures json/agent_status.json has entries for all active agents with accurate LEADER/FREE states."""
    try:
        current_status = {}
        if os.path.exists(AGENT_STATUS_FILE):
            try:
                with open(AGENT_STATUS_FILE, "r", encoding="utf-8") as f:
                    current_status = json.load(f)
            except Exception:
                current_status = {}
        
        all_active = list_all_active_agents()
        active_leader_id = LEAD_AGENT["id"]
        
        for a in all_active:
            aid = a["id"]
            is_cur_leader = (aid == active_leader_id)
            prev_entry = current_status.get(aid, {})
            prev_state = prev_entry.get("state", "FREE")
            
            if is_cur_leader:
                new_state = "LEADER"
                new_task = "Master Orchestrator"
            else:
                new_state = "FREE" if prev_state == "LEADER" else prev_state
                prev_task = prev_entry.get("current_task", "Idle - Ready for assignment")
                new_task = "Idle - Ready for assignment" if prev_task == "Master Orchestrator" else prev_task
            
            current_status[aid] = {
                "id": aid,
                "name": a.get("name", aid),
                "role": a.get("role", "AI Specialist"),
                "specialization": a.get("specialization", ""),
                "state": new_state,
                "current_task": new_task,
                "last_updated": prev_entry.get("last_updated", "Initialized")
            }
        
        os.makedirs(JSON_DIR, exist_ok=True)
        with open(AGENT_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(current_status, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[AgentList] Error syncing agent status file: {e}")


def reload_agents():
    """
    Reloads defaults and custom agents, updating global state.
    If any custom or specialist agent is marked as leader:
    - That agent becomes LEAD_AGENT.
    - Gemini automatically moves into SPECIALIST_AGENTS and acts as a normal specialist agent.
    - Otherwise, Gemini acts as the default LEAD_AGENT.
    """
    global LEAD_AGENT, SPECIALIST_AGENTS, CUSTOM_AGENTS, ALL_AGENTS
    
    CUSTOM_AGENTS = load_custom_agents_from_disk()
    
    # Check if any custom agent is configured as leader
    custom_leader = None
    custom_specialists = []
    for ca in CUSTOM_AGENTS:
        if ca.get("is_leader"):
            custom_leader = ca
        else:
            custom_specialists.append(ca)
            
    if custom_leader and custom_leader.get("id") != "gemini":
        # Custom model is Master Leader!
        LEAD_AGENT = dict(custom_leader)
        LEAD_AGENT["is_leader"] = True
        
        # Gemini goes to the specialists list and acts as a normal specialist agent
        gemini_specialist = dict(DEFAULT_LEAD_AGENT)
        gemini_specialist["is_leader"] = False
        gemini_specialist["role"] = "Multimodal Evaluator & Specialist Agent"
        gemini_specialist["routing_tag"] = "[SEND_TO: gemini]"
        
        # Filter default specialists so the custom leader isn't duplicated if it shares ID with default
        base_specialists = [gemini_specialist] + [
            dict(a) for a in DEFAULT_SPECIALIST_AGENTS if a["id"] != custom_leader["id"]
        ]
        SPECIALIST_AGENTS = base_specialists + custom_specialists
    else:
        # Default Gemini Leader
        LEAD_AGENT = dict(DEFAULT_LEAD_AGENT)
        LEAD_AGENT["is_leader"] = True
        SPECIALIST_AGENTS = [dict(a) for a in DEFAULT_SPECIALIST_AGENTS] + custom_specialists
        
    ALL_AGENTS = {
        LEAD_AGENT["id"]: LEAD_AGENT,
        **{agent["id"]: agent for agent in SPECIALIST_AGENTS}
    }
    sync_agent_status_file()


def parse_agent_text_format(text: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """
    Parses agent data provided in text format.
    Supports:
    1. Standard JSON object format
    2. Python dictionary format (with single quotes, tuples, multiline string)
    3. Key-Value text format (e.g. id: my_agent \n name: My Agent ...)
    
    Returns (agent_dict, error_message).
    """
    if not text or not text.strip():
        return None, "Empty text provided."
    
    clean_text = text.strip()
    
    # 1. Try standard JSON
    try:
        data = json.loads(clean_text)
        if isinstance(data, dict):
            valid, err = validate_agent_schema(data)
            if valid:
                return normalize_agent_dict(data), ""
            return None, err
    except json.JSONDecodeError:
        pass
        
    # 2. Try Python AST literal_eval (handles Python dicts with tuples/multiline strings)
    try:
        data = ast.literal_eval(clean_text)
        if isinstance(data, dict):
            valid, err = validate_agent_schema(data)
            if valid:
                return normalize_agent_dict(data), ""
            return None, err
    except Exception:
        pass
        
    # 3. Try Line-by-Line Key: Value parsing
    try:
        lines = clean_text.splitlines()
        parsed: Dict[str, Any] = {}
        current_key = None
        current_val_lines = []
        
        for line in lines:
            trimmed = line.strip()
            if not trimmed or trimmed.startswith("#") or trimmed.startswith("//"):
                continue
            trimmed = trimmed.rstrip(",")
            if trimmed in ("{", "}"):
                continue
                
            kv_match = re.match(r'^["\']?([a-zA-Z0-9_]+)["\']?\s*[:=]\s*(.*)$', trimmed)
            if kv_match:
                if current_key:
                    parsed[current_key] = " ".join(current_val_lines).strip()
                    current_val_lines = []
                current_key = kv_match.group(1).lower()
                val_part = kv_match.group(2).strip().strip("\"'()[]")
                current_val_lines.append(val_part)
            elif current_key:
                val_part = trimmed.strip("\"'()[]")
                current_val_lines.append(val_part)
                
        if current_key:
            parsed[current_key] = " ".join(current_val_lines).strip()
            
        if parsed:
            if "is_leader" in parsed:
                parsed["is_leader"] = str(parsed["is_leader"]).lower() in ("true", "1", "yes")
            valid, err = validate_agent_schema(parsed)
            if valid:
                return normalize_agent_dict(parsed), ""
            return None, err
    except Exception as e:
        return None, f"Failed to parse text format: {e}"
        
    return None, "Invalid text format. Please provide valid JSON or key: value text."


def validate_agent_schema(data: Dict[str, Any]) -> Tuple[bool, str]:
    """Validates that the required agent fields exist and are non-empty."""
    if not isinstance(data, dict):
        return False, "Agent data must be a dictionary/object."
        
    required_fields = ["id", "name", "role"]
    for field in required_fields:
        if field not in data or not str(data[field]).strip():
            return False, f"Missing required field: '{field}'"
            
    # Clean ID format
    aid = str(data["id"]).strip().lower()
    if not re.match(r'^[a-z0-9_\-]+$', aid):
        return False, f"Agent ID '{aid}' must contain only lowercase letters, digits, underscores, or hyphens."
        
    return True, ""


def normalize_agent_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes agent dictionary keys and provides defaults."""
    aid = str(data["id"]).strip().lower()
    name = str(data.get("name", aid.title())).strip()
    role = str(data.get("role", "Specialist Agent")).strip()
    
    spec = data.get("specialization", "")
    if isinstance(spec, (list, tuple)):
        spec = " ".join(str(s) for s in spec)
    spec = str(spec).strip()
    
    url = str(data.get("official_url", "https://google.com")).strip()
    is_leader = bool(data.get("is_leader", False))
    routing_tag = str(data.get("routing_tag", f"[SEND_TO: {aid}]")).strip()
    
    return {
        "id": aid,
        "name": name,
        "role": role,
        "specialization": spec,
        "official_url": url,
        "is_leader": is_leader,
        "routing_tag": routing_tag,
        "is_custom": True
    }


def add_custom_agent(agent_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Adds or updates a custom agent in persistent storage.
    If the agent is marked as leader, updates existing custom agents so only one leader is active.
    Returns (success, message).
    """
    valid, err = validate_agent_schema(agent_data)
    if not valid:
        return False, err
        
    normalized = normalize_agent_dict(agent_data)
    aid = normalized["id"]
    
    customs = load_custom_agents_from_disk()
    
    # If this custom agent is marked as leader, clear leader flag on other custom agents
    if normalized.get("is_leader"):
        for ca in customs:
            if ca["id"] != aid:
                ca["is_leader"] = False
                
    # Check if updating existing or adding new
    existing_idx = next((i for i, a in enumerate(customs) if a["id"] == aid), -1)
    if existing_idx >= 0:
        customs[existing_idx] = normalized
        msg = f"Custom agent '{normalized['name']}' ({aid}) updated successfully."
    else:
        customs.append(normalized)
        msg = f"Custom agent '{normalized['name']}' ({aid}) added successfully."
        
    if normalized.get("is_leader"):
        msg += " Set as Master Leader (Gemini moved to specialist list)."
        
    if save_custom_agents_to_disk(customs):
        reload_agents()
        return True, msg
    return False, "Failed to write custom agent to disk."


def remove_custom_agent(agent_id: str) -> Tuple[bool, str]:
    """Removes a custom agent from persistent storage."""
    aid = agent_id.strip().lower()
    
    # Prevent deletion of core default agents
    default_ids = [DEFAULT_LEAD_AGENT["id"]] + [a["id"] for a in DEFAULT_SPECIALIST_AGENTS]
    if aid in default_ids:
        return False, f"Cannot delete built-in default agent '{aid}'."
        
    customs = load_custom_agents_from_disk()
    filtered = [a for a in customs if a["id"] != aid]
    
    if len(filtered) == len(customs):
        return False, f"Custom agent '{aid}' not found."
        
    if save_custom_agents_to_disk(filtered):
        reload_agents()
        return True, f"Custom agent '{aid}' deleted successfully."
    return False, "Failed to update custom agents storage."


def get_leader() -> Dict[str, Any]:
    """Returns the leader agent controlling the hierarchy."""
    return LEAD_AGENT


def get_lead_agent() -> Dict[str, Any]:
    """Alias for get_leader() returning the active leader agent."""
    return LEAD_AGENT


def get_agent_by_id(agent_id: str) -> Optional[Dict[str, Any]]:
    """Fetch metadata and direct URL for a specific agent."""
    return ALL_AGENTS.get(agent_id, None)


def list_all_active_agents() -> List[Dict[str, Any]]:
    """Returns all available agents with leader prioritized first."""
    return [LEAD_AGENT] + [a for a in SPECIALIST_AGENTS if a["id"] != LEAD_AGENT["id"]]


def list_custom_agents() -> List[Dict[str, Any]]:
    """Returns all custom user-defined agents."""
    return load_custom_agents_from_disk()


# Initialize state on module load
reload_agents()
