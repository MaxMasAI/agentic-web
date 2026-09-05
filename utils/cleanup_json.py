"""
cleanup_json.py - Cleans up old redundant JSON files from tasks/ and root.
"""
import os

legacy_files = [
    "mcp_config.json",
    os.path.join("tasks", "memory.json"),
    os.path.join("tasks", "subagents.json"),
    os.path.join("tasks", "agent_status.json"),
    os.path.join("tasks", "tracked_pids.json")
]

for f in legacy_files:
    if os.path.exists(f):
        try:
            os.remove(f)
            print(f"Removed legacy: {f}")
        except Exception:
            pass
