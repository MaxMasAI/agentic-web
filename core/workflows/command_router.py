"""
core/command_router.py - Universal Slash Command & Direct Task Router.
Parses multi-agent slash syntax like '/{names} - {task}', internal tool control commands,
and provides rich routing metadata for immediate execution and autonomous agent tool use.
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
    "system": "system", "sys": "system", "os": "system", "host": "system", "exec": "system", "run": "system",
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
    - Internal tool slash commands:
      * "/mcp <tool_name> [args]" or "/mcp"
      * "/memory <search|add> <content>"
      * "/file <read|write|list|search> <path> [content]"
      * "/wiki <query>" or "/search <query>" or "/browser <url>"
      * "/harness <task>"
      * "/tokens", "/canvas", "/vscode", "/code", "/notepad", "/painter", "/scheduler"
    - Agent & squad syntax:
      * "/deepseek - build a landing page"
      * "/claude,chatgpt - review security"
      * "/all - full analysis across all specialists"
      * "/system - open notepad" or "/os - calc"
    - System state commands:
      * "/reset" (resets pool states to FREE)
      * "/help" (returns command help cheatsheet)
    - Natural language query (routes with agents="auto" + autonomous tool detection)
    """
    text = (input_text or "").strip()
    if not text:
        return {"type": "empty", "task": "", "agents": "auto", "raw": text}

    lower_text = text.lower()

    # 1. Direct standalone slash navigation & state commands
    if lower_text in ("/reset", "/clear", "/reset-agents"):
        return {"type": "reset", "task": "", "agents": "all", "raw": text}

    if lower_text in ("/help", "/?", "/commands"):
        return {"type": "help", "task": "", "agents": "auto", "raw": text}

    # Instant Page Navigations
    nav_map = {
        "/tokens": "tokens", "/token": "tokens",
        "/canvas": "canvas_dev", "/canvas_dev": "canvas_dev",
        "/vscode": "vscode", "/code": "vscode",
        "/notepad": "notepad", "/notes": "notepad",
        "/painter": "painter", "/draw": "painter",
        "/scheduler": "scheduler", "/cron": "scheduler",
        "/mcp": "mcp", "/mcp_hub": "mcp",
        "/memory_page": "memory", "/memories": "memory",
        "/harness_page": "harness"
    }
    if lower_text in nav_map:
        return {"type": "navigate", "target_page": nav_map[lower_text], "task": "", "agents": "system", "raw": text}

    # 2. Internal Tool Slash Commands
    # /mcp <tool_name> [args]
    if lower_text.startswith(("/mcp ", "/mcptool ")):
        body = text.split(" ", 1)[1].strip() if " " in text else ""
        parts = body.split(" ", 1)
        tool_name = parts[0]
        tool_args = parts[1] if len(parts) > 1 else "{}"
        return {
            "type": "mcp_tool",
            "tool_name": tool_name,
            "tool_args": tool_args,
            "task": body,
            "agents": "system",
            "raw": text
        }

    # /memory <search|add> <content>
    if lower_text.startswith(("/memory ", "/mem ")):
        body = text.split(" ", 1)[1].strip() if " " in text else ""
        action = "search"
        query_text = body
        if body.lower().startswith(("search ", "find ", "query ")):
            action = "search"
            query_text = body.split(" ", 1)[1].strip()
        elif body.lower().startswith(("add ", "save ", "store ", "record ")):
            action = "add"
            query_text = body.split(" ", 1)[1].strip()
        return {
            "type": "memory_tool",
            "action": action,
            "query": query_text,
            "task": body,
            "agents": "system",
            "raw": text
        }

    # /file <read|write|list|search> <path> [content]
    if lower_text.startswith(("/file ", "/read ", "/cat ", "/write ")):
        body = text.split(" ", 1)[1].strip() if " " in text else ""
        if lower_text.startswith(("/read ", "/cat ")):
            op = "read"
            path = body
            content = ""
        elif lower_text.startswith("/write "):
            op = "write"
            parts = body.split(" ", 1)
            path = parts[0]
            content = parts[1] if len(parts) > 1 else ""
        else:
            parts = body.split(" ", 2)
            op = parts[0] if len(parts) > 0 else "read"
            path = parts[1] if len(parts) > 1 else "."
            content = parts[2] if len(parts) > 2 else ""
        return {
            "type": "file_tool",
            "operation": op,
            "path": path,
            "content": content,
            "task": body,
            "agents": "system",
            "raw": text
        }

    # /wiki <query>
    if lower_text.startswith(("/wiki ", "/wikipedia ")):
        q = text.split(" ", 1)[1].strip()
        return {
            "type": "wiki_tool",
            "query": q,
            "task": q,
            "agents": "system",
            "raw": text
        }

    # /search <query> or /web <query> or /browser <url>
    if lower_text.startswith(("/search ", "/websearch ", "/bing ", "/google ")):
        q = text.split(" ", 1)[1].strip()
        return {
            "type": "web_tool",
            "query": q,
            "task": q,
            "agents": "perplexity",
            "raw": text
        }

    # /harness <task>
    if lower_text.startswith(("/harness ", "/eval ", "/cot ")):
        h_task = text.split(" ", 1)[1].strip()
        return {
            "type": "harness_tool",
            "task": h_task,
            "agents": "maxmasai_v3",
            "raw": text
        }

    # /inspect <agent>
    if lower_text.startswith(("/inspect ", "/info ")):
        parts = text.split(" ", 1)
        target = parts[1].strip() if len(parts) > 1 else "gemini"
        resolved = resolve_agent_id(target)
        return {"type": "inspect", "target_agent": resolved, "task": "", "agents": resolved, "raw": text}

    # 3. Match "/{names} - {task}" or "/{names} : {task}" or "/{names} {task}"
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

    # 4. Regular prompt with LAYA System 1 Decision Contract Analysis
    laya_meta = {}
    try:
        from core.laya_engine import LayaDecisionEngine
        engine = LayaDecisionEngine.get_instance()
        laya_res = engine.route_with_laya(text)
        laya_meta = laya_res.to_dict()
    except Exception:
        pass

    return {
        "type": "dispatch",
        "task": text,
        "agents": "auto",
        "resolved_list": [],
        "raw": text,
        "laya_decision": laya_meta
    }


