"""
launcher.py - CLI wrapper for run_agent_loop.
Called by the desktop mission control console to launch pipeline tasks.

Usage:
    python -u launcher.py --task "Write a poem" --agents "auto"
"""

import asyncio
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(description="Launch a multi-agent pipeline task.")
    parser.add_argument("--task", type=str, required=True, help="The task to execute.")
    parser.add_argument(
        "--agents", type=str, required=False, default="auto",
        help="Comma-separated agent IDs to use (e.g. 'gemini,deepseek,chatgpt'), or 'auto'."
    )
    args = parser.parse_args()

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from core import agentlist
    all_agents = agentlist.list_all_active_agents()

    if args.agents.lower() == "auto":
        selected = None  # triggers Gemini auto-selection
    else:
        ids = [a.strip().lower() for a in args.agents.split(",")]
        selected = []
        for aid in ids:
            agent = agentlist.get_agent_by_id(aid)
            if agent:
                selected.append(agent)
        if not selected:
            print("[!] No valid agent IDs found. Using auto selection.", flush=True)
            selected = None

    from core.main import run_agent_loop
    from utils.logger import close_logging

    print(f"[*] Task Received: '{args.task}'", flush=True)
    print(f"[*] Agent Selection: {args.agents}", flush=True)
    
    try:
        asyncio.run(run_agent_loop(args.task, selected))
        print("[*] Task execution completed successfully.", flush=True)
    except Exception as e:
        print(f"[!] Error executing task: {e}", flush=True)
    finally:
        close_logging()

if __name__ == "__main__":
    main()
