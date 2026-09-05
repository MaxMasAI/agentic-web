"""
app.py - Main PySide6 Desktop Application Entry Point for Agentic Mission Control Suite
"""

import sys
import os
import glob
import json
import time
import subprocess
import re
import multiprocessing

# Freeze support for PyInstaller on Windows
if __name__ == "__main__":
    multiprocessing.freeze_support()

# Ensure correct base directory and path resolution when running as standalone frozen executable
if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
    os.chdir(app_dir)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    internal_dir = getattr(sys, '_MEIPASS', None)
    if internal_dir and internal_dir not in sys.path:
        sys.path.insert(0, internal_dir)

# Support running pipeline sub-tasks directly from the standalone executable
if "--task" in sys.argv:
    from utils.launcher import main as run_launcher
    run_launcher()
    sys.exit(0)

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout,
    QStackedWidget, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut

from gui.theme import APP_QSS
from gui.widgets.sidebar import Sidebar

# Core Operations Pages
from gui.pages.mission_control import MissionControlPage
from gui.pages.task_dispatch import TaskDispatchPage
from gui.pages.squad_roster import SquadRosterPage
from gui.pages.mission_archive import MissionArchivePage
from gui.pages.file_explorer import FileExplorerPage
from gui.pages.mcp_hub import MCPHubPage
from gui.pages.neural_memory import NeuralMemoryPage

# Assistant Modes Pages
from gui.pages.chat_page import ChatPage
from gui.pages.chat_files_page import ChatFilesPage
from gui.pages.research_page import ResearchPage
from gui.pages.media_studio_page import MediaStudioPage
from gui.pages.settings_page import SettingsPage

# Creative & Productivity Tools
from gui.pages.playground import PlaygroundPage
from gui.tools.agent_builder import AgentBuilderPage
from gui.tools.painter import PainterPage
from gui.tools.notepad import NotepadPage
from gui.tools.scheduler_view import SchedulerPage

from core.agent_status import init_agent_status
from core import agentlist
from utils import pid_tracker

# Ensure core workspace directories exist
for d in ["tasks", "logs", "downloads", "visuals", "tests", "json"]:
    os.makedirs(d, exist_ok=True)

if not os.path.exists("json/agent_status.json"):
    init_agent_status(agentlist.list_all_active_agents())

_tasks_cache = []
_tasks_cache_mtime = 0


def parse_task_file(raw: str, path: str) -> dict:
    result = {
        "path": path,
        "filename": os.path.basename(path),
        "task": "", "timestamp": "",
        "gemini_plan": "", "worker_outputs": {}, "final_output": "",
    }
    for line in raw.split("\n")[:5]:
        if line.startswith("TASK:"):
            result["task"] = line.replace("TASK:", "").strip()
        elif line.startswith("TIMESTAMP:"):
            result["timestamp"] = line.replace("TIMESTAMP:", "").strip()
    sections = re.split(r"={40,}", raw)
    if len(sections) > 1:
        result["gemini_plan"] = sections[1].replace("GEMINI PLAN:\n", "").strip()
        for sec in sections[2:]:
            sec = sec.strip()
            if sec.startswith("FINAL APPROVED OUTPUT:"):
                result["final_output"] = sec.replace("FINAL APPROVED OUTPUT:", "").strip()
            else:
                for line in sec.split("\n"):
                    if line.strip().endswith("RESULT:"):
                        agent_name = line.strip().replace(" RESULT:", "").lower()
                        body = "\n".join(sec.split("\n")[1:]).strip()
                        result["worker_outputs"][agent_name] = body
                        break
    return result


