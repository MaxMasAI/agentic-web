"""
agentlist.py - AI Agent Directory & Metadata
Configured for multi-agent browser and workflow automation.
Gemini acts as the Master Orchestrator / Lead Agent.
"""

from typing import Dict, Any, List

# Master Leader / Orchestrator Agent
LEAD_AGENT: Dict[str, Any] = {
    "id": "gemini",
    "name": "Google Gemini",
    "role": "Master Orchestrator & Leadership Lead",
    "specialization": (
        "Project orchestration, multimodal asset evaluation, strict design quality audits, "
        "repetition filtering, prompt engineering refinement, and workflow direction."
    ),
    "official_url": "https://gemini.google.com/app",
    "is_leader": True,
    "routing_tag": "[SEND_TO: gemini]"
}

# Subordinate Specialist Agents
SPECIALIST_AGENTS: List[Dict[str, Any]] = [
    {
        "id": "deepseek",
        "name": "DeepSeek",
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
        "role": "European Multilingual & Open-Weights Specialist",
        "specialization": (
            "Fluent translation across multiple European languages, light-weight utility scripts coding, "
            "and cost-effective task delegation."
        ),
        "official_url": "https://chat.mistral.ai",
        "is_leader": False,
        "routing_tag": "[SEND_TO: mistral]"
    }
]

# Combined Lookup Registry
ALL_AGENTS: Dict[str, Dict[str, Any]] = {
    LEAD_AGENT["id"]: LEAD_AGENT,
    **{agent["id"]: agent for agent in SPECIALIST_AGENTS}
}

# Helper Functions
def get_leader() -> Dict[str, Any]:
    """Returns the leader agent controlling the hierarchy."""
    return LEAD_AGENT

def get_agent_by_id(agent_id: str) -> Dict[str, Any]:
    """Fetch metadata and direct URL for a specific agent."""
    return ALL_AGENTS.get(agent_id, None)

def list_all_active_agents() -> List[Dict[str, Any]]:
    """Returns all available agents with leader prioritized first."""
    return [LEAD_AGENT] + SPECIALIST_AGENTS
