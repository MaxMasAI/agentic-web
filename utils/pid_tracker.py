"""
pid_tracker.py - Centralized Process Tree (PID / PPID) Queue Manager
Tracks browser process trees, persists PIDs to disk, hooks native Windows
Console Control Handlers (CTRL_CLOSE_EVENT), and cleanly terminates only
the tracked process tree when the main CMD terminal or process is killed.
"""

import os
import json
import subprocess
import atexit
import signal
import sys
import ctypes

TRACKED_FILE = os.path.join("json", "tracked_pids.json")

def _load_persisted_pids() -> list:
    if os.path.exists(TRACKED_FILE):
        try:
            with open(TRACKED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [int(p) for p in data if str(p).isdigit()]
        except Exception:
            pass
    return []

def _save_persisted_pids(pids: list):
    try:
        os.makedirs("tasks", exist_ok=True)
        with open(TRACKED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(set(pids)), f, indent=2)
    except Exception:
        pass

def find_pid_on_port(port: int = 9222) -> int:
    """Finds the process ID listening on a given TCP port using netstat."""
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, errors="ignore")
        for line in out.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                if len(parts) >= 5 and parts[-1].isdigit():
                    return int(parts[-1])
    except Exception:
        pass
    return None

def register_pid(pid: int):
    """Adds a PID to both in-memory and persistent disk tracking queue."""
    if pid and isinstance(pid, int):
        pids = _load_persisted_pids()
        if pid not in pids:
            pids.append(pid)
            _save_persisted_pids(pids)
            print(f"[*] PID Tracker: Registered PID {pid} (Total tracked: {len(pids)})")

def get_tracked_pids() -> list:
    """Returns a list of all currently tracked PIDs from disk and memory."""
    pids = _load_persisted_pids()
    port_pid = find_pid_on_port(9222)
    if port_pid and port_pid not in pids:
        pids.append(port_pid)
    return pids

def kill_all_tracked_pids():
    """Terminates all registered process trees (/T) and clears the PID queue."""
    pids = get_tracked_pids()
    if not pids:
        return

    print(f"\n[*] Closing {len(pids)} tracked agent browser process tree(s)...")
    for pid in list(pids):
        try:
            # Kill process tree (/T) by PID (/PID) forcefully (/F)
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

    # Wipe persisted tracking queue
    _save_persisted_pids([])
    print(f"[OK] Process tree cleanup complete. Tracked PIDs terminated.")

# ──────────────────────────────────────────────
#  Native Windows Console Close & Signal Handlers
# ──────────────────────────────────────────────
def _win_ctrl_handler(ctrl_type: int) -> bool:
    """
    Handles Windows Console events:
    0 = CTRL_C_EVENT
    1 = CTRL_BREAK_EVENT
    2 = CTRL_CLOSE_EVENT (User clicked red 'X' on CMD)
    5 = CTRL_LOGOFF_EVENT
    6 = CTRL_SHUTDOWN_EVENT
    """
    kill_all_tracked_pids()
    return False

# Register Windows Kernel32 SetConsoleCtrlHandler only when running as standalone script
if __name__ == "__main__":
    kill_all_tracked_pids()

