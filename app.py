"""
app.py - Main PySide6 Desktop Application Entry Point for Agentic Mission Control Suite
"""

import multiprocessing

# Freeze support must be called immediately for Windows PyInstaller binaries
if __name__ == "__main__":
    multiprocessing.freeze_support()

import sys
import os
import glob
import json
import time
import subprocess
import re

# Ensure correct base directory and path resolution when running as standalone frozen executable
if getattr(sys, 'frozen', False):
    app_data_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AgenticWeb")
    os.makedirs(app_data_dir, exist_ok=True)
    os.chdir(app_data_dir)
    if app_data_dir not in sys.path:
        sys.path.insert(0, app_data_dir)
    internal_dir = getattr(sys, '_MEIPASS', None)
    if internal_dir and internal_dir not in sys.path:
        sys.path.insert(0, internal_dir)
        # Seed default configurations & assets from bundled binary into %APPDATA%/AgenticWeb
        import shutil
        for subfolder in ["json", "plugins"]:
            src_path = os.path.join(internal_dir, subfolder)
            dst_path = os.path.join(app_data_dir, subfolder)
            if os.path.exists(src_path) and not os.path.exists(dst_path):
                try:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                except Exception:
                    pass
        for file_name in [".env", "db.sqlite", "windows.xml", "linux.xml", "mac.xml"]:
            src_file = os.path.join(internal_dir, file_name)
            dst_file = os.path.join(app_data_dir, file_name)
            if os.path.exists(src_file) and not os.path.exists(dst_file):
                try:
                    shutil.copy2(src_file, dst_file)
                except Exception:
                    pass


# 0. Development Live-Reload Watcher
if "--watch" in sys.argv or "--dev" in sys.argv or "--auto-restart" in sys.argv:
    import dev
    filtered_args = [a for a in sys.argv[1:] if a not in ("--watch", "--dev", "--auto-restart")]
    if not dev.run_watchdog_cli([sys.executable, "app.py"] + filtered_args):
        dev.run_python_watcher(["app.py"] + filtered_args)
    sys.exit(0)

# 1. Pipeline Task Execution from CLI or Subprocess
if "--task" in sys.argv:
    from utils.launcher import main as run_launcher
    run_launcher()
    sys.exit(0)

# 2. Voice Server Execution
if "--voice-server" in sys.argv:
    import uvicorn
    print("\033[96m[*] Starting Gemini Live Voice Server on ws://127.0.0.1:8000/ws...\033[0m")
    uvicorn.run("voice.backend.server:app", host="127.0.0.1", port=8000)
    sys.exit(0)

# 3. Voice Mode Interactive Client
if "--voice" in sys.argv or "-v" in sys.argv:
    from core.main import launch_voice_mode
    launch_voice_mode()
    sys.exit(0)

# 4. Inline Python Execution (-c)
if "-c" in sys.argv:
    idx = sys.argv.index("-c")
    if idx + 1 < len(sys.argv):
        code_str = sys.argv[idx + 1]
        try:
            exec(compile(code_str, "<string>", "exec"), {"__name__": "__main__"})
        except Exception as e:
            print(f"Execution error: {e}", file=sys.stderr)
            sys.exit(1)
    sys.exit(0)

# 5. Direct Script Execution (e.g. agentic-web.exe script.py)
if len(sys.argv) > 1 and sys.argv[1].endswith(".py") and os.path.exists(sys.argv[1]):
    import runpy
    script_to_run = sys.argv[1]
    sys.argv = sys.argv[1:]  # shift sys.argv
    runpy.run_path(script_to_run, run_name="__main__")
    sys.exit(0)


from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QMessageBox, QDialog
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
from gui.pages.vscode_page import VSCodePage
from gui.pages.canvas_dev_page import CanvasDevPage
from gui.pages.playground import PlaygroundPage
from gui.tools.agent_builder import AgentBuilderPage
from gui.tools.painter import PainterPage
from gui.tools.notepad import NotepadPage
from gui.tools.scheduler_view import SchedulerPage


from core.agent_status import init_agent_status
from core import agentlist
from utils import pid_tracker

