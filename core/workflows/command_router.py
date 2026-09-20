"""
core/command_router.py - Universal Slash Command & Direct Task Router.
Parses multi-agent slash syntax like '/{names} - {task}', '/all - {task}', '/{cmd}'
and provides rich routing metadata for immediate execution and task delegation.
"""

import re
from typing import Dict, Any, List, Optional, Tuple

# Agent aliases mapping
AGENT_ALIASES: Dict[str, str] = {
    "gemini": "gemini", "google": "gemini", "lead": "gemini", "leader": "gemini",
    "deepseek": "deepseek", "ds": "deepseek", "reasoner": "deepseek",
    "chatgpt": "chatgpt", "gpt": "chatgpt", "gpt4": "chatgpt", "openai": "chatgpt",
    "claude": "claude", "anthropic": "claude", "sonnet": "claude",
    "meta": "meta_ai", "meta_ai": "meta_ai", "llama": "meta_ai",
    "dalle": "dalle", "dalle3": "dalle", "image": "dalle", "draw": "dalle",
    "perplexity": "perplexity", "sonar": "perplexity", "search": "perplexity",
    "copilot": "copilot", "ms": "copilot", "microsoft": "copilot", "office": "copilot",
    "nvidia": "nvidia_ai", "nvidia_ai": "nvidia_ai", "nim": "nvidia_ai", "gpu": "nvidia_ai",
    "mistral": "mistral", "lechat": "mistral",
    "web": "web_agent", "web_agent": "web_agent", "browser": "web_agent",
    "qwen": "qwen_coder", "qwen_coder": "qwen_coder", "coder": "qwen_coder",
    "system": "system", "sys": "system", "os": "system", "host": "system",
    "all": "all", "squad": "all", "everyone": "all", "team": "all"
}


def resolve_agent_id(raw_name: str) -> str:
    """Normalizes an agent name or alias to its canonical agent ID."""
    clean = re.sub(r"[^a-zA-Z0-9_-]", "", raw_name.strip().lower())
    return AGENT_ALIASES.get(clean, clean)


def parse_slash_task_command(input_text: str) -> Dict[str, Any]:
    """
    Parses an input string from text areas.
    
    Supported formats:
    - "/deepseek - build a landing page"
    - "/claude,chatgpt - review security"
    - "/all - full analysis across all specialists"
    - "/system - open notepad" or "/os - calc"
    - "/reset" (resets pool states to FREE)
    - "/help" (returns command help cheatsheet)
    - "regular task description" (routes with agents="auto")
    """
    text = (input_text or "").strip()
    if not text:
        return {"type": "empty", "task": "", "agents": "auto", "raw": text}

    # 1. Direct standalone slash commands
    if text.lower() in ("/reset", "/clear", "/reset-agents"):
        return {"type": "reset", "task": "", "agents": "all", "raw": text}

    if text.lower() in ("/help", "/?", "/commands"):
        return {"type": "help", "task": "", "agents": "auto", "raw": text}

    if text.lower().startswith(("/inspect ", "/info ")):
        parts = text.split(" ", 1)
        target = parts[1].strip() if len(parts) > 1 else "gemini"
        resolved = resolve_agent_id(target)
        return {"type": "inspect", "target_agent": resolved, "task": "", "agents": resolved, "raw": text}

    # 2. Match "/{names} - {task}" or "/{names} : {task}" or "/{names} {task}"
    slash_match = re.match(r"^/([a-zA-Z0-9_,\-\s]+?)(?:\s*[-:]\s*|\s+)(.+)$", text, re.DOTALL)
    if slash_match:
        raw_agents = slash_match.group(1).strip()
        task_body = slash_match.group(2).strip()

        # Split multiple comma or space separated agents
        agent_tokens = re.split(r"[,;]\s*|\s+", raw_agents)
        resolved_agents: List[str] = []
        for token in agent_tokens:
            if not token:
                continue
            aid = resolve_agent_id(token)
            if aid and aid not in resolved_agents:
                resolved_agents.append(aid)

        if "all" in resolved_agents:
            agents_str = "all"
        elif resolved_agents:
            agents_str = ",".join(resolved_agents)
        else:
            agents_str = "auto"

        # Check if targeting system command execution
        if agents_str == "system":
            return {
                "type": "system_exec",
                "task": task_body,
                "agents": "system",
                "resolved_list": ["system"],
                "raw": text
            }

        return {
            "type": "dispatch",
            "task": task_body,
            "agents": agents_str,
            "resolved_list": resolved_agents,
            "raw": text
        }

    # 3. Default fallback: Regular task dispatched to leader & auto specialists
    return {
        "type": "dispatch",
        "task": text,
        "agents": "auto",
        "resolved_list": [],
        "raw": text
    }
