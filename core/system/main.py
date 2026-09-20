import asyncio
import os
import json
import socket
import subprocess
import sys
import re
from playwright.async_api import async_playwright

import atexit
import signal

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.pid_tracker import register_pid, kill_all_tracked_pids, get_tracked_pids

# Force UTF-8 encoding on standard streams to avoid Windows charmap errors
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Initialize Virtual Terminal processing for Windows command prompt ANSI styling
os.system("")

import shutil

def find_pid_on_port(port=9222):
    """Finds the specific process ID listening on the remote debugging port."""
    try:
        output = subprocess.check_output(f'netstat -ano | findstr :{port}', shell=True, text=True)
        for line in output.strip().splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.strip().split()
                return int(parts[-1])
    except Exception:
        pass
    return None

def find_browser_executable() -> str:
    """Finds installed Google Chrome or Microsoft Edge executable on the system."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
            
    which_chrome = shutil.which("chrome") or shutil.which("google-chrome") or shutil.which("msedge")
    if which_chrome:
        return which_chrome

    return r"C:\Program Files\Google\Chrome\Application\chrome.exe"


# ANSI Color Codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Import our split modules
from browser.browser_helpers import get_or_open_tab
from core.agents import talk_to_agent
from utils.dashboard import generate_dashboard
from browser.downloader import make_task_folder, setup_download_handler, try_download_images
from core.discussion import run_discussion_round
from utils.logger import setup_logging, close_logging, log_path
from core.agent_status import init_agent_status, set_agent_state, reset_all_workers_to_free
from core.agent_skills_router import get_agent_skills_directive
from core import agentlist

# Import Voice Narrator for real-time spoken commentary throughout the task flow
try:
    from voice.voice_narrator import speak_narrator
except Exception:
    def speak_narrator(text: str, non_blocking: bool = True): pass

async def run_agent_loop(task, selected_agents_override=None):
    os.makedirs("visuals", exist_ok=True)
    from core import agentlist
    all_available_agents = agentlist.list_all_active_agents()
    init_agent_status(all_available_agents)

    # Gemini Voice Announcement: Mission Start
    speak_narrator(f"Mission initiated: {task[:60]}")

    # Set up logging — all prints go to terminal AND logs/ file
    import re as _re
    slug = _re.sub(r"[^\w\s-]", "", task).strip().replace(" ", "_")[:40]
    lp = setup_logging(slug)
    print(f"{CYAN}[OK] Logging to: {lp}{RESET}")

    # Clean up previous runs' screenshots if they exist
    for f in os.listdir("visuals"):
        if f.startswith("step_") and f.endswith(".png"):
            try:
                os.remove(os.path.join("visuals", f))
            except Exception:
                pass

    # Load memory from json/memory.json
    memory_file = "json/memory.json"
    existing_memories = []
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                existing_memories = json.load(f)
            print(f"{GREEN}[OK] Memory loaded: {len(existing_memories)} items found.{RESET}")
        except Exception:
            pass

    # ── Direct Native Windows System Application Launcher ──
    try:
        from services.system_app_launcher import is_system_app_task, execute_system_app_launch
        if is_system_app_task(task):
            deliverable = execute_system_app_launch(task)
            print(f"\n{GREEN}" + "=" * 60)
            print(f"{BOLD}       SYSTEM APPLICATION LAUNCHED SUCCESSFULLY       ")
            print("=" * 60 + f"{RESET}")
            print(f"\n{deliverable}\n")
            print(f"{GREEN}" + "=" * 60 + f"{RESET}")
            reset_all_workers_to_free(all_available_agents)
            return
    except Exception as e:
        print(f"{YELLOW}[*] System launcher check notice: {e}{RESET}")

    async with async_playwright() as p:
        # Start Chrome on port 9222 if not running
        chrome_running = False
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2.0)  # Socket timeout to prevent hang
                s.connect(("127.0.0.1", 9222))
                pid_found = find_pid_on_port(9222)
                if pid_found:
                    register_pid(pid_found)
                chrome_running = True
                print(f"{GREEN}[OK] Chrome already running on port 9222.{RESET}")
        except Exception:
            pass

        if not chrome_running:
            browser_bin = find_browser_executable()
            print(f"{YELLOW}[*] Launching browser ({browser_bin}) with remote debugging on port 9222...{RESET}")
            chrome_cmd = [
                browser_bin,
                "--remote-debugging-port=9222",
                r"--user-data-dir=C:\ChromeAgentProfile",
                "--disable-popup-blocking",          # Allow all window.open() popups
                "--disable-infobars",                # No "Chrome is being controlled" bar
                "--disable-notifications",           # Block notification prompts
                "--no-first-run",                    # Skip first-run wizard
                "--disable-default-apps",
            ]
            try:
                proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                register_pid(proc.pid)
            except Exception as e:
                print(f"{RED}[!] Failed to launch browser process: {e}{RESET}")
            await asyncio.sleep(2)  # Initial wait for browser process to spin up

        # Attach to the running Chrome instance on port 9222 with retry resilience
        browser = None
        for cdp_attempt in range(6):
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
                break
            except Exception as cdp_err:
                if cdp_attempt < 5:
                    print(f"{YELLOW}[*] Waiting for browser CDP endpoint on port 9222 (retry {cdp_attempt+1}/5)...{RESET}")
                    await asyncio.sleep(1.5)
                else:
                    raise cdp_err

        if not browser.contexts:
            context = await browser.new_context()
        else:
            context = browser.contexts[0]

        # ── Direct Autonomous Browser Action Handler (Any Website & YouTube Media) ──
        from browser.browser_controller import is_direct_browser_or_media_task, execute_direct_browser_action
        if is_direct_browser_or_media_task(task):
            deliverable = await execute_direct_browser_action(task, context)
            try:
                from services.tab_screenshot_service import capture_all_tabs_screenshots
                await capture_all_tabs_screenshots(context, output_dir="images")
            except Exception:
                pass
            print(f"\n{GREEN}" + "=" * 60)
            print(f"{BOLD}          DIRECT BROWSER ACTION COMPLETED          ")
            print("=" * 60 + f"{RESET}")
            print(f"\n{deliverable}\n")
            print(f"{GREEN}" + "=" * 60 + f"{RESET}")
            reset_all_workers_to_free(all_available_agents)
            return

        # Create task-named download folder and set up auto-download listener
        task_folder = make_task_folder(task)
        setup_download_handler(context, task_folder)

        # 1. Connect to Gemini Leader first (temporarily full screen; will be repositioned after agent count is known)
        print(f"{YELLOW}[*] Initializing Master Orchestrator (Gemini)...{RESET}")
        from core import agentlist
        gemini_tab = await get_or_open_tab(context, "gemini", "https://gemini.google.com/app")
        await gemini_tab.bring_to_front()
        try:
            from browser.agent_cursor import inject_agent_cursor, set_cursor_action
            await inject_agent_cursor(gemini_tab, agent_name="Gemini", agent_role="Leader & Orchestrator")
            await set_cursor_action(gemini_tab, "⚡ Evaluating Task & Selecting Squad...")
        except Exception:
            pass

        # 2. Determine worker agents dynamically if in "auto" mode
        selected_agents = []
        if selected_agents_override is None:
            print(f"\n{MAGENTA}[Gemini Leader] Evaluating task complexity & distributing workload (including self-assignment)...{RESET}")
            all_agents_pool = agentlist.list_all_active_agents()
            specialists_desc = ""
            for s in all_agents_pool:
                specialists_desc += f"- ID: '{s['id']}': {s['name']} ({s['role']}) - {s['specialization']}\n"
                
            selection_prompt = (
                "You are the Master Orchestrator (Gemini). A user wants to execute this task:\n"
                f"'{task}'\n\n"
                "Evaluate the task complexity and select the executing agents. You can assign tasks to YOURSELF ('gemini') as well as to your specialist agents:\n"
                "• EASY / FOCUSED TASK (single domain or direct execution):\n"
                "  -> Assign to EXACTLY 1 agent best suited for it (can be 'gemini' for direct self-execution, or 'deepseek', 'chatgpt', etc.).\n"
                "• COMPLEX / MULTI-DISCIPLINARY TASK:\n"
                "  -> Assign to 2 to 3 required agents to distribute the workload (can include 'gemini' and other specialists).\n\n"
                f"Available Agents Pool (including yourself):\n{specialists_desc}\n"
                "RULES:\n"
                "- If easy/direct: Output ONLY 1 agent ID (e.g. 'gemini' or 'deepseek' or 'chatgpt').\n"
                "- If complex: Output 2 to 3 comma-separated agent IDs (e.g. 'gemini,deepseek,chatgpt' or 'deepseek,claude').\n"
                "- Output ONLY the ID(s). Output absolutely nothing else."
            )
            selection_response = await talk_to_agent("gemini", gemini_tab, selection_prompt)
            
            # Robust regex scanner for known agent IDs
            selected_ids = []
            known_ids = ["deepseek", "claude", "chatgpt", "perplexity", "copilot", "mistral", "nvidia_ai", "meta_ai", "dalle", "gemini"]
            for kid in known_ids:
                if re.search(r"\b" + re.escape(kid) + r"\b", selection_response.lower()):
                    if kid not in selected_ids:
                        selected_ids.append(kid)
            
            # Cap at maximum 3 agents
            selected_ids = selected_ids[:3]
            
            # Resolve to active agent structures
            selected_agents = [agentlist.get_leader()]
            for aid in selected_ids:
                if aid != "gemini":
                    agent = agentlist.get_agent_by_id(aid)
                    if agent and agent not in selected_agents:
                        selected_agents.append(agent)
            
            # If Gemini failed to return any valid agent IDs at all, use task-based heuristic fallback
            if len(selected_ids) == 0:
                t_lower = task.lower()
                if any(w in t_lower for w in ["code", "build", "script", "app", "python", "fix", "bug", "implement", "develop", "plugin", "widget", "gui"]):
                    print(f"{YELLOW}[*] Software Engineering task: Enlisting DeepSeek (Build) and Claude (Review).{RESET}")
                    selected_agents.append(agentlist.get_agent_by_id("deepseek"))
                    selected_agents.append(agentlist.get_agent_by_id("claude"))
                elif any(w in t_lower for w in ["search", "find", "news", "research", "compare", "latest", "who", "what"]):
                    print(f"{YELLOW}[*] Deep Research task: Enlisting Perplexity and ChatGPT.{RESET}")
                    selected_agents.append(agentlist.get_agent_by_id("perplexity"))
                    selected_agents.append(agentlist.get_agent_by_id("chatgpt"))
                else:
                    print(f"{YELLOW}[*] Multi-Agent Collaborative task: Enlisting DeepSeek and ChatGPT.{RESET}")
                    selected_agents.append(agentlist.get_agent_by_id("deepseek"))
                    selected_agents.append(agentlist.get_agent_by_id("chatgpt"))
        else:
            selected_agents = selected_agents_override

        # Print the finalized agent loop
        print(f"\n{GREEN}[OK] Selected Multi-Agent Squad for this task:{RESET}")
        for idx, agent in enumerate(selected_agents, 1):
            role_tag = "Leader & Orchestrator" if agent["is_leader"] else f"Specialist Worker {idx-1}"
            print(f"  {idx}. {CYAN}{agent['name']} ({role_tag}){RESET}")

        # Gemini Voice Announcement: Delegation Strategy
        workers = selected_agents[1:] if len(selected_agents) > 1 else selected_agents
        worker_names = [a["name"] for a in workers]
        if len(selected_agents) == 1 and selected_agents[0]["id"] == "gemini":
            speak_narrator("Self-assignment active. Gemini will execute this task directly.")
        elif len(worker_names) == 1:
            speak_narrator(f"Task analyzed. Delegating to single specialist {worker_names[0]}.")
        elif len(worker_names) > 1:
            speak_narrator(f"Workload distributed across {len(worker_names)} specialists: {', '.join(worker_names)}.")

        # 3. Connect to all selected agents with FancyZones layout
        total_cols = len(selected_agents)
        try:
            from system.fancyzones_manager import get_fancyzones_layout
            from services.app_config import config
            fz_layout = config.get("fancyzones.layout", "auto")
            fz_spacing = int(config.get("fancyzones.spacing", 16))
            print(f"\n{YELLOW}[FancyZones] Snapping {total_cols} agent browser windows into '{fz_layout}' layout (spacing: {fz_spacing}px)...{RESET}")
        except Exception:
            print(f"\n{YELLOW}[*] Opening {total_cols} agent windows in equal-sized tiles...{RESET}")

        tabs = {}
        for col_idx, agent in enumerate(selected_agents):
            tab = await get_or_open_tab(
                context,
                agent["id"],
                agent["official_url"],
                col_index=col_idx,
                total_cols=total_cols
            )
            tabs[agent["id"]] = tab
            # Reassign gemini_tab to the correctly tiled version
            if agent["id"] == "gemini":
                gemini_tab = tab

            try:
                from browser.agent_cursor import inject_agent_cursor, set_cursor_action
                role_tag = "Leader & Orchestrator" if agent["is_leader"] else "Specialist Worker"
                status_chip = "⚡ Orchestrating Squad" if agent["is_leader"] else "⏳ In Queue"
                await inject_agent_cursor(tab, agent_name=agent["name"], agent_role=role_tag)
                await set_cursor_action(tab, status_chip)
            except Exception:
                pass

        # Explicitly snap all agent windows into side-by-side FancyZones with zero overlap
        from browser.browser_helpers import snap_all_agents_to_fancyzones
        await snap_all_agents_to_fancyzones(context, selected_agents)

        print(f"{GREEN}[OK] All active agent interfaces connected & snapped into FancyZones successfully.{RESET}")

        # Step 1: Gemini (Leader) Planning
        print(f"\n{MAGENTA}[Gemini Leader] Creating plan and delegating tasks...{RESET}")
        set_agent_state("gemini", "LEADER", f"Decomposing task & dispatching: {task[:35]}...")
        
        # Pop Gemini window in front with cursor badge
        try:
            from browser.agent_cursor import inject_agent_cursor, set_cursor_action
            await gemini_tab.bring_to_front()
            await inject_agent_cursor(gemini_tab, agent_name="Gemini", agent_role="Leader & Orchestrator")
            await set_cursor_action(gemini_tab, "⚡ Orchestrating & Planning...")
        except Exception:
            pass

        # Dynamic Semantic Neural Memory Retrieval
        from utils.enhanced_memory import get_relevant_memories_for_task, batch_add_from_mission
        memory_context = get_relevant_memories_for_task(task, max_items=10)
        if memory_context:
            memory_context = f"{memory_context}\n\nUse these persistent memories & user directives to guide your orchestration decisions.\n\n"

        # Get worker agent metadata (supports self-execution if Gemini is sole worker)
        workers = selected_agents[1:] if len(selected_agents) > 1 else selected_agents
        worker_descriptions = ""
        format_placeholders = ""
        for i, worker in enumerate(workers, 1):
            worker_descriptions += f"{i}. {worker['name']} (Agent ID: {worker['id']}): {worker['specialization']}\n"
            format_placeholders += f"--- {worker['name'].upper()} INSTRUCTION ---\n[Provide exact, detailed prompt for {worker['name']} here]\n"
            
        gemini_plan_prompt = (
            "You are the Leader and Orchestrator in an autonomous multi-agent system.\n"
            f"{get_agent_skills_directive('gemini')}"
            f"{memory_context}"
            f"The user wants to accomplish the following task: '{task}'\n\n"
            "Your job is to analyze this task and decompose it into sequential instructions for your worker agents:\n"
            f"{worker_descriptions}\n"
            "Output your plan in this exact format:\n"
            f"{format_placeholders}\n"
            "IMPORTANT: Your plan and all delegated instructions MUST be written entirely in English. "
            "Instruct all workers to write their responses ONLY in English."
        )
        
        gemini_plan = await talk_to_agent("gemini", gemini_tab, gemini_plan_prompt)
        await gemini_tab.screenshot(path="visuals/step_gemini_plan.png")
        set_agent_state("gemini", "LEADER", "Plan generated. Delegating subtasks.")

        try:
            from browser.agent_cursor import inject_agent_cursor, set_cursor_action
            await inject_agent_cursor(gemini_tab, agent_name="Gemini", agent_role="Leader & Orchestrator")
            await set_cursor_action(gemini_tab, "✓ Plan Dispatched")
        except Exception:
            pass

        # Parse planning instructions
        worker_instructions = {}
        for worker in workers:
            marker = f"--- {worker['name'].upper()} INSTRUCTION ---"
            if marker in gemini_plan:
                try:
                    parts = gemini_plan.split(marker)[1]
                    next_markers = [f"--- {w['name'].upper()} INSTRUCTION ---" for w in workers if w['id'] != worker['id']]
                    min_idx = len(parts)
                    for m in next_markers:
                        if m in parts:
                            min_idx = min(min_idx, parts.index(m))
                    worker_instructions[worker["id"]] = parts[:min_idx].strip()
                except Exception:
                    worker_instructions[worker["id"]] = f"Execute phase for task: {task}"
            else:
                worker_instructions[worker["id"]] = f"Execute specialized phase for task: {task}"

        # Load dynamic inter-agent latency settings
        from utils.latency_manager import load_latency_config
        lat_cfg = load_latency_config()
        dispatch_delay = lat_cfg.get("dispatch_delay_sec", 1.5)
        debate_delay = lat_cfg.get("debate_delay_sec", 2.0)

        # Step 2: Specialist Workers Execution (Parallel Mode)
        worker_outputs = {}
        
        async def execute_parallel_worker(worker):
            instr = worker_instructions.get(worker["id"], "")
            if not instr:
                instr = f"Execute your assigned specialized role for: {task}"
                
            print(f"\n{CYAN}[{worker['name']}] Performing delegated task in PARALLEL mode...{RESET}")
            set_agent_state(worker["id"], "BUSY", f"Executing assignment (Parallel): {instr[:40]}...")
            
            # Pop active worker browser tab in front and set cursor badge
            worker_tab = tabs[worker["id"]]
            try:
                from browser.agent_cursor import inject_agent_cursor, set_cursor_action
                role_tag = "Leader" if worker.get("is_leader") else "Specialist Worker"
                await inject_agent_cursor(worker_tab, agent_name=worker["name"], agent_role=role_tag)
                await set_cursor_action(worker_tab, "⚡ Queue: Executing Task")
            except Exception:
                pass

            worker_skills = get_agent_skills_directive(worker["id"])
            worker_prompt = (
                f"You are {worker['name']} ({worker['role']}), a specialist worker in a high-speed parallel multi-agent system.\n"
                f"{worker_skills}"
                f"Your leader (Gemini) has assigned you the following task:\n\n{instr}\n\n"
                "Please execute your assignment and return your finalized output adhering to your senior engineering skills.\n\n"
                "IMPORTANT: You MUST write your response entirely in English. "
                "Do not respond in Chinese, Spanish, or any other language. Respond ONLY in English."
            )
            
            worker_result = await talk_to_agent(worker["id"], worker_tab, worker_prompt)
            set_agent_state(worker["id"], "FREE", f"Completed: Output ready ({len(worker_result)} chars)")
            
            try:
                from browser.agent_cursor import inject_agent_cursor, set_cursor_action
                role_tag = "Leader" if worker.get("is_leader") else "Specialist Worker"
                await inject_agent_cursor(worker_tab, agent_name=worker["name"], agent_role=role_tag)
                await set_cursor_action(worker_tab, "✓ Output Ready")
            except Exception:
                pass

            try:
                await worker_tab.screenshot(path=f"visuals/step_{worker['id']}.png")
            except Exception:
                pass

            # Auto-download any images or files generated by this worker
            try:
                n = await try_download_images(worker_tab, task_folder, worker["id"])
                if n > 0:
                    print(f"{GREEN}[+] {n} file(s) auto-downloaded for {worker['name']} -> {task_folder}{RESET}")
            except Exception:
                pass

            return worker["id"], worker_result

        print(f"\n{GREEN}[*] Launching {len(workers)} specialist agent(s) simultaneously in PARALLEL mode...{RESET}")
        speak_narrator(f"Deploying {len(workers)} agents in parallel execution mode.")
        parallel_results = await asyncio.gather(*[execute_parallel_worker(w) for w in workers])
        for w_id, w_res in parallel_results:
            worker_outputs[w_id] = w_res

        # Step 2.5: Multi-Agent Discussion & Debate Round
        discussion_log = ""
        if len(workers) >= 2:
            print(f"\n{CYAN}" + "=" * 60)
            print(f"{BOLD}  DISCUSSION PHASE — AGENTS CRITIQUING & IMPROVING EACH OTHER")
            print("=" * 60 + f"{RESET}")
            speak_narrator("Initiating multi-agent critique and debate round.")
            for w in workers:
                set_agent_state(w["id"], "BUSY", "Critiquing and refining in debate round")
            worker_outputs, discussion_log = await run_discussion_round(
                task=task,
                workers=workers,
                worker_outputs=worker_outputs,
                tabs=tabs,
                talk_fn=talk_to_agent,
                gemini_tab=gemini_tab,
                rounds=1
            )
            for w in workers:
                set_agent_state(w["id"], "FREE", "Debate & critique completed")
            print(f"{GREEN}[OK] Discussion phase complete. Outputs refined.{RESET}")
        else:
            print(f"{YELLOW}[*] Only one worker — skipping discussion phase.{RESET}")
        print(f"\n{MAGENTA}[Gemini Leader] Reviewing worker outputs & compiling deliverable...{RESET}")
        try:
            from browser.agent_cursor import inject_agent_cursor, set_cursor_action
            await gemini_tab.bring_to_front()
            await inject_agent_cursor(gemini_tab, agent_name="Gemini", agent_role="Leader & Orchestrator")
            await set_cursor_action(gemini_tab, "✨ Finalizing Deliverable...")
        except Exception:
            pass

        review_inputs = ""
        for w_id, w_out in worker_outputs.items():
            review_inputs += f"=== {w_id.upper()} OUTPUT ===\n{w_out}\n\n"
            
        gemini_review_prompt = (
            "You are the Leader (Gemini). Review the work done by your agents.\n"
            f"Original Goal: '{task}'\n"
            f"Worker Outputs:\n{review_inputs}\n"
            "1. Audit the outputs. Are there any issues, mistakes, or missing requirements?\n"
            "2. If there are issues, reply starting with: 'ISSUE: [Describe what is wrong and provide specific correction instructions]'\n"
            "3. If everything is approved and meets requirements, reply starting with: 'APPROVED: [Provide the final compiled, synthesized, and polished outcome here]'\n\n"
            "IMPORTANT: Your review and the final approved outcome MUST be written entirely in English."
        )
        gemini_review = await talk_to_agent("gemini", gemini_tab, gemini_review_prompt)
        await gemini_tab.screenshot(path="visuals/step_gemini_review.png")

        try:
            from browser.agent_cursor import inject_agent_cursor, set_cursor_action
            await inject_agent_cursor(gemini_tab, agent_name="Gemini", agent_role="Leader & Orchestrator")
            await set_cursor_action(gemini_tab, "✓ Deliverable Approved")
        except Exception:
            pass

        final_output = ""
        # Dynamic Help / Correction Loop (targets the last worker for packaging)
        if "ISSUE:" in gemini_review:
            print(f"\n{RED}[!] Gemini Leadership identified an issue. Starting correction loop...{RESET}")
            correction_instr = gemini_review.split("ISSUE:")[1].strip()
            
            # Send correction back to the last specialist worker
            last_worker = workers[-1]
            last_worker_tab = tabs[last_worker["id"]]
            
            revision_prompt = (
                "The Leader (Gemini) has reviewed the project and identified the following issues:\n\n"
                f"{correction_instr}\n\n"
                "Please revise and correct the final output to address these issues.\n\n"
                "IMPORTANT: You MUST write your response entirely in English."
            )
            fixed_result = await talk_to_agent(last_worker["id"], last_worker_tab, revision_prompt)
            await last_worker_tab.screenshot(path=f"visuals/step_{last_worker['id']}_fixed.png")
            
            # Final submit back to Gemini for approval
            gemini_final_prompt = (
                f"Review the corrected final output from {last_worker['name']}:\n\n"
                f"{fixed_result}\n\n"
                "If approved, output the final, polished, production-ready outcome starting with 'APPROVED: [content]'.\n\n"
                "IMPORTANT: The final outcome MUST be written entirely in English."
            )
            gemini_final = await talk_to_agent("gemini", gemini_tab, gemini_final_prompt)
            await gemini_tab.screenshot(path="visuals/step_gemini_final.png")
            
            final_output = gemini_final
            worker_outputs[last_worker["id"]] = fixed_result
        else:
            final_output = gemini_review

        # Extract memories and update memory.json
        print(f"\n{MAGENTA}[Gemini Leader] Saving key learnings to memory...{RESET}")
        gemini_memory_prompt = (
            "Summarize the key facts, decisions, styles, or concepts created in this task to store in your memory.\n"
            f"Task: {task}\n"
            f"Final Output Summary: {final_output[:1000]}\n\n"
            "Provide a concise list of 1-3 key memory points that would be useful for future runs. "
            "Output ONLY the bullet points, starting each with '-'."
        )
        new_memories_text = await talk_to_agent("gemini", gemini_tab, gemini_memory_prompt)
        
        # Save newly acquired learnings into categorized neural memory
        try:
            added_cnt = batch_add_from_mission(new_memories_text, source_mission=task[:45])
            if added_cnt > 0:
                print(f"{GREEN}[OK] Neural Memory bank updated with {added_cnt} structured categorized items.{RESET}")
        except Exception as e:
            print(f"{RED}[!] Error saving structured memory: {e}{RESET}")

        # Detect repeated task patterns & autonomously synthesize reusable squads
        try:
            from core.squad_learner import detect_and_create_repeated_pattern_squads
            new_learned = detect_and_create_repeated_pattern_squads(min_repetition_threshold=2)
            if new_learned:
                print(f"{GREEN}[🧠 SQUAD LEARNER] Autonomously created {len(new_learned)} reusable squad(s) from repeated task patterns!{RESET}")
        except Exception as e:
            print(f"{YELLOW}[*] Squad pattern analyzer notice: {e}{RESET}")

        # Stream/display final approved results cleanly
        # Capture screenshots of all active tabs with tab names and save to images/
        try:
            from services.tab_screenshot_service import capture_all_tabs_screenshots
            saved_shots = await capture_all_tabs_screenshots(context, output_dir="images")
            if saved_shots:
                print(f"{GREEN}[📷 SNAPSHOT] Captured {len(saved_shots)} tab screenshot(s) saved into images/ directory.{RESET}")
        except Exception as e:
            print(f"{YELLOW}[*] Tab screenshot snapshot notice: {e}{RESET}")

        reset_all_workers_to_free(all_available_agents)
        speak_narrator("Mission complete. Final deliverable ready. I am standing by for your next directive.")

def launch_voice_mode(port: int = 8000):
    """
    Directly connects to Gemini Live Voice session with Master Orchestrator.
    Spawns the voice backend server if not already running on port.
    """
    server_running = False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.5)
            s.connect(("127.0.0.1", port))
            server_running = True
    except Exception:
        pass

    if not server_running:
        print(f"\n{YELLOW}[*] Initializing Gemini Live Voice Backend on port {port}...{RESET}")
        if getattr(sys, 'frozen', False):
            cmd = [sys.executable, "--voice-server"]
        else:
            cmd = [sys.executable, "-m", "uvicorn", "voice.backend.server:app", "--host", "127.0.0.1", "--port", str(port)]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        register_pid(proc.pid)
        import time
        time.sleep(2)
        print(f"{GREEN}[OK] Voice Backend running at ws://127.0.0.1:{port}/ws{RESET}")


    from voice.live_client import run_voice_client
    ws_url = f"ws://127.0.0.1:{port}/ws"
    try:
        asyncio.run(run_voice_client(ws_url))
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[*] Voice session ended.{RESET}")
    except Exception as e:
        print(f"\n{RED}[!] Voice error: {e}{RESET}")


def main():
    from core import agentlist

    if "--voice" in sys.argv or "-v" in sys.argv:
        launch_voice_mode()
        sys.exit(0)

    if "--voice-server" in sys.argv:
        import uvicorn
        print(f"{CYAN}[*] Starting Gemini Live Voice Server on ws://127.0.0.1:8000/ws...{RESET}")
        uvicorn.run("voice.backend.server:app", host="127.0.0.1", port=8000)
        sys.exit(0)

    if "--task" in sys.argv:
        idx = sys.argv.index("--task")
        if idx + 1 < len(sys.argv):
            task = sys.argv[idx + 1]
            try:
                asyncio.run(run_agent_loop(task))
            except Exception as e:
                print(f"\n{RED}[!] Error running task: {e}{RESET}")
            finally:
                saved = log_path()
                if saved:
                    print(f"{CYAN}[OK] Full log saved -> {saved}{RESET}")
                close_logging()
            sys.exit(0)

    print(f"\n{CYAN}" + "=" * 60)
    print(f"{BOLD}   LEADER-WORKER MULTI-AI COLLABORATIVE SYSTEM   ")
    print(f"{BOLD}   [Voice Mode available: type 'voice' or run with -v]   ")
    print("=" * 60 + f"{RESET}")
    
    # Display list of active agents side-by-side with specializations
    active_agents = agentlist.list_all_active_agents()
    print(f"{YELLOW}Available Agents & Specializations:{RESET}")
    for i, agent in enumerate(active_agents, 1):
        role_desc = "Leader" if agent["is_leader"] else "Worker"
        spec_summary = agent["specialization"][:70] + "..." if len(agent["specialization"]) > 70 else agent["specialization"]
        print(f"  {CYAN}{i}. {agent['name']} ({role_desc}) {RESET}- {spec_summary}")

    while True:
        # Prompt for agent selection count (default to auto)
        num_agents_input = input(f"\n{YELLOW}Enter number of agents (default: auto, max: 9, 'voice' to speak, or 'exit'): {RESET}").strip()
        if num_agents_input.lower() in ["exit", "quit"]:
            print(f"{YELLOW}[*] Exiting pipeline. Goodbye!{RESET}")
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
                    print(f"{RED}[!] Invalid count. Please choose between 2 and {len(active_agents)}.{RESET}")
                    continue
            except ValueError:
                print(f"{RED}[!] Please enter a valid number, 'auto', or 'voice'.{RESET}")
                continue
        
        # Prompt for task
        task = input(f"{YELLOW}Enter the task you want the AI pipeline to perform (or 'voice' to speak): {RESET}").strip()
        if not task:
            continue

        if task.lower() in ["voice", "v"]:
            launch_voice_mode()
            continue

        # Quick YouTube / Music playback handler
        if task.lower().startswith(("play ", "youtube ", "open youtube", "yt ")):
            query = re.sub(r"^(play|youtube|open youtube|yt)\s*", "", task, flags=re.IGNORECASE).strip()
            if not query:
                query = "lofi hip hop radio live"
            print(f"{GREEN}[*] Opening YouTube and playing: '{query}'...{RESET}")
            speak_narrator(f"Opening YouTube and playing {query}.")
            import webbrowser, urllib.parse
            webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
            continue
        
        try:
            asyncio.run(run_agent_loop(task, selected_agents_override))
        except KeyboardInterrupt:
            print(f"\n{RED}[!] Task execution interrupted by user.{RESET}")
        except Exception as e:
            print(f"\n{RED}[!] Error running task: {e}{RESET}")
        finally:
            saved = log_path()
            if saved:
                print(f"{CYAN}[OK] Full log saved -> {saved}{RESET}")
            close_logging()


if __name__ == "__main__":
    main()
