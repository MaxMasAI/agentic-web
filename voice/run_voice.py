"""
run_voice.py - Direct Launcher for Gemini Live Voice Orchestrator.
Directly starts the live voice backend on port 8000 without any parser flags.
"""
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn


def free_port(port: int = 8000):
    """Kills any previous hanging process listening on the port to prevent WinError 10048."""
    try:
        import subprocess, os
        output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True, text=True)
        for line in output.strip().splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                pid = int(parts[-1])
                if pid != os.getpid() and pid > 0:
                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def main():
    free_port(8000)
    print("\n=======================================================")
    print("  Starting Gemini Orchestrator Live Voice Backend")
    print("  Endpoint: ws://127.0.0.1:8000/ws")
    print("  Health:   http://127.0.0.1:8000/health")
    print("=======================================================\n")

    uvicorn.run(
        "voice.backend.server:app",
        host="127.0.0.1",
        port=8000
    )


if __name__ == "__main__":
    main()
