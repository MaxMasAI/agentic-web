"""
core.agents - Agent Ecosystem, Registry, Status, Skills & Discussion Modules
"""

from core.agents import agents
from core.agents import agentlist
from core.agents import agent_status
from core.agents import agent_skills_router
from core.agents import squad_learner
from core.agents import discussion
from core.agents import experts_manager

# Re-export key functions from agents
from core.agents.agents import (
    talk_to_agent,
    AGENT_SELECTORS,
)

from core.agents.agentlist import (
    get_leader,
    get_lead_agent,
    get_agent_by_id,
    list_all_active_agents,
    list_custom_agents,
    add_custom_agent,
    remove_custom_agent,
    reload_agents,
    parse_agent_text_format,
    validate_agent_schema,
    normalize_agent_dict,
)
from core.agents.agent_status import (
    init_agent_status,
    set_agent_state,
    reset_all_workers_to_free,
    get_all_agent_status,
)
from core.agents.agent_skills_router import (
    get_agent_skills_directive,
    AGENT_SKILLS_MAP,
    SUPERPOWERS_SKILLS_MAP,
)
from core.agents.squad_learner import (
    detect_and_create_repeated_pattern_squads,
    load_subagents,
    save_subagents,
)
from core.agents.discussion import (
    run_discussion_round,
)
from core.agents.experts_manager import (
    ExpertsManager,
    ExpertContext,
    get_experts_manager,
)

__all__ = [
    "agents",
    "agentlist",
    "agent_status",
    "agent_skills_router",
    "squad_learner",
    "discussion",
    "experts_manager",
    "talk_to_agent",
    "AGENT_SELECTORS",
    "get_leader",
    "get_lead_agent",
    "get_agent_by_id",
    "list_all_active_agents",
    "list_custom_agents",
    "add_custom_agent",
    "remove_custom_agent",
    "reload_agents",
    "parse_agent_text_format",
    "validate_agent_schema",
    "normalize_agent_dict",
    "init_agent_status",
    "set_agent_state",
    "reset_all_workers_to_free",
    "get_all_agent_status",
    "get_agent_skills_directive",
    "AGENT_SKILLS_MAP",
    "SUPERPOWERS_SKILLS_MAP",
    "detect_and_create_repeated_pattern_squads",
    "load_subagents",
    "save_subagents",
    "run_discussion_round",
    "ExpertsManager",
    "ExpertContext",
    "get_experts_manager",
]

