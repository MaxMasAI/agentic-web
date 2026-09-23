"""
gui/widgets/popout_dispatcher_widget.py - Multi-Window Pop-Out Task Dispatcher & Telemetry Workspace
Provides standalone, detachable floating multi-windows capable of decomposing compound prompts into multiple
parallel specialist agent tasks, streaming live telemetry HUDs, and controlling multi-agent squads.
"""

import os
import time
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QFrame, QSizePolicy, QDialog,
    QTabWidget, QCheckBox, QRadioButton, QButtonGroup, QGridLayout,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor, QFont, QColor, QKeySequence, QShortcut

from core.command_router import route_task_with_laya, split_multi_task_prompt
from core.agent_status import get_all_agent_status
from core.agentlist import get_lead_agent
from gui.widgets.slash_autocomplete import attach_slash_autocomplete
from gui.widgets.terminal_view import TerminalView
from gui.widgets.workflow_hud_widget import WorkflowHUDWidget
from utils.latency_manager import load_latency_config, save_latency_config, PROFILES


class PopoutDispatcherWidget(QFrame):
    """
    Multi-Agent Pop-out Task Dispatcher Widget.
    Embedded inside pages or hosted within standalone PopoutDispatcherDialog floating windows.
    """
    task_dispatched = Signal(str, str, str)  # (task_text, agents_str, label)
    multi_tasks_dispatched = Signal(list)    # list of (task_text, agents_str, label)
    spawn_new_window_requested = Signal()
    closed = Signal()

    def __init__(self, parent=None, is_standalone: bool = False):
        super().__init__(parent)
        self.setObjectName("PopoutDispatcherWidget")
        self.is_standalone = is_standalone
        self.running_procs: Dict[str, Any] = {}
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame#PopoutDispatcherWidget {
                background-color: #0b1120;
                border: 2px solid #38bdf8;
                border-radius: 12px;
            }
            QTabWidget::pane {
                border: 1px solid rgba(56, 189, 248, 0.25);
                background-color: #0f172a;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 7px 14px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 700;
                font-size: 11px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #38bdf8;
                color: #0b1120;
            }
            QTabBar::tab:hover:!selected {
                background-color: rgba(56, 189, 248, 0.2);
                color: #38bdf8;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # 1. Top Header Bar
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        t_lbl = QLabel("⚡ MULTI-AGENT TASK DISPATCHER")
        t_lbl.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #38bdf8; letter-spacing: 0.8px;")
        hdr.addWidget(t_lbl)

        self.active_badge = QLabel("0 Active Missions")
        self.active_badge.setStyleSheet("""
            background: rgba(16, 185, 129, 0.15);
            color: #10b981;
            border: 1px solid #10b98155;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 700;
        """)
        hdr.addWidget(self.active_badge)
        hdr.addStretch()

        # Spawn New Window Button
        btn_new_win = QPushButton("⊞ New Window")
        btn_new_win.setCursor(QCursor(Qt.PointingHandCursor))
        btn_new_win.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                border: 1px solid #38bdf866;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #0b1120;
            }
        """)
        btn_new_win.setToolTip("Open another independent floating Multi-Agent Task Window")
        btn_new_win.clicked.connect(self.spawn_new_window_requested.emit)
        hdr.addWidget(btn_new_win)

        # Close Button
        btn_close = QPushButton("✕")
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setStyleSheet("background: transparent; color: #94a3b8; border: none; font-size: 14px; font-weight: 800; padding: 2px 6px;")
        btn_close.clicked.connect(self.close_widget)
        hdr.addWidget(btn_close)

        self.main_layout.addLayout(hdr)

        # 2. Main Tabbed Workspace
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Tab 1: Dispatch Studio (Multi-Task)
        self.tab_dispatch = QWidget()
        self.setup_dispatch_tab()
        self.tabs.addTab(self.tab_dispatch, "🚀 Dispatch Studio (Multi-Task)")

        # Tab 2: Live Telemetry & HUD
        self.tab_stream = QWidget()
        self.setup_stream_tab()
        self.tabs.addTab(self.tab_stream, "📡 Live Telemetry & Agent HUD")

        # Tab 3: Specialist Agent Roster
        self.tab_roster = QWidget()
        self.setup_roster_tab()
        self.tabs.addTab(self.tab_roster, "🤖 Specialist Roster")

        self.main_layout.addWidget(self.tabs)

    def setup_dispatch_tab(self):
        lay = QVBoxLayout(self.tab_dispatch)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        # Instructions / Multi-Task hint
        hint_lbl = QLabel(
            "<b>Multi-Task Prompting:</b> Enter a single task or compound prompt (e.g. numbered list <code>1. ... 2. ...</code>, "
            "or chained slash commands <code>/deepseek - code ; /claude - review</code>). Tasks will be automatically split and dispatched!"
        )
        hint_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: rgba(15, 23, 42, 0.6); padding: 6px; border-radius: 6px;")
        hint_lbl.setWordWrap(True)
        lay.addWidget(hint_lbl)

        # Prompt Input
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText(
            "🎯 Enter task, compound goal, or /{agent} commands...\n\n"
            "Examples:\n"
            "• Single Goal: Build a high-performance REST API with authentication\n"
            "• Multi-Task Chained: /deepseek - build auth backend ; /claude - audit security ; /perplexity - find CVEs\n"
            "• Numbered Tasks:\n"
            "  1. Scrape latest tech news\n"
            "  2. Summarize top stories with ChatGPT\n"
            "  3. Generate executive dashboard chart"
        )
        self.prompt_edit.setFixedHeight(110)
        self.prompt_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1.5px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
            }
            QTextEdit:focus {
                border-color: #38bdf8;
            }
        """)
        attach_slash_autocomplete(self.prompt_edit)
        lay.addWidget(self.prompt_edit)

        # Options Row
        opt_row = QHBoxLayout()
        opt_row.setSpacing(10)

        self.cb_auto_split = QCheckBox("⚡ Auto-Split Compound Prompts into Multi-Agent Tasks")
        self.cb_auto_split.setChecked(True)
        self.cb_auto_split.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 11px;")
        opt_row.addWidget(self.cb_auto_split)

        opt_row.addStretch()

        self.combo_target_agent = QComboBox()
        self.combo_target_agent.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """)
        self.combo_target_agent.addItems([
            "🤖 Dynamic AI Auto-Select (LAYA)",
            "👑 Google Gemini (Master Leader)",
            "💻 DeepSeek (Coder & Reasoning)",
            "📝 ChatGPT (Synthesis & Copy)",
            "🛡️ Claude (Security & Review)",
            "🌐 Perplexity AI (Web Search)",
            "⚡ All Specialists (Full Squad)"
        ])
        opt_row.addWidget(self.combo_target_agent)
        lay.addLayout(opt_row)

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_dispatch = QPushButton("🚀 Dispatch Mission(s)")
        self.btn_dispatch.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_dispatch.setStyleSheet("""
            QPushButton {
                background-color: #ff4b4b;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 9px 20px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
        """)
        self.btn_dispatch.clicked.connect(self.dispatch_from_studio)
        btn_row.addWidget(self.btn_dispatch, stretch=3)

        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        btn_clear.setStyleSheet("background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef444444; border-radius: 6px; padding: 8px 12px; font-size: 11px; font-weight: 700;")
        btn_clear.clicked.connect(lambda: self.prompt_edit.clear())
        btn_row.addWidget(btn_clear, stretch=1)

        lay.addLayout(btn_row)

    def setup_stream_tab(self):
        lay = QVBoxLayout(self.tab_stream)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        # Stream Selector Row
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("<b>Active Mission Stream:</b>"))

        self.stream_combo = QComboBox()
        self.stream_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """)
        self.stream_combo.currentIndexChanged.connect(self.on_stream_changed)
        top_row.addWidget(self.stream_combo, stretch=2)

        self.btn_abort_stream = QPushButton("⏹ Abort Mission")
        self.btn_abort_stream.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_abort_stream.setStyleSheet("background: rgba(239, 68, 68, 0.2); color: #ef4444; border: 1px solid #ef4444; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 700;")
        self.btn_abort_stream.clicked.connect(self.abort_current_stream)
        top_row.addWidget(self.btn_abort_stream)

        lay.addLayout(top_row)

        # Real-Time Workflow HUD
        self.workflow_hud = WorkflowHUDWidget()
        lay.addWidget(self.workflow_hud)

        # Terminal Log Stream
        self.terminal = TerminalView()
        self.terminal.setMinimumHeight(180)
        lay.addWidget(self.terminal, stretch=1)

    def setup_roster_tab(self):
        lay = QVBoxLayout(self.tab_roster)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        info_lbl = QLabel("<b>1-Click Quick Specialist Dispatch:</b> Click any model below to prefill and dispatch:")
        info_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        lay.addWidget(info_lbl)

        grid = QGridLayout()
        grid.setSpacing(8)

        roster = [
            ("👑 Gemini", "gemini", "Master Orchestrator"),
            ("💻 DeepSeek", "deepseek", "Coder & Reasoning"),
            ("📝 ChatGPT", "chatgpt", "Synthesis & Report"),
            ("🛡️ Claude", "claude", "Audit & Review"),
            ("🌐 Perplexity", "perplexity", "Live Web Search"),
            ("🚀 Copilot", "copilot", "Automation & Office"),
            ("🎨 DALL-E 3", "dalle", "Image Generation"),
            ("⚡ Nvidia NIM", "nvidia_ai", "High-Performance GPU"),
        ]

        for idx, (label, aid, desc) in enumerate(roster):
            btn = QPushButton(f"{label}\n({desc})")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(15, 23, 42, 0.8);
                    color: #e2e8f0;
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    border-radius: 6px;
                    padding: 8px 6px;
                    font-size: 11px;
                    font-weight: 700;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: rgba(56, 189, 248, 0.2);
                    border-color: #38bdf8;
                    color: #38bdf8;
                }
            """)
            btn.clicked.connect(lambda *args, a=aid: self.quick_select_agent(a))
            grid.addWidget(btn, idx // 4, idx % 4)

        lay.addLayout(grid)

    def quick_select_agent(self, agent_id: str):
        self.tabs.setCurrentIndex(0)
        current = self.prompt_edit.toPlainText().strip()
        if current and not current.startswith("/"):
            self.prompt_edit.setPlainText(f"/{agent_id} - {current}")
        elif not current:
            self.prompt_edit.setPlainText(f"/{agent_id} - ")
            self.prompt_edit.setFocus()

    def dispatch_from_studio(self):
        text = self.prompt_edit.toPlainText().strip()
        if not text:
            return

        auto_split = self.cb_auto_split.isChecked()
        if auto_split:
            tasks = split_multi_task_prompt(text)
        else:
            tasks = [route_task_with_laya(text)]

        # Map agent selection dropdown if not overridden by slash command
        agent_idx = self.combo_target_agent.currentIndex()
        default_agent_map = {
            0: "auto",
            1: "gemini",
            2: "deepseek",
            3: "chatgpt",
            4: "claude",
            5: "perplexity",
            6: "all"
        }
        dropdown_agent = default_agent_map.get(agent_idx, "auto")

        dispatched_list = []
        for idx, t_info in enumerate(tasks, 1):
            task_str = t_info.get("task", text)
            agent_str = t_info.get("agents", "auto")
            if agent_str == "auto" and dropdown_agent != "auto":
                agent_str = dropdown_agent

            label = f"[{idx}/{len(tasks)}] {agent_str.upper()} @ {time.strftime('%H:%M:%S')}" if len(tasks) > 1 else f"{agent_str.upper()} @ {time.strftime('%H:%M:%S')}"
            
            dispatched_list.append((task_str, agent_str, label))

        # Clear input & switch to Live Telemetry stream tab
        self.prompt_edit.clear()
        self.tabs.setCurrentIndex(1)

        if len(dispatched_list) == 1:
            item = dispatched_list[0]
            self.task_dispatched.emit(item[0], item[1], item[2])
        else:
            self.multi_tasks_dispatched.emit(dispatched_list)

    def update_running_processes(self, procs: Dict[str, Any]):
        self.running_procs = procs
        current_sel = self.stream_combo.currentText()
        self.stream_combo.blockSignals(True)
        self.stream_combo.clear()

        running_count = sum(1 for p in procs.values() if p.get("status") == "running")
        self.active_badge.setText(f"{running_count} Active Missions")
        self.active_badge.setStyleSheet(f"""
            background: {'rgba(16, 185, 129, 0.15)' if running_count > 0 else 'rgba(100, 116, 139, 0.15)'};
            color: {'#10b981' if running_count > 0 else '#94a3b8'};
            border: 1px solid {'#10b98155' if running_count > 0 else '#64748b55'};
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 700;
        """)

        for label, info in procs.items():
            status_icon = "🟢" if info.get("status") == "running" else ("🔴" if info.get("status") == "error" else "⚪")
            self.stream_combo.addItem(f"{status_icon} {label}", label)

        # Restore previous selection if possible, otherwise select latest
        idx = self.stream_combo.findData(current_sel)
        if idx >= 0:
            self.stream_combo.setCurrentIndex(idx)
        elif self.stream_combo.count() > 0:
            self.stream_combo.setCurrentIndex(self.stream_combo.count() - 1)

        self.stream_combo.blockSignals(False)
        self.on_stream_changed()

    def on_stream_changed(self):
        label = self.stream_combo.currentData()
        if not label or label not in self.running_procs:
            return

        info = self.running_procs[label]
        log_file = info.get("log_file", "")
        if log_file and os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                    self.terminal.set_text(content)
                    if hasattr(self.workflow_hud, "update_from_log_content"):
                        self.workflow_hud.update_from_log_content(content)
            except Exception:
                pass

    def abort_current_stream(self):
        label = self.stream_combo.currentData()
        if label and label in self.running_procs:
            info = self.running_procs[label]
            proc = info.get("proc")
            if proc and proc.pid:
                try:
                    import subprocess
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception:
                    proc.terminate()
            info["status"] = "done"
            self.update_running_processes(self.running_procs)

    def close_widget(self):
        self.hide()
        self.closed.emit()


class PopoutDispatcherDialog(QDialog):
    """
    Dedicated Standalone Floating Multi-Window for Task Dispatching & Multi-Agent Telemetry.
    Supports spawning multiple concurrent floating windows, Pin to Top, and multi-task execution.
    """
    task_dispatched = Signal(str, str, str)
    multi_tasks_dispatched = Signal(list)
    new_window_requested = Signal()

    _active_dialogs: List['PopoutDispatcherDialog'] = []
    _window_counter: int = 0

    def __init__(self, parent=None, initial_text: str = "", running_procs: Optional[dict] = None):
        super().__init__(None)  # Top-level standalone window
        PopoutDispatcherDialog._window_counter += 1
        self.win_id = PopoutDispatcherDialog._window_counter
        self.setWindowTitle(f"⚡ Multi-Agent Task Dispatcher & Telemetry (Window #{self.win_id})")
        self.resize(920, 620)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b1120;
                border: 2px solid #38bdf8;
                border-radius: 12px;
            }
        """)

        # Cascade offset for multi-windows
        offset = ((self.win_id - 1) % 8) * 32
        if parent:
            try:
                p_geo = parent.geometry()
                self.move(p_geo.x() + 80 + offset, p_geo.y() + 80 + offset)
            except Exception:
                pass

        # Keep track of active dialogs
        PopoutDispatcherDialog._active_dialogs.append(self)

        d_layout = QVBoxLayout(self)
        d_layout.setContentsMargins(10, 10, 10, 10)
        d_layout.setSpacing(6)

        # Title / Multi-Window Top Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        win_lbl = QLabel(f"🪟 MULTI-AGENT FLOATING WORKBENCH · WINDOW #{self.win_id}")
        win_lbl.setStyleSheet("font-size: 12px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px;")
        top_bar.addWidget(win_lbl)
        top_bar.addStretch()

        # New Window Quick Button
        btn_add_win = QPushButton("⊞ Spawn Window")
        btn_add_win.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add_win.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 5px;
                padding: 3px 8px;
                font-size: 10.5px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #0b1120;
            }
        """)
        btn_add_win.clicked.connect(self.new_window_requested.emit)
        top_bar.addWidget(btn_add_win)

        # Pin / Always on Top Toggle
        self.btn_pin = QPushButton("📌 Always on Top")
        self.btn_pin.setCheckable(True)
        self.btn_pin.setChecked(False)
        self.btn_pin.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_pin.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.12);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 5px;
                padding: 3px 8px;
                font-size: 10.5px;
                font-weight: 700;
            }
            QPushButton:checked {
                background: #38bdf8;
                color: #0b1120;
            }
        """)
        self.btn_pin.toggled.connect(self.toggle_always_on_top)
        top_bar.addWidget(self.btn_pin)

        d_layout.addLayout(top_bar)

        # Hosted Dispatcher Widget
        self.dispatcher_widget = PopoutDispatcherWidget(self, is_standalone=True)
        self.dispatcher_widget.task_dispatched.connect(self.task_dispatched.emit)
        self.dispatcher_widget.multi_tasks_dispatched.connect(self.multi_tasks_dispatched.emit)
        self.dispatcher_widget.spawn_new_window_requested.connect(self.new_window_requested.emit)
        self.dispatcher_widget.closed.connect(self.close)

        if initial_text:
            self.dispatcher_widget.prompt_edit.setPlainText(initial_text)

        if running_procs:
            self.dispatcher_widget.update_running_processes(running_procs)

        d_layout.addWidget(self.dispatcher_widget)

    def toggle_always_on_top(self, enabled: bool):
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()

    def update_running_processes(self, procs: dict):
        if hasattr(self, 'dispatcher_widget') and self.dispatcher_widget:
            self.dispatcher_widget.update_running_processes(procs)

    def closeEvent(self, event):
        if self in PopoutDispatcherDialog._active_dialogs:
            PopoutDispatcherDialog._active_dialogs.remove(self)
        super().closeEvent(event)

