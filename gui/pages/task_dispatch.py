"""
gui/pages/task_dispatch.py - Task Dispatch Console & Live Telemetry Monitor
"""

import os
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QRadioButton, QCheckBox, QComboBox, QSlider,
    QGroupBox, QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QKeySequence, QShortcut

from gui.widgets.terminal_view import TerminalView
from gui.widgets.pool_monitor import PoolMonitor
from utils.latency_manager import load_latency_config, save_latency_config, PROFILES


class TaskDispatchPage(QWidget):
    launch_requested = Signal(str, str, str)
    abort_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.manual_agent_boxes = {}
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)

        # Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🚀 TASK DISPATCH CONSOLE")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Configure Mission Parameters & Monitor Live Multi-Agent Output")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 8px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        self.layout.addLayout(t_box)

        # 2 Column Form & Monitor Split
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)

        # --- LEFT: CONFIGURATION FORM ---
        left_box = QVBoxLayout()
        left_box.setSpacing(12)

        sec1 = QLabel("⚙️ Mission Configuration")
        sec1.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 4px;")
        left_box.addWidget(sec1)

        # Latency Group Box
        self.latency_grp = QGroupBox("⚡ Inter-Agent Communication Latency Tuning")
        lat_layout = QVBoxLayout(self.latency_grp)
        lat_layout.setSpacing(8)

        # Presets Row
        preset_row = QHBoxLayout()
        btn_turbo = QPushButton("🚀 Turbo (0.5s)")
        btn_turbo.clicked.connect(lambda: self.apply_latency_profile("turbo"))
        btn_bal = QPushButton("⚖️ Balanced (1.5s)")
        btn_bal.clicked.connect(lambda: self.apply_latency_profile("balanced"))
        btn_paced = QPushButton("🐢 Paced (3.5s)")
        btn_paced.clicked.connect(lambda: self.apply_latency_profile("paced"))
        
        preset_row.addWidget(btn_turbo)
        preset_row.addWidget(btn_bal)
        preset_row.addWidget(btn_paced)
        lat_layout.addLayout(preset_row)

        self.lat_info_lbl = QLabel()
        self.lat_info_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        lat_layout.addWidget(self.lat_info_lbl)

        # Custom Sliders
        sl_grid = QHBoxLayout()
        v1 = QVBoxLayout()
        v1.addWidget(QLabel("Dispatch Delay (s):"))
        self.sl_dispatch = QSlider(Qt.Horizontal)
        self.sl_dispatch.setRange(2, 80)
        self.sl_dispatch.setValue(15)
        self.sl_dispatch.valueChanged.connect(self.save_custom_latency)
        v1.addWidget(self.sl_dispatch)
        
        v1.addWidget(QLabel("Settling Interval (s):"))
        self.sl_settle = QSlider(Qt.Horizontal)
        self.sl_settle.setRange(3, 50)
        self.sl_settle.setValue(15)
        self.sl_settle.valueChanged.connect(self.save_custom_latency)
        v1.addWidget(self.sl_settle)
        sl_grid.addLayout(v1)

        v2 = QVBoxLayout()
        v2.addWidget(QLabel("Debate Latency (s):"))
        self.sl_debate = QSlider(Qt.Horizontal)
        self.sl_debate.setRange(5, 100)
        self.sl_debate.setValue(20)
        self.sl_debate.valueChanged.connect(self.save_custom_latency)
        v2.addWidget(self.sl_debate)

        v2.addWidget(QLabel("Max Timeout (s):"))
        self.sl_timeout = QSlider(Qt.Horizontal)
        self.sl_timeout.setRange(30, 300)
        self.sl_timeout.setValue(120)
        self.sl_timeout.valueChanged.connect(self.save_custom_latency)
        v2.addWidget(self.sl_timeout)
        sl_grid.addLayout(v2)

        lat_layout.addLayout(sl_grid)
        left_box.addWidget(self.latency_grp)

        # Mission Prompt
        left_box.addWidget(QLabel("<b>Mission Prompt / Instructions:</b>"))
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText("Describe your project, code requirements, research topic, or design asset... (Ctrl+Enter to deploy)")
        self.prompt_edit.setFixedHeight(120)
        left_box.addWidget(self.prompt_edit)

        # Agent Allocation Strategy
        left_box.addWidget(QLabel("<b>Agent Allocation Strategy:</b>"))
        mode_row = QHBoxLayout()
        self.rb_auto = QRadioButton("🤖 Dynamic AI Auto-Select")
        self.rb_auto.setChecked(True)
        self.rb_auto.toggled.connect(self.on_alloc_mode_changed)

        self.rb_manual = QRadioButton("✋ Manual Specialist Squad Selection")
        self.rb_manual.toggled.connect(self.on_alloc_mode_changed)

        mode_row.addWidget(self.rb_auto)
        mode_row.addWidget(self.rb_manual)
        left_box.addLayout(mode_row)

        # Manual Agents Checkboxes Frame
        self.manual_frame = QFrame()
        self.manual_frame.setStyleSheet("background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 6px;")
        m_layout = QVBoxLayout(self.manual_frame)
        m_layout.setSpacing(4)
        m_layout.addWidget(QLabel("<span style='color:#38bdf8;font-weight:700;'>Select Agents for Squad:</span> (Select Gemini for direct sole execution or combine with specialists)"))

        agents_roster = [
            ("gemini", "Google Gemini — Master Orchestrator & Direct Execution"),
            ("deepseek", "DeepSeek — Creative & Coder"),
            ("chatgpt", "ChatGPT — Copy & Synthesis"),
            ("claude", "Claude — Critique & Review"),
            ("perplexity", "Perplexity AI — Live Web Search"),
            ("copilot", "Microsoft Copilot — Workflow Specialist"),
            ("meta_ai", "Meta AI — Social & Engagement"),
            ("mistral", "Mistral Le Chat — Multilingual Logic"),
            ("dalle", "DALL-E 3 — Visual Designer"),
            ("nvidia_ai", "Nvidia NIM — High-Performance GPU"),
        ]
        for aid, label in agents_roster:
            cb = QCheckBox(label)
            if aid == "gemini":
                cb.setChecked(True)
            self.manual_agent_boxes[aid] = cb
            m_layout.addWidget(cb)

        self.manual_frame.hide()
        left_box.addWidget(self.manual_frame)

        # Mission Codename
        left_box.addWidget(QLabel("<b>Mission Codename (Optional):</b>"))
        self.codename_edit = QLineEdit()
        self.codename_edit.setPlaceholderText("e.g. Modern Web Dashboard v1")
        left_box.addWidget(self.codename_edit)

        # Deploy Button
        self.deploy_btn = QPushButton("🚀 Deploy Mission to Agent Pool")
        self.deploy_btn.setProperty("class", "primary-btn")
        self.deploy_btn.setFixedHeight(42)
        self.deploy_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.deploy_btn.setToolTip("Deploy Mission to Agent Pool (Ctrl+Enter)")
        self.deploy_btn.clicked.connect(self.on_deploy_clicked)
        left_box.addWidget(self.deploy_btn)

        # Page-level shortcuts
        self.deploy_sc1 = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.deploy_sc1.setContext(Qt.WidgetWithChildrenShortcut)
        self.deploy_sc1.activated.connect(self.on_deploy_clicked)

        self.deploy_sc2 = QShortcut(QKeySequence("Ctrl+Enter"), self)
        self.deploy_sc2.setContext(Qt.WidgetWithChildrenShortcut)
        self.deploy_sc2.activated.connect(self.on_deploy_clicked)

        split_layout.addLayout(left_box, stretch=1)

        # --- RIGHT: LIVE TELEMETRY & EXECUTION LOG ---
        right_box = QVBoxLayout()
        right_box.setSpacing(10)

        sec2 = QLabel("📡 Live Telemetry & Execution Log")
        sec2.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 4px;")
        right_box.addWidget(sec2)

        # Mission Selector Row
        sel_row = QHBoxLayout()
        sel_row.addWidget(QLabel("<b>Mission Stream:</b>"))
        self.stream_combo = QComboBox()
        self.stream_combo.currentIndexChanged.connect(self.on_stream_selected)
        sel_row.addWidget(self.stream_combo, stretch=2)
        right_box.addLayout(sel_row)

        # Mission Status Info Bar
        self.status_bar_lbl = QLabel("No active mission selected.")
        self.status_bar_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; background: rgba(15, 23, 42, 0.7); padding: 8px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.05);")
        right_box.addWidget(self.status_bar_lbl)

        # Real-Time Multi-Agent Workflow HUD
        from gui.widgets.workflow_hud_widget import WorkflowHUDWidget
        self.workflow_hud = WorkflowHUDWidget()
        right_box.addWidget(self.workflow_hud)

        # Live Terminal View
        self.terminal = TerminalView()
        right_box.addWidget(self.terminal, stretch=1)

        # Monitor Action Buttons
        btn_row = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Refresh Telemetry")
        self.refresh_btn.setToolTip("Refresh Live Terminal Output (F5 / Ctrl+R)")
        self.refresh_btn.clicked.connect(self.refresh_terminal)
        btn_row.addWidget(self.refresh_btn)

        self.abort_btn = QPushButton("⏹ Abort Mission")
        self.abort_btn.setProperty("class", "danger-btn")
        self.abort_btn.setToolTip("Abort Mission (Ctrl+Shift+X)")
        self.abort_btn.clicked.connect(self.on_abort_clicked)
        btn_row.addWidget(self.abort_btn)

        self.abort_sc = QShortcut(QKeySequence("Ctrl+Shift+X"), self)
        self.abort_sc.setContext(Qt.WidgetWithChildrenShortcut)
        self.abort_sc.activated.connect(self.on_abort_clicked)

        right_box.addLayout(btn_row)
        split_layout.addLayout(right_box, stretch=1)

        self.layout.addLayout(split_layout)

        # Bottom: Live Agent Pool Monitor
        sec3 = QLabel("⚡ Live Agent Pool Hierarchy")
        sec3.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 4px; margin-top: 10px;")
        self.layout.addWidget(sec3)

        self.pool_monitor = PoolMonitor()
        self.pool_monitor.direct_task_submitted.connect(self.prefill_task)
        self.layout.addWidget(self.pool_monitor)

        self.layout.addStretch()
        scroll.setWidget(container)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(scroll)

        self.refresh_latency_ui()

    def prefill_task(self, task_str: str):
        self.prompt_edit.setPlainText(task_str)
        self.on_deploy_clicked()

    def on_alloc_mode_changed(self):
        self.manual_frame.setVisible(self.rb_manual.isChecked())

    def apply_latency_profile(self, profile_name: str):
        if profile_name in PROFILES:
            save_latency_config(PROFILES[profile_name])
            self.refresh_latency_ui()

    def save_custom_latency(self):
        curr = load_latency_config()
        curr["profile"] = "custom"
        curr["dispatch_delay_sec"] = self.sl_dispatch.value() / 10.0
        curr["check_interval_sec"] = self.sl_settle.value() / 10.0
        curr["debate_delay_sec"] = self.sl_debate.value() / 10.0
        curr["max_timeout_sec"] = self.sl_timeout.value()
        save_latency_config(curr)
        self.update_latency_label(curr)

    def refresh_latency_ui(self):
        curr = load_latency_config()
        self.sl_dispatch.blockSignals(True)
        self.sl_settle.blockSignals(True)
        self.sl_debate.blockSignals(True)
        self.sl_timeout.blockSignals(True)

        self.sl_dispatch.setValue(int(curr.get("dispatch_delay_sec", 1.5) * 10))
        self.sl_settle.setValue(int(curr.get("check_interval_sec", 1.5) * 10))
        self.sl_debate.setValue(int(curr.get("debate_delay_sec", 2.0) * 10))
        self.sl_timeout.setValue(int(curr.get("max_timeout_sec", 120)))

        self.sl_dispatch.blockSignals(False)
        self.sl_settle.blockSignals(False)
        self.sl_debate.blockSignals(False)
        self.sl_timeout.blockSignals(False)

        self.update_latency_label(curr)

    def update_latency_label(self, curr: dict):
        self.lat_info_lbl.setText(f"Active Profile: <b><span style='color:#38bdf8;'>{curr.get('profile', 'balanced').upper()}</span></b> (Dispatch: {curr.get('dispatch_delay_sec', 1.5)}s · Settling: {curr.get('check_interval_sec', 1.5)}s · Debate: {curr.get('debate_delay_sec', 2.0)}s)")

    def on_deploy_clicked(self):
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Missing Instructions", "Please enter a mission prompt / instructions.")
            return

        if self.rb_auto.isChecked():
            agents_str = "auto"
        else:
            selected = []
            for aid, cb in self.manual_agent_boxes.items():
                if cb.isChecked():
                    selected.append(aid)
            if not selected:
                # Default to Gemini if nothing selected in manual mode
                selected = ["gemini"]
            agents_str = ",".join(selected)

        codename = self.codename_edit.text().strip() or f"Mission @ {time.strftime('%H:%M:%S')}"
        self.prompt_edit.clear()
        self.codename_edit.clear()
        self.launch_requested.emit(prompt, agents_str, codename)

    def update_running_processes(self, procs: dict):
        self.running_procs = procs
        current_selection = self.stream_combo.currentText()
        
        self.stream_combo.blockSignals(True)
        self.stream_combo.clear()
        for label in procs.keys():
            self.stream_combo.addItem(label)
        
        idx = self.stream_combo.findText(current_selection)
        if idx >= 0:
            self.stream_combo.setCurrentIndex(idx)
        elif self.stream_combo.count() > 0:
            self.stream_combo.setCurrentIndex(self.stream_combo.count() - 1)
        self.stream_combo.blockSignals(False)

        self.on_stream_selected()
        self.pool_monitor.refresh_pool()

    def on_stream_selected(self):
        label = self.stream_combo.currentText()
        if not hasattr(self, 'running_procs') or label not in self.running_procs:
            self.status_bar_lbl.setText("No active mission selected.")
            return

        info = self.running_procs[label]
        status = info.get("status", "unknown").upper()
        col = "#10b981" if status == "DONE" else ("#fbbf24" if status == "RUNNING" else "#ef4444")
        
        self.status_bar_lbl.setText(
            f"<b>Status:</b> <span style='color:{col};font-weight:800;'>{status}</span> &nbsp;|&nbsp; "
            f"<b>Started:</b> {info.get('started', '')} &nbsp;|&nbsp; "
            f"<b>Pool:</b> <code>[{info.get('agents', '')}]</code><br>"
            f"<b>Goal:</b> {info.get('task', '')}"
        )
        self.refresh_terminal()

    def refresh_terminal(self):
        label = self.stream_combo.currentText()
        if not hasattr(self, 'running_procs') or label not in self.running_procs:
            return

        info = self.running_procs[label]
        log_file = info.get("log_file")
        if log_file and os.path.exists(log_file):
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    self.terminal.set_text("".join(lines[-150:]))
            except Exception:
                pass

    def on_abort_clicked(self):
        label = self.stream_combo.currentText()
        if label:
            self.abort_requested.emit(label)