def load_all_tasks(force_reload: bool = False) -> list:
    global _tasks_cache, _tasks_cache_mtime
    tasks_dir = "tasks"
    if not os.path.exists(tasks_dir):
        return []
    
    try:
        current_mtime = os.path.getmtime(tasks_dir)
    except Exception:
        current_mtime = 0

    if not force_reload and _tasks_cache and current_mtime == _tasks_cache_mtime:
        return _tasks_cache

    tasks = []
    for path in sorted(glob.glob(os.path.join(tasks_dir, "task_*.txt")), reverse=True):
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                raw = f.read()
            parsed = parse_task_file(raw, path)
            tasks.append(parsed)
        except Exception:
            continue
    
    _tasks_cache = tasks
    _tasks_cache_mtime = current_mtime
    return tasks


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("⚡ Agentic Mission Control & Multi-Model AI Assistant Suite")
        self.resize(1380, 900)
        self.setMinimumSize(1020, 680)

        self.running_procs = {}
        self._last_tasks_count = -1
        self._last_mem_count = -1
        self._last_sub_count = -1

        self.init_ui()
        self.init_timers()
        self.refresh_all_data(force=True)

    def init_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Categorized Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.switch_page)
        self.sidebar.abort_requested.connect(self.abort_mission)
        main_layout.addWidget(self.sidebar)

        # 2. Stacked Pages Suite
        self.stack = QStackedWidget()
        self.pages = {
            # Operations
            "home": MissionControlPage(),
            "launch": TaskDispatchPage(),
            "subagents": SquadRosterPage(),
            "history": MissionArchivePage(),
            # Assistant Modes
            "chat": ChatPage(),
            "chat_files": ChatFilesPage(),
            "research": ResearchPage(),
            "media_studio": MediaStudioPage(),
            # Creative & Tools
            "playground": PlaygroundPage(),
            "agent_builder": AgentBuilderPage(),
            "painter": PainterPage(),
            "notepad": NotepadPage(),
            "scheduler": SchedulerPage(),
            # System
            "mcp": MCPHubPage(),
            "memory": NeuralMemoryPage(),
            "explorer": FileExplorerPage(),
            "settings": SettingsPage(),
        }

        for page in self.pages.values():
            self.stack.addWidget(page)

        # Cross-Page Signals
        self.pages["home"].navigate_requested.connect(self.switch_page)
        self.pages["home"].direct_task_submitted.connect(self.on_direct_task_submitted)

        self.pages["launch"].launch_requested.connect(self.launch_pipeline)
        self.pages["launch"].abort_requested.connect(self.abort_mission)

        self.pages["playground"].dispatch_refactor_requested.connect(self.launch_pipeline)

        self.pages["subagents"].launch_squad_requested.connect(self.launch_pipeline)
        self.pages["subagents"].squads_updated.connect(lambda: self.refresh_all_data(force=True))

        self.pages["history"].open_in_playground_requested.connect(self.on_open_deliverable_in_playground)

        self.pages["memory"].memories_updated.connect(lambda: self.refresh_all_data(force=True))

        self.pages["painter"].send_sketch_requested.connect(self.on_sketch_sent_to_studio)

        self.pages["scheduler"].trigger_job_requested.connect(self.launch_pipeline)

        # Global Shortcut: Ctrl+B to Toggle Sidebar Auto-Hide / Pin
        self.sidebar_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.sidebar_shortcut.activated.connect(self.sidebar.toggle_pin)

        main_layout.addWidget(self.stack, stretch=1)

    def init_timers(self):
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(1200)
        self.poll_timer.timeout.connect(self.poll_active_processes)
        self.poll_timer.start()

    def switch_page(self, page_key: str):
        if page_key.startswith("settings_") or page_key == "settings":
            widget = self.pages["settings"]
            if self.stack.currentWidget() != widget:
                self.stack.setCurrentWidget(widget)
            if page_key.startswith("settings_"):
                cat = page_key.replace("settings_", "")
                self.pages["settings"].set_category_by_key(cat)
            self.sidebar.set_active_page(page_key, emit_signal=False)
        elif page_key in self.pages:
            widget = self.pages[page_key]
            if self.stack.currentWidget() != widget:
                self.stack.setCurrentWidget(widget)
            self.sidebar.set_active_page(page_key, emit_signal=False)

    def on_direct_task_submitted(self, task_str: str):
        self.launch_pipeline(task_str, "auto", f"Task @ {time.strftime('%H:%M:%S')}")
        self.switch_page("launch")

    def on_open_deliverable_in_playground(self, html_code: str):
        self.pages["playground"].set_editor_code(html_code)
        self.switch_page("playground")

    def on_sketch_sent_to_studio(self, sketch_path: str):
        self.pages["media_studio"].attach_sketch(sketch_path)
        self.switch_page("media_studio")

    def launch_pipeline(self, task: str, agents: str, label: str):
        task_log_file = os.path.join("logs", f"live_{int(time.time())}.log")
        log_fp = open(task_log_file, "w", encoding="utf-8", buffering=1)

        if getattr(sys, 'frozen', False):
            # In standalone executable mode, invoke self with --task
            cmd = [sys.executable, "--task", task, "--agents", agents]
            work_dir = os.path.dirname(sys.executable)
        else:
            launcher_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "launcher.py")
            cmd = [sys.executable, "-u", launcher_script, "--task", task, "--agents", agents]
            work_dir = os.path.dirname(os.path.abspath(__file__))

        proc = subprocess.Popen(
            cmd,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
            cwd=work_dir
        )

        self.running_procs[label] = {
            "proc": proc,
            "log_file": task_log_file,
            "log_fp": log_fp,
            "task": task,
            "agents": agents,
            "status": "running",
            "started": time.strftime("%H:%M:%S"),
        }

        self.pages["launch"].update_running_processes(self.running_procs)
        self.sidebar.update_active_missions(self.running_procs)
        self.switch_page("launch")

    def abort_mission(self, label: str):
        if label in self.running_procs:
            info = self.running_procs[label]
            proc = info.get("proc")
            if proc and proc.pid:
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    proc.terminate()
            info["status"] = "done"
            if "log_fp" in info and info["log_fp"] and not info["log_fp"].closed:
                try:
                    info["log_fp"].close()
                except Exception:
                    pass
            self.pages["launch"].update_running_processes(self.running_procs)
            self.sidebar.update_active_missions(self.running_procs)

    def poll_active_processes(self):
        has_changes = False
        for label, info in list(self.running_procs.items()):
            proc = info.get("proc")
            if proc:
                poll_res = proc.poll()
                if poll_res is None:
                    info["status"] = "running"
                else:
                    new_status = "done" if poll_res == 0 else "error"
                    if info["status"] != new_status:
                        info["status"] = new_status
                        has_changes = True
                    if "log_fp" in info and info["log_fp"] and not info["log_fp"].closed:
                        try:
                            info["log_fp"].close()
                        except Exception:
                            pass

        if has_changes:
            self.refresh_all_data(force=True)

        if self.stack.currentWidget() == self.pages["launch"]:
            self.pages["launch"].refresh_terminal()

        self.sidebar.update_active_missions(self.running_procs)

    def refresh_all_data(self, force: bool = False):
        tasks = load_all_tasks(force_reload=force)
        
        memories = []
        if os.path.exists("json/memory.json"):
            try:
                with open("json/memory.json", "r", encoding="utf-8") as f:
                    memories = json.load(f)
            except Exception:
                pass

        subagents = []
        if os.path.exists("json/subagents.json"):
            try:
                with open("json/subagents.json", "r", encoding="utf-8") as f:
                    subagents = json.load(f)
            except Exception:
                pass

        self.pages["home"].refresh_data(tasks, memories, subagents, self.running_procs)
        self.pages["launch"].update_running_processes(self.running_procs)

        if force or len(tasks) != self._last_tasks_count:
            self.pages["history"].refresh_tasks(tasks)
            self.pages["playground"].refresh_tasks(tasks)

        self._last_tasks_count = len(tasks)
        self._last_mem_count = len(memories)
        self._last_sub_count = len(subagents)

        from utils.mcp_service import get_skills_count
        self.sidebar.update_stats(len(tasks), len(memories), get_skills_count())
        self.sidebar.update_active_missions(self.running_procs)

    def closeEvent(self, event):
        for label, info in self.running_procs.items():
            proc = info.get("proc")
            if proc and proc.pid:
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    pass
            if "log_fp" in info and info["log_fp"] and not info["log_fp"].closed:
                try:
                    info["log_fp"].close()
                except Exception:
                    pass

        try:
            pid_tracker.kill_all_tracked_pids()
        except Exception:
            pass

        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
