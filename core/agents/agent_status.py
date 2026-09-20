"""
agent_status.py - Real-Time Multi-Agent State & Work Dispatch Tracker
Maintains live state (FREE, BUSY, LEADER) and current task assignments
for all agents in the pool, shared with the desktop console.
"""

import os
import json
import time

STATUS_FILE = os.path.join("json", "agent_status.json")

def init_agent_status(all_agents):
    """Initializes all agents in the pool to FREE/IDLE status."""
    os.makedirs("tasks", exist_ok=True)
    status_data = {}
    for a in all_agents:
        is_leader = a.get("is_leader", False)
        status_data[a["id"]] = {
            "id": a["id"],
            "name": a["name"],
            "role": a["role"],
            "specialization": a.get("specialization", ""),
            "state": "LEADER" if is_leader else "FREE",
            "current_task": "Master Orchestrator" if is_leader else "Idle - Ready for assignment",
            "last_updated": time.strftime("%H:%M:%S")
        }

    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def set_agent_state(agent_id: str, state: str, current_task: str = ""):
    """
    Updates the live status of an agent.
    state: "FREE", "BUSY", "LEADER", or "REVIEWING"
    """
    try:
        if not os.path.exists(STATUS_FILE):
            return

        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if agent_id in data:
            data[agent_id]["state"] = state
            if current_task:
                data[agent_id]["current_task"] = current_task
            elif state == "FREE":
                data[agent_id]["current_task"] = "Idle - Ready for assignment"
            data[agent_id]["last_updated"] = time.strftime("%H:%M:%S")

            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def reset_all_workers_to_free(all_agents):
    """Resets all worker agents back to FREE state once tasks complete."""
    init_agent_status(all_agents)


def get_all_agent_status() -> dict:
    """Reads the current live status dictionary for all agents."""
    if not os.path.exists(STATUS_FILE):
        return {}
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