def route_task_with_laya(input_text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Executes a high-throughput LAYA decision contract over the input task.
    Returns slash parsed metadata, sub-40ms System 1 decision contracts, and
    autonomous internal tool evaluation results.
    """
    cmd_info = parse_slash_task_command(input_text)
    
    # 1. Evaluate LAYA Decision Engine
    try:
        from core.laya_engine import LayaDecisionEngine
        engine = LayaDecisionEngine.get_instance()
        laya_res = engine.route_with_laya(input_text, context)
        cmd_info["laya_decision"] = laya_res.to_dict()
        cmd_info["laya_fast_path"] = laya_res.fast_path_eligible
        cmd_info["laya_recommended_specialist"] = laya_res.primary_choice
        cmd_info["laya_urgency"] = laya_res.urgency_tier
        cmd_info["laya_latency_ms"] = laya_res.latency_ms
    except Exception as e:
        cmd_info["laya_error"] = str(e)

    # 2. Autonomous Internal Tool Detection for natural language queries
    if cmd_info.get("type") == "dispatch":
        try:
            from core.internal_tool_executor import InternalToolExecutor
            tool_exec = InternalToolExecutor.get_instance()
            auto_res = tool_exec.detect_and_auto_execute_tools(input_text)
            if auto_res:
                cmd_info["auto_tool_result"] = auto_res
                cmd_info["auto_tool_name"] = auto_res.get("tool", "internal_tool")
        except Exception:
            pass

    return cmd_info


def split_multi_task_prompt(input_text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Parses a single compound prompt and decomposes it into multiple individual tasks.
    Supports:
    1. Multiple slash commands: '/deepseek - task 1\n/claude - task 2' or '/deepseek - t1 ; /claude - t2'
    2. Numbered / bulleted tasks: '1. Scrape data\n2. Clean data\n3. Visualize data'
    3. 'Task 1: ... Task 2: ...' patterns
    4. Semicolon / '&&' separated multi-action instructions
    Returns a list of routed task dictionaries ready for parallel or sequential dispatch.
    """
    raw_text = (input_text or "").strip()
    if not raw_text:
        return [route_task_with_laya(raw_text, context)]

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

    # Case A: Multiple lines where multiple lines start with a slash command
    slash_lines = [l for l in lines if l.startswith("/")]
    if len(slash_lines) >= 2 and len(slash_lines) == len(lines):
        tasks = []
        for l in slash_lines:
            sub_res = route_task_with_laya(l, context)
            if sub_res.get("type") != "empty":
                tasks.append(sub_res)
        if tasks:
            return tasks

    # Case B: Semicolon or && separated slash commands on a single line: '/deepseek - t1 ; /claude - t2'
    if ";" in raw_text or "&&" in raw_text:
        delimiter = ";" if ";" in raw_text else "&&"
        segments = [s.strip() for s in raw_text.split(delimiter) if s.strip()]
        if len(segments) >= 2 and any(s.startswith("/") for s in segments):
            tasks = []
            for s in segments:
                sub_res = route_task_with_laya(s, context)
                if sub_res.get("type") != "empty":
                    tasks.append(sub_res)
            if tasks:
                return tasks

    # Case C: Numbered list items or bullet points (e.g. '1. ...', '2. ...', '- ...', 'Task 1: ...')
    item_pattern = re.compile(r"^\s*(?:(?:\d+|[a-zA-Z])[\.\)]|\-|\*|Task\s+\d+[:\.\-])\s*(.+)$", re.IGNORECASE)
    numbered_items = []
    for line in lines:
        m = item_pattern.match(line)
        if m:
            item_text = m.group(1).strip()
            if item_text:
                numbered_items.append(item_text)

    if len(numbered_items) >= 2:
        tasks = []
        for idx, item in enumerate(numbered_items, 1):
            sub_res = route_task_with_laya(item, context)
            sub_res["subtask_index"] = idx
            sub_res["total_subtasks"] = len(numbered_items)
            tasks.append(sub_res)
        return tasks

    # Fallback: Single Task
    single_res = route_task_with_laya(raw_text, context)
    return [single_res]
