"""
gui/widgets/popout_dispatcher_widget.py - Detachable Multi-Agent Task Dispatcher & Telemetry Workbench
Conforms strictly to design_system_ui_theme_documentation.md
"""

import os
import time
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QTextEdit,
    QPushButton, QComboBox, QCheckBox, QTabWidget, QDialog, QFrame,
    QMessageBox, QApplication, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from gui.widgets.terminal_view import TerminalView
from gui.widgets.workflow_hud_widget import WorkflowHUDWidget
from gui.widgets.slash_autocomplete import attach_slash_autocomplete
from core.command_router import split_multi_task_prompt, route_task_with_laya


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
        self.setProperty("class", "card")
        self.is_standalone = is_standalone
        self.running_procs: Dict[str, Any] = {}
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # 1. Top Header Bar
        hdr = QHBoxLayout()
        hdr.setSpacing(8)

        t_lbl = QLabel("MULTI-AGENT TASK DISPATCHER")
        t_lbl.setProperty("class", "metric-value")
        hdr.addWidget(t_lbl)

        self.active_badge = QLabel("0 Active Missions")
        self.active_badge.setProperty("class", "badge-idle")
        hdr.addWidget(self.active_badge)
        hdr.addStretch()

        if not self.is_standalone:
            # Pop out to Standalone Window Button
            btn_popout = QPushButton("Pop out Window")
            btn_popout.setProperty("class", "btn-secondary")
            btn_popout.setCursor(QCursor(Qt.PointingHandCursor))
            btn_popout.setToolTip("Open in independent floating Multi-Agent Task Window")
            btn_popout.clicked.connect(self.spawn_new_window_requested.emit)
            hdr.addWidget(btn_popout)

            # Close Button
            btn_close = QPushButton("✕")
            btn_close.setProperty("class", "btn-secondary")
            btn_close.setFixedSize(28, 28)
            btn_close.setCursor(QCursor(Qt.PointingHandCursor))
            btn_close.clicked.connect(self.close_widget)
            hdr.addWidget(btn_close)

        self.main_layout.addLayout(hdr)

        # 2. Main Tabbed Workspace
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        # Tab 1: Dispatch Studio (Multi-Task)
        self.tab_dispatch = QWidget()
        self.setup_dispatch_tab()
        self.tabs.addTab(self.tab_dispatch, "Dispatch Studio")

        # Tab 2: Live Telemetry & HUD
        self.tab_stream = QWidget()
        self.setup_stream_tab()
        self.tabs.addTab(self.tab_stream, "Live Telemetry")

        # Tab 3: Specialist Agent Roster
        self.tab_roster = QWidget()
        self.setup_roster_tab()
        self.tabs.addTab(self.tab_roster, "Specialist Roster")

        self.main_layout.addWidget(self.tabs)

    def setup_dispatch_tab(self):
        lay = QVBoxLayout(self.tab_dispatch)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        # Instructions / Multi-Task hint
        hint_lbl = QLabel(
            "Multi-Task Prompting: Enter a single task or compound prompt (e.g. numbered list 1. ... 2. ..., "
            "or chained slash commands /deepseek - code ; /claude - review). Tasks will be automatically split and dispatched!"
        )
        hint_lbl.setProperty("class", "metric-label")
        hint_lbl.setWordWrap(True)
        lay.addWidget(hint_lbl)

        # Prompt Input
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText(
            "Enter task, compound goal, or /{agent} commands...\n\n"
            "Examples:\n"
            "• Single Goal: Build a high-performance REST API with authentication\n"
            "• Multi-Task Chained: /deepseek - build auth backend ; /claude - audit security ; /perplexity - find CVEs\n"
            "• Numbered Tasks:\n"
            "  1. Scrape latest tech news\n"
            "  2. Summarize top stories with ChatGPT\n"
            "  3. Generate executive dashboard chart"
        )
        self.prompt_edit.setMinimumHeight(140)
        attach_slash_autocomplete(self.prompt_edit)
        lay.addWidget(self.prompt_edit, stretch=1)

        # Options Row
        opt_row = QHBoxLayout()
        opt_row.setSpacing(10)

        self.cb_auto_split = QCheckBox("Auto-Split Compound Prompts into Multi-Agent Tasks")
        self.cb_auto_split.setChecked(True)
        opt_row.addWidget(self.cb_auto_split)

        opt_row.addStretch()

        self.combo_target_agent = QComboBox()
        self.combo_target_agent.addItems([
            "Dynamic AI Auto-Select (LAYA)",
            "Google Gemini (Master Leader)",
            "DeepSeek (Coder & Reasoning)",
            "ChatGPT (Synthesis & Copy)",
            "Claude (Security & Review)",
            "Perplexity AI (Web Search)",
            "All Specialists (Full Squad)"
        ])
        opt_row.addWidget(self.combo_target_agent)
        lay.addLayout(opt_row)

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.btn_dispatch = QPushButton("Dispatch Mission(s)")
        self.btn_dispatch.setProperty("class", "btn-primary")
        self.btn_dispatch.setFixedHeight(38)
        self.btn_dispatch.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_dispatch.clicked.connect(self.dispatch_from_studio)
        btn_row.addWidget(self.btn_dispatch, stretch=3)

        btn_clear = QPushButton("Clear")
        btn_clear.setProperty("class", "btn-secondary")
        btn_clear.setFixedHeight(38)
        btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        btn_clear.clicked.connect(lambda: self.prompt_edit.clear())
        btn_row.addWidget(btn_clear, stretch=1)

        lay.addLayout(btn_row)

    def setup_stream_tab(self):
        lay = QVBoxLayout(self.tab_stream)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        # Stream Selector Row
        top_row = QHBoxLayout()
        lbl_ms = QLabel("Active Mission Stream:")
        lbl_ms.setProperty("class", "metric-label")
        top_row.addWidget(lbl_ms)

        self.stream_combo = QComboBox()
        self.stream_combo.currentIndexChanged.connect(self.on_stream_changed)
        top_row.addWidget(self.stream_combo, stretch=2)

        self.btn_abort_stream = QPushButton("Abort Mission")
        self.btn_abort_stream.setProperty("class", "btn-secondary")
        self.btn_abort_stream.setCursor(QCursor(Qt.PointingHandCursor))
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

        info_lbl = QLabel("1-Click Quick Specialist Dispatch: Click any model below to prefill and dispatch:")
        info_lbl.setProperty("class", "metric-label")
        lay.addWidget(info_lbl)

        grid = QGridLayout()
        grid.setSpacing(8)

        roster = [
            ("Google Gemini", "gemini", "Master Orchestrator"),
            ("DeepSeek", "deepseek", "Coder & Reasoning"),
            ("ChatGPT", "chatgpt", "Synthesis & Report"),
            ("Claude", "claude", "Audit & Review"),
            ("Perplexity", "perplexity", "Live Web Search"),
            ("Copilot", "copilot", "Automation & Office"),
            ("DALL-E 3", "dalle", "Image Generation"),
            ("Nvidia NIM", "nvidia_ai", "High-Performance GPU"),
        ]

        for idx, (label, aid, desc) in enumerate(roster):
            btn = QPushButton(f"{label}\n({desc})")
            btn.setProperty("class", "btn-secondary")
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn.clicked.connect(lambda *args, a=aid: self.quick_select_agent(a))
            grid.addWidget(btn, idx // 4, idx % 4)

        lay.addLayout(grid)
        lay.addStretch()

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
        self.active_badge.setProperty("class", "badge-busy" if running_count > 0 else "badge-idle")
        self.active_badge.style().unpolish(self.active_badge)
        self.active_badge.style().polish(self.active_badge)

        for label, info in procs.items():
            status_icon = "●" if info.get("status") == "running" else ("✕" if info.get("status") == "error" else "✓")
            self.stream_combo.addItem(f"{status_icon} {label}", label)

        idx = self.stream_combo.findData(current_sel)
        if idx >= 0:
            self.stream_combo.setCurrentIndex(idx)
        elif self.stream_combo.count() > 0:
            self.stream_combo.setCurrentIndex(self.stream_combo.count() - 1)
        self.stream_combo.blockSignals(False)

        self.on_stream_changed()

    def on_stream_changed(self):
        curr_key = self.stream_combo.currentData()
        if not curr_key or curr_key not in self.running_procs:
            return

        info = self.running_procs[curr_key]
        log_file = info.get("log_file")
        if log_file and os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    self.terminal.set_text(content)
            except Exception:
                pass

    def abort_current_stream(self):
        curr_key = self.stream_combo.currentData()
        if curr_key and hasattr(self.parent(), "abort_mission"):
            self.parent().abort_mission(curr_key)

    def close_widget(self):
        self.hide()
        self.closed.emit()


class PopoutDispatcherDialog(QDialog):
    """
    Floating, Multi-Window Independent Dispatcher Dialog.
    Can be spawned into multiple concurrent windows.
    """
    task_dispatched = Signal(str, str, str)
    multi_tasks_dispatched = Signal(list)
    new_window_requested = Signal()

    _active_dialogs: List['PopoutDispatcherDialog'] = []
    _window_counter: int = 0

    def __init__(self, parent=None, initial_text: str = "", running_procs: Optional[dict] = None):
        super().__init__(None)  # Standalone floating window
        PopoutDispatcherDialog._window_counter += 1
        self.win_id = PopoutDispatcherDialog._window_counter
        self.setWindowTitle(f"Multi-Agent Task Dispatcher (Window #{self.win_id})")
        self.resize(880, 560)
        self.setMinimumSize(700, 440)
        self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint | Qt.WindowCloseButtonHint)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setProperty("class", "card")

        offset = ((self.win_id - 1) % 8) * 32
        if parent:
            try:
                p_geo = parent.geometry()
                self.move(p_geo.x() + 60 + offset, p_geo.y() + 60 + offset)
            except Exception:
                pass

        PopoutDispatcherDialog._active_dialogs.append(self)

        d_layout = QVBoxLayout(self)
        d_layout.setContentsMargins(12, 12, 12, 12)
        d_layout.setSpacing(8)

        # Title / Multi-Window Top Bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        win_lbl = QLabel(f"MULTI-AGENT WORKBENCH · WINDOW #{self.win_id}")
        win_lbl.setProperty("class", "sidebar-group-label")
        top_bar.addWidget(win_lbl)
        top_bar.addStretch()

        btn_add_win = QPushButton("Spawn Window")
        btn_add_win.setProperty("class", "btn-secondary")
        btn_add_win.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add_win.clicked.connect(self.new_window_requested.emit)
        top_bar.addWidget(btn_add_win)

        self.btn_pin = QPushButton("Always on Top")
        self.btn_pin.setProperty("class", "btn-secondary")
        self.btn_pin.setCheckable(True)
        self.btn_pin.setChecked(False)
        self.btn_pin.setCursor(QCursor(Qt.PointingHandCursor))
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

        d_layout.addWidget(self.dispatcher_widget, stretch=1)

    def toggle_always_on_top(self, checked: bool):
        flags = self.windowFlags()
        if checked:
            flags |= Qt.WindowStaysOnTopHint
            self.btn_pin.setProperty("class", "btn-primary")
        else:
            flags &= ~Qt.WindowStaysOnTopHint
            self.btn_pin.setProperty("class", "btn-secondary")
        self.btn_pin.style().unpolish(self.btn_pin)
        self.btn_pin.style().polish(self.btn_pin)
        self.setWindowFlags(flags)
        self.show()

    def update_running_processes(self, procs: dict):
        if hasattr(self, 'dispatcher_widget') and self.dispatcher_widget:
            self.dispatcher_widget.update_running_processes(procs)

    def closeEvent(self, event):
        if self in PopoutDispatcherDialog._active_dialogs:
            PopoutDispatcherDialog._active_dialogs.remove(self)
        event.accept()