# Ensure core workspace directories exist
for d in ["tasks", "logs", "downloads", "visuals", "json", "plugins"]:
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
            "vscode": VSCodePage(),
            "canvas_dev": CanvasDevPage(),
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

        # Global Shortcuts
        # Ctrl+B: Toggle Sidebar
        self.sidebar_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self.sidebar_shortcut.setContext(Qt.ApplicationShortcut)
        self.sidebar_shortcut.activated.connect(self.sidebar.toggle_pin)

        # Ctrl+K & Ctrl+Shift+C: Instant Switch to Agent Canvas IDE
        self.canvas_shortcut_k = QShortcut(QKeySequence("Ctrl+K"), self)
        self.canvas_shortcut_k.setContext(Qt.ApplicationShortcut)
        self.canvas_shortcut_k.activated.connect(lambda: self.switch_page("canvas_dev"))

        self.canvas_shortcut_c = QShortcut(QKeySequence("Ctrl+Shift+C"), self)
        self.canvas_shortcut_c.setContext(Qt.ApplicationShortcut)
        self.canvas_shortcut_c.activated.connect(lambda: self.switch_page("canvas_dev"))

        # Ctrl+H & F1: Global Hotkey Reference List
        self.hotkey_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        self.hotkey_shortcut.setContext(Qt.ApplicationShortcut)
        self.hotkey_shortcut.activated.connect(self.show_hotkeys_dialog)

        self.f1_shortcut = QShortcut(QKeySequence("F1"), self)
        self.f1_shortcut.setContext(Qt.ApplicationShortcut)
        self.f1_shortcut.activated.connect(self.show_hotkeys_dialog)

        # F5 & Ctrl+R: Global Refresh
        self.refresh_shortcut_f5 = QShortcut(QKeySequence("F5"), self)
        self.refresh_shortcut_f5.setContext(Qt.ApplicationShortcut)
        self.refresh_shortcut_f5.activated.connect(lambda: self.refresh_all_data(force=True))

        self.refresh_shortcut_r = QShortcut(QKeySequence("Ctrl+R"), self)
        self.refresh_shortcut_r.setContext(Qt.ApplicationShortcut)
        self.refresh_shortcut_r.activated.connect(lambda: self.refresh_all_data(force=True))

        # Fast Tab Jump Keys (Character-based mnemonic hotkeys)
        nav_keys = [
            ("Alt+H", "home"),
            ("Alt+D", "launch"),
            ("Ctrl+K", "canvas_dev"),
            ("Alt+C", "canvas_dev"),
            ("Alt+P", "playground"),
            ("Alt+U", "chat"),
            ("Ctrl+E", "explorer"),
            ("Alt+E", "explorer"),
            ("Alt+S", "subagents"),
            ("Alt+R", "research"),
            ("Alt+M", "media_studio"),
            ("Ctrl+,", "settings"),
            ("Ctrl+Shift+F", "chat_files"),
            ("Ctrl+Shift+M", "mcp"),
            ("Ctrl+Shift+N", "memory"),
        ]
        # Ctrl+Shift+S: Capture High-Res Screenshots of all App Tabs into images/
        self.screenshot_all_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.screenshot_all_shortcut.setContext(Qt.ApplicationShortcut)
        self.screenshot_all_shortcut.activated.connect(self.capture_app_tabs_to_images)

        main_layout.addWidget(self.stack, stretch=1)

    def show_hotkeys_dialog(self):
        """Displays master side-by-side 3-column hotkey cheatsheet dialog across the application."""
        dialog = QDialog(self)
        dialog.setWindowTitle("⌨️ Agentic Web - Master Keyboard Shortcuts (Ctrl+H / F1)")
        dialog.setMinimumWidth(920)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b1120;
                border: 1.5px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
            }
            QLabel {
                color: #f8fafc;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                color: white;
                font-weight: 700;
                border-radius: 6px;
                padding: 7px 24px;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #080b11;
            }
        """)
        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(18, 16, 18, 16)
        d_layout.setSpacing(12)

        hdr = QLabel("<div style='margin-bottom: 2px;'><span style='font-size: 16px; font-weight: 800; color: #38bdf8;'>⌨️ Master Keyboard Shortcuts Cheatsheet</span> &nbsp;<span style='color: #64748b; font-size: 11px;'>(Press <b>Ctrl+H</b> or <b>F1</b> anytime)</span></div>")
        d_layout.addWidget(hdr)

        content_lbl = QLabel()
        content_lbl.setText("""
        <table border="0" cellspacing="10" cellpadding="0" width="100%" style="font-family: 'Segoe UI', sans-serif;">
        <tr>
            <!-- Column 1: Global Navigation -->
            <td valign="top" width="34%" style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 10px 12px;">
                <div style="color: #38bdf8; font-weight: 800; font-size: 12px; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 4px; margin-bottom: 6px;">🌐 GLOBAL NAVIGATION</div>
                <table border="0" cellpadding="3" cellspacing="0" width="100%" style="font-family: monospace; font-size: 11px;">
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+H / F1</td><td style="color:#cbd5e1;">Master Hotkeys</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+B</td><td style="color:#cbd5e1;">Toggle Sidebar</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">F5 / Ctrl+R</td><td style="color:#cbd5e1;">Global Refresh</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+H</td><td style="color:#cbd5e1;">Mission Control</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+D</td><td style="color:#cbd5e1;">Task Dispatch</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+K / Alt+C</td><td style="color:#cbd5e1;">Agent Canvas IDE</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+P</td><td style="color:#cbd5e1;">Playground Studio</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+U</td><td style="color:#cbd5e1;">Universal AI Chat</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+E / Alt+E</td><td style="color:#cbd5e1;">Folder Explorer</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+S</td><td style="color:#cbd5e1;">Agent Squads</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+R</td><td style="color:#cbd5e1;">Deep Research</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+M</td><td style="color:#cbd5e1;">Media Studio</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+,</td><td style="color:#cbd5e1;">Settings</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+Shift+F</td><td style="color:#cbd5e1;">Chat with Files</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+Shift+M</td><td style="color:#cbd5e1;">MCP Service Hub</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+Shift+N</td><td style="color:#cbd5e1;">Neural Memory</td></tr>
                </table>
            </td>

            <!-- Column 2: Agent Canvas IDE -->
            <td valign="top" width="36%" style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(167, 139, 250, 0.25); border-radius: 8px; padding: 10px 12px;">
                <div style="color: #a78bfa; font-weight: 800; font-size: 12px; border-bottom: 1px solid rgba(167, 139, 250, 0.2); padding-bottom: 4px; margin-bottom: 6px;">🌌 AGENT CANVAS IDE</div>
                <table border="0" cellpadding="3" cellspacing="0" width="100%" style="font-family: monospace; font-size: 11px;">
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+A</td><td style="color:#cbd5e1;">Select All Nodes & Wires</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Delete / Backspace</td><td style="color:#cbd5e1;">Delete Selected</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+T</td><td style="color:#cbd5e1;">Add Terminal Node</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Alt+A / Ctrl+Shift+A</td><td style="color:#cbd5e1;">Add Agent Node</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Alt+D / Ctrl+D</td><td style="color:#cbd5e1;">Add File/Diff Node</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Alt+N</td><td style="color:#cbd5e1;">Add Note Card</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Alt+T / Ctrl+Shift+T</td><td style="color:#cbd5e1;">✨ Tidy Graph (DAG)</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">F5 / Ctrl+Enter</td><td style="color:#cbd5e1;">Run Pipeline</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+S</td><td style="color:#cbd5e1;">Export Session JSON</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+O</td><td style="color:#cbd5e1;">Import Session JSON</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+M</td><td style="color:#cbd5e1;">Load Demo Template</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+0</td><td style="color:#cbd5e1;">Center Viewport (0,0)</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl++ / Ctrl+-</td><td style="color:#cbd5e1;">Zoom In / Zoom Out</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Middle-Click Drag</td><td style="color:#cbd5e1;">Pan Infinite Workspace</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Right-Click Area</td><td style="color:#cbd5e1;">Quick-Add Palette</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+L</td><td style="color:#cbd5e1;">Clear Canvas</td></tr>
                </table>
            </td>

            <!-- Column 3: Dispatch & Workflows -->
            <td valign="top" width="30%" style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(52, 211, 153, 0.25); border-radius: 8px; padding: 10px 12px;">
                <div style="color: #34d399; font-weight: 800; font-size: 12px; border-bottom: 1px solid rgba(52, 211, 153, 0.2); padding-bottom: 4px; margin-bottom: 6px;">🚀 DISPATCH & WORKFLOWS</div>
                <table border="0" cellpadding="3" cellspacing="0" width="100%" style="font-family: monospace; font-size: 11px;">
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+Enter</td><td style="color:#cbd5e1;">Deploy / Send / Run</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+N</td><td style="color:#cbd5e1;">New Conversation</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+Shift+L</td><td style="color:#cbd5e1;">Clear Chat History</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+S</td><td style="color:#cbd5e1;">Export HTML Preview</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+Shift+X</td><td style="color:#cbd5e1;">Abort Active Mission</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">F5 / Ctrl+R</td><td style="color:#cbd5e1;">Refresh Directory</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Esc</td><td style="color:#cbd5e1;">Close Modal / Dialog</td></tr>
                </table>
            </td>
        </tr>
        </table>
        """)
        d_layout.addWidget(content_lbl)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Done (Esc)")
        close_btn.clicked.connect(dialog.accept)
        btn_box.addWidget(close_btn)
        d_layout.addLayout(btn_box)

        dialog.exec()

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
        try:
            os.makedirs("logs", exist_ok=True)
            task_log_file = os.path.join("logs", f"live_{int(time.time())}.log")
            log_fp = open(task_log_file, "w", encoding="utf-8", errors="replace", buffering=1)

            if getattr(sys, 'frozen', False):
                # In standalone executable mode, invoke self with --task
                cmd = [sys.executable, "--task", task, "--agents", agents]
                work_dir = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AgenticWeb")
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

            try:
                self.pages["launch"].update_running_processes(self.running_procs)
                self.sidebar.update_active_missions(self.running_procs)
                self.switch_page("launch")
            except Exception as e:
                print(f"[!] Error updating UI after pipeline launch: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[!] Failed to launch task pipeline: {e}", file=sys.stderr)
            QMessageBox.critical(self, "Mission Launch Error", f"Unable to launch pipeline task:\n{e}")

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

    def capture_app_tabs_to_images(self):
        """Captures high-res screenshots of all 19 application tabs into images/ folder."""
        try:
            from utils.capture_app_tabs import capture_all_app_tabs
            res = capture_all_app_tabs()
            QMessageBox.information(
                self,
                "📸 App Screenshots Saved",
                f"Successfully captured {len(res)} high-resolution application screenshots!\n\n"
                f"Saved into: images/\n(All tabs labeled and ready for showcase)"
            )
        except Exception as e:
            QMessageBox.warning(self, "Capture Error", f"Could not capture all tabs: {e}")

    def closeEvent(self, event):
        for info in self.running_procs.values():
            proc = info.get("proc")
            if proc and proc.pid:
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    proc.terminate()
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
