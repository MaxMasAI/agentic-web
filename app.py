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

# Ensure project root is always first in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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
from PySide6.QtGui import QKeySequence, QShortcut, QIcon, QCursor

from gui.theme import APP_QSS
from gui.widgets.sidebar import Sidebar
from gui.widgets.custom_title_bar import CustomTitleBar

# Core Operations Pages
from gui.pages.mission_control import MissionControlPage
from gui.pages.task_dispatch import TaskDispatchPage
from gui.pages.squad_roster import SquadRosterPage
from gui.pages.mission_archive import MissionArchivePage
from gui.pages.file_explorer import FileExplorerPage
from gui.pages.mcp_hub import MCPHubPage
from gui.pages.neural_memory import NeuralMemoryPage
from gui.pages.token_manager_page import TokenManagerPage

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
from gui.pages.maxmasai_harness_page import MaxMasAIHarnessPage


from core.agent_status import init_agent_status
from core import agentlist
from utils import pid_tracker

# Ensure core workspace directories exist
for d in ["tasks", "logs", "downloads", "visuals", "json", "plugins"]:
    os.makedirs(d, exist_ok=True)


if not os.path.exists("json/agent_status.json"):
    init_agent_status(agentlist.list_all_active_agents())

# Fast cached task indexer
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
        self.setWindowTitle("⚡ AUTONOMOUS MULTI-AGENT OS")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(1380, 900)
        self.setMinimumSize(1020, 680)

        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "000_web_agent.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.running_procs = {}
        self._last_tasks_count = -1
        self._last_mem_count = -1
        self._last_sub_count = -1

        # Initialize Antigravity System Cursor Overlay (Auto-shows during system tasks)
        self.system_cursor_overlay = None
        self._cursor_auto_hide_timer = None
        try:
            DesktopSystemCursorOverlay = None
            try:
                import system.system_cursor as _sys_cursor
                DesktopSystemCursorOverlay = getattr(_sys_cursor, "DesktopSystemCursorOverlay", None)
            except (ImportError, AttributeError):
                pass

            if not DesktopSystemCursorOverlay:
                try:
                    from system import DesktopSystemCursorOverlay
                except (ImportError, AttributeError):
                    pass

            if not DesktopSystemCursorOverlay:
                # Direct file import fallback to root system/system_cursor.py
                import importlib.util
                sys_cursor_file = os.path.join(PROJECT_ROOT, "system", "system_cursor.py")
                if os.path.exists(sys_cursor_file):
                    spec = importlib.util.spec_from_file_location("root_system_cursor_pkg", sys_cursor_file)
                    if spec and spec.loader:
                        mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        DesktopSystemCursorOverlay = getattr(mod, "DesktopSystemCursorOverlay", None)

            if DesktopSystemCursorOverlay:
                self.system_cursor_overlay = DesktopSystemCursorOverlay(agent_id="gemini")
                self.system_cursor_overlay.hide()
        except Exception as e:
            print(f"[SystemCursor] Note: {e}")

        self.init_ui()
        self.init_timers()
        self.refresh_all_data(force=True)

        # Restore last active tab from previous session
        try:
            from services.app_config import config
            last_tab = config.get("app.last_active_tab", "home")
            if last_tab and (last_tab in self.pages or last_tab.startswith("settings")):
                self.switch_page(last_tab)
        except Exception as e:
            print(f"[MainWindow] Note restoring last tab: {e}")

    def show_system_cursor_for_task(self, action_text: str = "Gemini Orchestrating...", duration_sec: float = 4.0, agent_id: str = "gemini"):
        """Auto-activates visual agent cursor overlay when tasks run, hiding automatically upon completion."""
        if getattr(self, "system_cursor_overlay", None):
            try:
                self.system_cursor_overlay.set_active_worker(agent_id, action_text)
                self.system_cursor_overlay.show()
                self.system_cursor_overlay.start_following_mouse(interval_ms=16)

                # Check if permanently pinned by user toggle
                is_pinned = hasattr(self, "title_bar") and self.title_bar and hasattr(self.title_bar, "btn_cursor") and self.title_bar.btn_cursor.isChecked()
                if not is_pinned:
                    if self._cursor_auto_hide_timer:
                        self._cursor_auto_hide_timer.stop()
                    self._cursor_auto_hide_timer = QTimer(self)
                    self._cursor_auto_hide_timer.setSingleShot(True)
                    self._cursor_auto_hide_timer.timeout.connect(self._auto_hide_system_cursor)
                    self._cursor_auto_hide_timer.start(int(duration_sec * 1000))
            except Exception as e:
                print(f"[SystemCursor] Trigger Note: {e}")

    def _auto_hide_system_cursor(self):
        if getattr(self, "system_cursor_overlay", None):
            is_pinned = hasattr(self, "title_bar") and self.title_bar and hasattr(self.title_bar, "btn_cursor") and self.title_bar.btn_cursor.isChecked()
            if not is_pinned:
                self.system_cursor_overlay.stop_following_mouse()
                self.system_cursor_overlay.hide()

    def toggle_system_cursor(self, enabled: bool):
        """Manually toggles or pins the visual follow cursor overlay (Default Google Gemini Leader)."""
        if getattr(self, "system_cursor_overlay", None):
            if enabled:
                if self._cursor_auto_hide_timer and self._cursor_auto_hide_timer.isActive():
                    self._cursor_auto_hide_timer.stop()
                self.system_cursor_overlay.set_active_worker("gemini", "👑 Gemini Follow")
                self.system_cursor_overlay.show()
                self.system_cursor_overlay.start_following_mouse(16)
            else:
                self.system_cursor_overlay.stop_following_mouse()
                self.system_cursor_overlay.hide()

    def init_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        # Root vertical layout: Title bar + Body
        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 0. Custom Top Title Bar
        self.title_bar = CustomTitleBar(self)
        self.title_bar.snapshot_requested.connect(self.capture_app_tabs_to_images)
        self.title_bar.cursor_toggled.connect(self.toggle_system_cursor)
        self.title_bar.about_requested.connect(self.show_about_dialog)
        root_layout.addWidget(self.title_bar)

        # Body Horizontal Layout
        body_layout = QHBoxLayout()
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # 1. Categorized Sidebar
        self.sidebar = Sidebar()
        self.sidebar.page_changed.connect(self.switch_page)
        self.sidebar.abort_requested.connect(self.abort_mission)
        body_layout.addWidget(self.sidebar)

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
            "harness": MaxMasAIHarnessPage(),
            "agent_builder": AgentBuilderPage(),
            "painter": PainterPage(),
            "notepad": NotepadPage(),
            "scheduler": SchedulerPage(),
            # System
            "tokens": TokenManagerPage(),
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
        self.pages["home"].multi_tasks_submitted.connect(self.on_multi_tasks_submitted)

        self.pages["launch"].launch_requested.connect(self.launch_pipeline)
        self.pages["launch"].multi_tasks_submitted.connect(self.on_multi_tasks_submitted)
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
            ("Ctrl+Shift+H", "harness"),
        ]
        # Ctrl+Shift+S: Capture High-Res Screenshots of all App Tabs into images/
        self.screenshot_all_shortcut = QShortcut(QKeySequence("Ctrl+Shift+S"), self)
        self.screenshot_all_shortcut.setContext(Qt.ApplicationShortcut)
        self.screenshot_all_shortcut.activated.connect(self.capture_app_tabs_to_images)

        body_layout.addWidget(self.stack, stretch=1)
        root_layout.addLayout(body_layout)

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

    def show_about_dialog(self):
        """Displays the official About dialog modal with full versioning, links, and license."""
        from gui.widgets.about_dialog import AboutDialog
        dialog = AboutDialog(self)
        dialog.exec()

    def init_timers(self):
        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(1200)
        self.poll_timer.timeout.connect(self.poll_active_processes)
        self.poll_timer.start()

    def switch_page(self, page_key: str):
        page_titles = {
            "home": "Mission Control Dashboard",
            "launch": "Antigravity Agents & Task Dispatch",
            "subagents": "Multi-Agent Squad Roster",
            "history": "Mission Archives & Deliverables",
            "chat": "Multi-Model AI Chat",
            "chat_files": "Document & Knowledge Chat",
            "research": "Deep Research Studio",
            "media_studio": "Media & Creative Studio",
            "vscode": "Monaco Code Studio (IDE)",
            "canvas_dev": "Infinite Agent Canvas IDE",
            "playground": "Agent Playground & Live Preview",
            "agent_builder": "Custom Agent Builder",
            "painter": "AI Visual Sketch Studio",
            "notepad": "Scratchpad & Notes",
            "scheduler": "Automated Job Scheduler",
            "tokens": "Token & Cost Optimization",
            "mcp": "MCP Server Hub & Protocol",
            "memory": "Neural Memory & Knowledge",
            "explorer": "Project File Explorer",
            "settings": "System Configuration & Models",
        }
        title = page_titles.get(page_key.replace("settings_", ""), page_key.title())
        if hasattr(self, 'title_bar') and self.title_bar:
            self.title_bar.set_page_title(title)

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

        # Persist selected page across application restarts
        try:
            from services.app_config import config
            config.set("app.last_active_tab", page_key)
        except Exception:
            pass

    def on_direct_task_submitted(self, task_str: str):
        from core.command_router import route_task_with_laya, split_multi_task_prompt
        from core.internal_tool_executor import InternalToolExecutor
        
        # Check if the prompt contains multiple compound subtasks
        subtasks = split_multi_task_prompt(task_str)
        if len(subtasks) > 1:
            dispatched = []
            for idx, t_info in enumerate(subtasks, 1):
                t_txt = t_info.get("task", task_str)
                t_agt = t_info.get("agents", "auto")
                lbl = f"[{idx}/{len(subtasks)}] {t_agt.upper()} @ {time.strftime('%H:%M:%S')}"
                dispatched.append((t_txt, t_agt, lbl))
            self.on_multi_tasks_submitted(dispatched)
            return

        cmd_info = route_task_with_laya(task_str)
        cmd_type = cmd_info.get("type", "dispatch")
        tool_exec = InternalToolExecutor.get_instance()

        if cmd_type == "empty":
            return

        # 1. State Reset
        if cmd_type == "reset":
            self.show_system_cursor_for_task("Pool State Reset", duration_sec=3.0, agent_id="system")
            from core.agent_status import set_all_agents_free
            set_all_agents_free("Idle - Ready for assignment")
            self.refresh_all_data(force=True)
            QMessageBox.information(self, "🔄 State Reset", "All agent statuses have been reset to FREE.")
            return

        # 2. Help Guide
        if cmd_type == "help":
            self.show_slash_commands_help_dialog()
            return

        # 3. Direct Page Navigation
        if cmd_type == "navigate":
            target_page = cmd_info.get("target_page", "home")
            self.show_system_cursor_for_task(f"Navigating to {target_page.title()}", duration_sec=2.0, agent_id="gemini")
            self.switch_page(target_page)
            return

        # 4. Agent Inspector
        if cmd_type == "inspect":
            target = cmd_info.get("target_agent", "gemini")
            self.show_system_cursor_for_task(f"Inspecting {target.title()}", duration_sec=3.0, agent_id=target)
            self.pages["home"].pool_monitor.inspect_agent(target)
            return

        # 5. Direct OS / System Exec Tool
        if cmd_type == "system_exec":
            task_cmd = cmd_info.get("task", "")
            self.show_system_cursor_for_task(f"OS Exec: {task_cmd[:20]}", duration_sec=5.0, agent_id="system")
            res = tool_exec.execute_os_command(task_cmd)
            msg = res.get("output") or res.get("error") or "Command executed."
            QMessageBox.information(self, "⚡ System OS Execution", f"<b>Command:</b> <code>{task_cmd}</code><br><br><b>Output:</b><pre style='background:#1e293b;padding:8px;border-radius:6px;color:#f8fafc;'>{msg[:1200]}</pre>")
            return

        # 6. Direct MCP Tool Execution
        if cmd_type == "mcp_tool":
            tool_name = cmd_info.get("tool_name", "")
            tool_args = cmd_info.get("tool_args", "{}")
            self.show_system_cursor_for_task(f"MCP Tool: {tool_name}", duration_sec=4.0, agent_id="system")
            res = tool_exec.execute_mcp_tool(tool_name, tool_args)
            msg = res.get("output") or res.get("error") or "MCP operation finished."
            QMessageBox.information(self, "🔌 MCP Hub Execution", f"<b>Tool:</b> <code>{tool_name}</code><br><br><b>Output:</b><pre style='background:#1e293b;padding:8px;border-radius:6px;color:#f8fafc;'>{msg[:1200]}</pre>")
            return

        # 7. Direct Neural Memory Tool
        if cmd_type == "memory_tool":
            act = cmd_info.get("action", "search")
            q = cmd_info.get("query", "")
            self.show_system_cursor_for_task(f"Neural Memory {act.title()}", duration_sec=3.0, agent_id="gemini")
            res = tool_exec.execute_memory_operation(act, q)
            msg = res.get("output") or res.get("error") or "Memory updated."
            QMessageBox.information(self, "🧠 Neural Memory", f"<b>Action:</b> {act.upper()}<br><b>Query:</b> {q}<br><br><b>Result:</b><pre style='background:#1e293b;padding:8px;border-radius:6px;color:#f8fafc;'>{msg[:1200]}</pre>")
            return

        # 8. Direct File I/O Tool
        if cmd_type == "file_tool":
            op = cmd_info.get("operation", "read")
            path = cmd_info.get("path", "")
            content = cmd_info.get("content", "")
            self.show_system_cursor_for_task(f"File {op.title()}: {path}", duration_sec=3.0, agent_id="system")
            res = tool_exec.execute_file_operation(op, path, content)
            msg = res.get("output") or res.get("error") or "File operation completed."
            QMessageBox.information(self, "📁 Local Filesystem Tool", f"<b>Operation:</b> {op.upper()}<br><b>Path:</b> <code>{path}</code><br><br><b>Output:</b><pre style='background:#1e293b;padding:8px;border-radius:6px;color:#f8fafc;'>{msg[:1200]}</pre>")
            return

        # 9. Direct Wikipedia Tool
        if cmd_type == "wiki_tool":
            q = cmd_info.get("query", "")
            self.show_system_cursor_for_task(f"Wikipedia: {q}", duration_sec=3.0, agent_id="gemini")
            res = tool_exec.execute_wikipedia(q)
            msg = res.get("output") or res.get("error") or "No article found."
            QMessageBox.information(self, "📚 Wikipedia Knowledge Tool", f"<b>Article:</b> {res.get('title', q)}<br><br><div style='line-height:1.6;color:#f8fafc;'>{msg[:1500]}</div>")
            return

        # 10. Direct Web Search Tool
        if cmd_type == "web_tool":
            q = cmd_info.get("query", "")
            self.show_system_cursor_for_task(f"Web Search: {q}", duration_sec=4.0, agent_id="perplexity")
            res = tool_exec.execute_web_search(q)
            msg = res.get("output") or res.get("error") or "Search complete."
            QMessageBox.information(self, "🌐 Real-Time Web Search", f"<b>Query:</b> {q}<br><br><pre style='background:#1e293b;padding:8px;border-radius:6px;color:#f8fafc;white-space:pre-wrap;'>{msg[:1500]}</pre>")
            return

        # 11. Direct MaxMasAI Harness Execution
        if cmd_type == "harness_tool":
            h_task = cmd_info.get("task", "")
            self.show_system_cursor_for_task("Launching MaxMasAI Harness", duration_sec=3.0, agent_id="gemini")
            self.switch_page("harness")
            if hasattr(self.pages["harness"], "input_area"):
                self.pages["harness"].input_area.setText(h_task)
            return

        # 12. Regular or Multi-Agent Task Dispatch with Autonomous Tool Ingestion & LAYA Telemetry
        target_agents = cmd_info.get("agents", "auto")
        task_text = cmd_info.get("task", task_str)

        # Autonomous Agent Tool Resolution: If LAYA or InternalToolExecutor detected an internal tool need
        auto_tool = cmd_info.get("auto_tool_result")
        if auto_tool:
            tool_name = auto_tool.get("tool", "internal_tool")
            self.show_system_cursor_for_task(f"Auto Tool Executed: {tool_name.upper()}", duration_sec=3.5, agent_id="gemini")
            tool_injection = InternalToolExecutor.format_tool_result_for_agent(auto_tool)
            task_text = f"{task_text}\n\n{tool_injection}"

        # If agents="auto" and LAYA fast-path identified a specialist with >=85% confidence
        if target_agents == "auto" and cmd_info.get("laya_fast_path"):
            rec_specialist = cmd_info.get("laya_recommended_specialist", "gemini_leader")
            spec_map = {
                "gemini_leader": "gemini",
                "deepseek_coder": "deepseek",
                "claude_auditor": "claude",
                "chatgpt_synthesizer": "chatgpt",
                "web_researcher": "perplexity",
                "system_exec": "system",
                "multi_agent_squad": "all"
            }
            mapped_agent = spec_map.get(rec_specialist, "auto")
            if mapped_agent != "auto":
                target_agents = mapped_agent

        active_agent_id = "gemini" if target_agents in ("auto", "gemini", "all") else target_agents.split(",")[0]
        self.show_system_cursor_for_task(f"Deploying {target_agents.upper()}", duration_sec=3.5, agent_id=active_agent_id)

        laya_lat = cmd_info.get("laya_latency_ms", 0.0)
        label = f"{target_agents.upper()} (LAYA {laya_lat}ms) @ {time.strftime('%H:%M:%S')}"
        self.launch_pipeline(task_text, target_agents, label)
        self.switch_page("launch")

    def show_slash_commands_help_dialog(self):
        """Displays slash command syntax reference and internal tool cheatsheet."""
        dialog = QDialog(self)
        dialog.setWindowTitle("⚡ Multi-Agent Direct Slash Commands & Internal Tools Guide")
        dialog.setMinimumWidth(800)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b1120;
                border: 1.5px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
            }
            QLabel { color: #f8fafc; font-size: 12.5px; }
            QPushButton {
                background: #38bdf8;
                color: #080b11;
                font-weight: 700;
                border-radius: 6px;
                padding: 6px 20px;
            }
        """)
        d_lay = QVBoxLayout(dialog)
        d_lay.setContentsMargins(20, 18, 20, 18)
        d_lay.setSpacing(12)

        hdr = QLabel("<div style='font-size:16px;font-weight:800;color:#38bdf8;'>⚡ Unified Internal Tools & Multi-Agent Slash Routing</div>")
        d_lay.addWidget(hdr)

        body = QLabel("""
        <div style='line-height:1.7; color:#cbd5e1;'>
        You can control all internal tools and route tasks directly from the Mission Control input bar:<br><br>
        
        <b>🛠️ Internal Tool Controls:</b><br>
        • <b>System / OS Exec:</b> <code>/system - open notepad</code> or <code>/os - calc</code> or <code>/exec - ipconfig</code><br>
        • <b>Real-Time Web Search:</b> <code>/search &lt;query&gt;</code> or <code>/web &lt;query&gt;</code><br>
        • <b>Neural Memory:</b> <code>/memory search &lt;query&gt;</code> or <code>/memory add &lt;note&gt;</code><br>
        • <b>File I/O:</b> <code>/file read &lt;path&gt;</code> or <code>/file write &lt;path&gt; &lt;content&gt;</code><br>
        • <b>Wikipedia Lookup:</b> <code>/wiki &lt;topic&gt;</code><br>
        • <b>MCP Protocol:</b> <code>/mcp &lt;tool_name&gt; [args_json]</code><br>
        • <b>MaxMasAI Harness:</b> <code>/harness &lt;task&gt;</code><br>
        • <b>Instant Page Jump:</b> <code>/tokens</code>, <code>/canvas</code>, <code>/vscode</code>, <code>/notepad</code>, <code>/painter</code>, <code>/scheduler</code><br><br>
        
        <b>👥 Multi-Agent Squad Routing:</b><br>
        • <b>Single Specialist:</b> <code>/deepseek - Write a python web scraper</code><br>
        • <b>Multi-Agent Squad:</b> <code>/claude,chatgpt - Review and synthesize report</code><br>
        • <b>Full Team Squad:</b> <code>/all - Execute full collaborative plan</code><br>
        • <b>Inspect Agent:</b> <code>/inspect deepseek</code> | <b>Reset Pool:</b> <code>/reset</code><br><br>
        
        <b>🤖 Autonomous Agent Tool Execution:</b><br>
        • Ask natural language questions (e.g. <i>'Search web for latest Python release'</i> or <i>'Read file project.yml'</i>) — agents will autonomously select and run internal tools dynamically!
        </div>
        """)
        d_lay.addWidget(body)

        btn_ok = QPushButton("Got It")
        btn_ok.setCursor(QCursor(Qt.PointingHandCursor))
        btn_ok.clicked.connect(dialog.accept)
        d_lay.addWidget(btn_ok, alignment=Qt.AlignRight)
        dialog.exec()

    def on_open_deliverable_in_playground(self, html_code: str):
        self.pages["playground"].set_editor_code(html_code)
        self.switch_page("playground")

    def on_sketch_sent_to_studio(self, sketch_path: str):
        self.pages["media_studio"].attach_sketch(sketch_path)
        self.switch_page("media_studio")

    def on_multi_tasks_submitted(self, tasks_list: list):
        if not tasks_list:
            return
        self.show_system_cursor_for_task(f"Deploying {len(tasks_list)} Parallel Tasks", duration_sec=3.5)
        for task_txt, agents_str, label in tasks_list:
            self.launch_pipeline(task_txt, agents_str, label)
        self.switch_page("launch")

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
                if hasattr(self.pages["home"], "update_running_processes"):
                    self.pages["home"].update_running_processes(self.running_procs)
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
        if getattr(self, "system_cursor_overlay", None):
            try:
                self.system_cursor_overlay.stop_following_mouse()
                self.system_cursor_overlay.close()
            except Exception:
                pass

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
    
    # Load central QSS theme conforming to design_system_ui_theme_documentation.md
    theme_path = os.path.join(PROJECT_ROOT, "theme.qss")
    if os.path.exists(theme_path):
        try:
            with open(theme_path, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        except Exception:
            app.setStyleSheet(APP_QSS)
    else:
        app.setStyleSheet(APP_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
