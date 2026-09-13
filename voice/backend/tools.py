"""
tools.py - Instant Tool Calling Definitions for Gemini Orchestrator Live Voice.

In Gemini Live API, tool calls are synchronous: the model's voice stream pauses
until the tool returns. Therefore, all handlers do non-blocking work and return
INSTANTLY so the voice conversation never stalls.
"""
import sys
import os
import subprocess
import json
import logging
from pathlib import Path

# Add project root to sys.path so we can import orchestrator modules
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

log = logging.getLogger("voice-tools")

# Live Tool Declarations in Google GenAI dict format
TOOL_DECLARATIONS = [
    {
        "name": "dispatch_mission",
        "description": "Dispatch an autonomous multi-agent task or engineering mission to the specialist agent squad (DeepSeek, ChatGPT, Claude, etc.). Executes asynchronously in the background.",
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "The full detailed prompt and objective for the mission."
                },
                "specialist_agents": {
                    "type": "string",
                    "description": "Optional comma-separated list of agent IDs to assign (e.g. 'deepseek,chatgpt' or 'auto')."
                }
            },
            "required": ["task"]
        }
    },
    {
        "name": "check_agent_status",
        "description": "Check the real-time operational status (FREE, BUSY, LEADER) and current assignments of all agents in the pool.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "query_orchestrator_memory",
        "description": "Retrieve relevant long-term memories, architecture directives, or past mission learnings from neural storage.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query or topic to look up in memory."
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_available_agents",
        "description": "List all active specialist agents currently available in the multi-agent roster along with their specializations.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "play_youtube_music",
        "description": "Open YouTube / YouTube Music and play any requested song, artist, album, genre, or video.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The song title, artist, mood, or search terms to play (e.g. 'lofi hip hop radio', 'daft punk get lucky', 'relaxing piano music')."
                }
            },
            "required": ["query"]
        }
    }
]


def _launch_agent_mission_background(task: str, agents_str: str = ""):
    """Spawns the mission asynchronously via main.py or launcher."""
    try:
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--task", task]
            if agents_str:
                cmd.extend(["--agents", agents_str])
        elif (ROOT_DIR / "launcher.py").exists():
            cmd = [sys.executable, str(ROOT_DIR / "launcher.py"), "--task", task]
            if agents_str:
                cmd.extend(["--agents", agents_str])
        else:
            # Fallback inline python runner
            code = (
                f"import asyncio, sys; from core.main import run_agent_loop; "
                f"asyncio.run(run_agent_loop({repr(task)}))"
            )
            cmd = [sys.executable, "-c", code]

        subprocess.Popen(
            cmd,
            cwd=str(ROOT_DIR),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        )
        log.info("Successfully launched background mission: %s", task[:50])
    except Exception as e:
        log.error("Failed to spawn background mission: %s", e)



def dispatch_tool(name: str, args: dict):
    """
    Executes the tool handler instantly and returns (command_dict | None, result_dict).
    The result_dict is immediately returned to Gemini Live session.
    """
    log.info("Tool called: %s with args: %s", name, args)

    if name == "dispatch_mission":
        task = args.get("task", "").strip()
        agents = args.get("specialist_agents", "auto")
        if task:
            _launch_agent_mission_background(task, agents)
            return (
                {"action": "mission_started", "task": task, "agents": agents},
                {"status": "ok", "message": f"Mission '{task[:40]}' dispatched to specialist agents."}
            )
        return None, {"status": "error", "message": "Task description cannot be empty."}

    elif name == "check_agent_status":
        try:
            from core import agent_status
            status_data = agent_status.get_all_agent_status()
            summary = {k: v.get("state", "UNKNOWN") for k, v in status_data.items()}
            return (
                {"action": "status_check", "data": summary},
                {"status": "ok", "agents_status": summary}
            )
        except Exception as e:
            return None, {"status": "error", "message": str(e)}

    elif name == "query_orchestrator_memory":
        query = args.get("query", "")
        try:
            from utils.enhanced_memory import get_relevant_memories_for_task
            memories = get_relevant_memories_for_task(query, max_items=4)
            return (
                {"action": "memory_retrieved", "query": query},
                {"status": "ok", "memories": memories or "No specific prior memory recorded for this topic."}
            )
        except Exception as e:
            return None, {"status": "error", "message": str(e)}

    elif name == "list_available_agents":
        try:
            from core import agentlist
            agents = agentlist.list_all_active_agents()
            roster = [{"id": a["id"], "name": a["name"], "role": a["role"]} for a in agents]
            return (
                {"action": "roster_listed", "count": len(roster)},
                {"status": "ok", "roster": roster}
            )
        except Exception as e:
            return None, {"status": "error", "message": str(e)}

    elif name == "play_youtube_music":
        query = args.get("query", "").strip()
        if query:
            import urllib.parse
            import webbrowser
            encoded_query = urllib.parse.quote(query)
            yt_url = f"https://www.youtube.com/results?search_query={encoded_query}"
            try:
                webbrowser.open(yt_url)
                log.info("Opening YouTube music for query: %s -> %s", query, yt_url)
            except Exception as ex:
                log.error("Error opening YouTube: %s", ex)

            return (
                {"action": "youtube_playing", "query": query, "url": yt_url},
                {"status": "ok", "message": f"Opening YouTube and playing {query}."}
            )
        return None, {"status": "error", "message": "Music query cannot be empty."}

    return None, {"status": "unknown_tool", "message": f"Tool '{name}' is not recognized."}
