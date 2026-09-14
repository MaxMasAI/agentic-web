"""
main.py - Unified Entry Point for CLI & Terminal Multi-Agent Orchestrator.
For GUI Desktop Application, launch via 'python app.py' or 'run.bat'.
"""

import sys
import os

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Install Autonomous GitHub Crash & Issue Reporter
try:
    from system.issue_reporter import install_crash_reporter
    install_crash_reporter()
except Exception as e:
    pass

if __name__ == "__main__":
    if "--watch" in sys.argv or "--dev" in sys.argv or "--auto-restart" in sys.argv:
        import dev
        filtered_args = [a for a in sys.argv[1:] if a not in ("--watch", "--dev", "--auto-restart")]
        if not dev.run_watchdog_cli([sys.executable, "main.py"] + filtered_args):
            dev.run_python_watcher(["main.py"] + filtered_args)
        sys.exit(0)

    if "--gui" in sys.argv:
        import app
        app.main()
    else:
        from core.main import run_agent_loop, launch_voice_mode
        import core.main
        # Re-execute core main logic
        if "--voice" in sys.argv or "-v" in sys.argv:
            launch_voice_mode()
            sys.exit(0)

        if "--voice-server" in sys.argv:
            import uvicorn
            print("\033[96m[*] Starting Gemini Live Voice Server on ws://127.0.0.1:8000/ws...\033[0m")
            uvicorn.run("voice.backend.server:app", host="127.0.0.1", port=8000)
            sys.exit(0)

        # Fallback to interactive CLI loop in core.main
        import asyncio
        from core import agentlist

        print("\n\033[96m" + "=" * 60)
        print("   LEADER-WORKER MULTI-AI COLLABORATIVE SYSTEM (CLI)   ")
        print("   [For Desktop GUI: run 'python app.py' or 'run.bat']   ")
        print("=" * 60 + "\033[0m")

        active_agents = agentlist.list_all_active_agents()
        print("\033[93mAvailable Agents & Specializations:\033[0m")
        for i, agent in enumerate(active_agents, 1):
            role_desc = "Leader" if agent["is_leader"] else "Worker"
            spec = agent["specialization"][:70] + "..." if len(agent["specialization"]) > 70 else agent["specialization"]
            print(f"  \033[96m{i}. {agent['name']} ({role_desc}) \033[0m- {spec}")

        while True:
            num_agents_input = input(f"\n\033[93mEnter number of agents (default: auto, 'gui', 'voice', or 'exit'): \033[0m").strip()
            if num_agents_input.lower() in ["exit", "quit"]:
                print("\033[93m[*] Exiting pipeline. Goodbye!\033[0m")
                break

            if num_agents_input.lower() == "gui":
                import app
                app.main()
                break

            if num_agents_input.lower() in ["voice", "v"]:
                launch_voice_mode()
                continue

            selected_agents_override = None
            if num_agents_input and num_agents_input.lower() != "auto":
                try:
                    parsed = int(num_agents_input)
                    if 2 <= parsed <= len(active_agents):
                        selected_agents_override = active_agents[:parsed]
                    else:
                        print(f"\033[91m[!] Invalid count. Please choose between 2 and {len(active_agents)}.\033[0m")
                        continue
                except ValueError:
                    print("\033[91m[!] Please enter a valid number, 'auto', 'gui', or 'voice'.\033[0m")
                    continue

            task = input("\033[93mEnter the task you want the AI pipeline to perform: \033[0m").strip()
            if not task:
                continue

            try:
                asyncio.run(run_agent_loop(task, selected_agents_override))
            except KeyboardInterrupt:
                print("\n\033[91m[!] Task execution interrupted by user.\033[0m")
            except Exception as e:
                print(f"\n\033[91m[!] Error running task: {e}\033[0m")
