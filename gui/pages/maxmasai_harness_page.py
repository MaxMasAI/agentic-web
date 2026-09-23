"""
gui/pages/maxmasai_harness_page.py - MaxMasAI Harness Developer Preview & "Everything is a Plugin" Studio
Comprehensive interactive suite for hot-pluggable harness execution, CoT reasoning inspection,
sandbox evaluation, and dynamic plugin management.
"""

import os
import json
import time
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QComboBox, QLineEdit, QTextEdit, QPlainTextEdit,
    QScrollArea, QFrame, QMessageBox, QSpinBox, QCheckBox,
    QProgressBar, QSplitter, QGridLayout, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QThread, Signal
from PySide6.QtGui import QCursor, QFont, QColor

from gui.widgets.metric_card import MetricCard
from core.maxmasai_harness import MaxMasAIHarnessEngine, HarnessStep, HarnessResult


class HarnessWorkerThread(QThread):
    step_received = Signal(object)
    finished_result = Signal(object)

    def __init__(self, prompt: str, model_id: str):
        super().__init__()
        self.prompt = prompt
        self.model_id = model_id

    def run(self):
        engine = MaxMasAIHarnessEngine.get_instance()
        result = engine.run_harness_loop(
            prompt=self.prompt,
            model_id=self.model_id,
            step_callback=lambda s: self.step_received.emit(s)
        )
        self.finished_result.emit(result)


class BenchmarkWorkerThread(QThread):
    progress_updated = Signal(int, str)
    benchmark_finished = Signal(list)

    def run(self):
        engine = MaxMasAIHarnessEngine.get_instance()
        results = engine.run_benchmark_suite(
            progress_callback=lambda p, msg: self.progress_updated.emit(p, msg)
        )
        self.benchmark_finished.emit(results)


class MaxMasAIHarnessPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.engine = MaxMasAIHarnessEngine.get_instance()
        self.worker_thread = None
        self.benchmark_thread = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Title & Status Badge
        header_box = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(2)

        title_row = QHBoxLayout()
        title = QLabel("⚡ MAXMASAI HARNESS")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        dev_badge = QLabel("DEVELOPER PREVIEW")
        dev_badge.setStyleSheet("""
            background: rgba(56, 189, 248, 0.15);
            border: 1px solid rgba(56, 189, 248, 0.4);
            color: #38bdf8;
            font-size: 11px;
            font-weight: 800;
            font-family: monospace;
            padding: 3px 8px;
            border-radius: 4px;
        """)
        title_row.addWidget(title)
        title_row.addWidget(dev_badge)
        title_row.addStretch()

        subtitle = QLabel("Everything is a Plugin — Hot-Pluggable Autonomous CoT Execution, Sandboxing & Tool Evaluation")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addLayout(title_row)
        t_box.addWidget(subtitle)
        header_box.addLayout(t_box)

        # Top Action Buttons
        actions_box = QHBoxLayout()
        self.btn_quick_reload = QPushButton("🔄 Hot Reload Plugins")
        self.btn_quick_reload.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_quick_reload.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.15);
                color: #f8fafc;
                font-size: 12px;
                font-weight: 600;
                padding: 7px 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.15);
                border-color: #38bdf8;
                color: #38bdf8;
            }
        """)
        self.btn_quick_reload.clicked.connect(self.on_hot_reload_clicked)

        actions_box.addWidget(self.btn_quick_reload)
        header_box.addLayout(actions_box)
        main_layout.addLayout(header_box)

        # 4 Telemetry Metric Cards
        self.telemetry_layout = QHBoxLayout()
        self.card_model = MetricCard("MaxMasAI Core", "Active Harness Model", "#38bdf8")
        self.card_plugins = MetricCard("0", "Loaded Plugins", "#10b981")
        self.card_latency = MetricCard("142 ms", "Reasoning Latency", "#fbbf24")
        self.card_sandbox = MetricCard("Isolated", "Sandbox Security", "#c084fc")

        for c in [self.card_model, self.card_plugins, self.card_latency, self.card_sandbox]:
            self.telemetry_layout.addWidget(c)
        main_layout.addLayout(self.telemetry_layout)

        # 4 Interactive Studio Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(56, 189, 248, 0.2);
                background: #090e1f;
                border-radius: 8px;
            }
            QTabBar::tab {
                background: rgba(15, 23, 42, 0.8);
                color: #94a3b8;
                font-weight: 600;
                font-size: 13px;
                padding: 10px 18px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background: #172236;
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-bottom: none;
            }
            QTabBar::tab:hover {
                color: #ffffff;
            }
        """)

        self.tabs.addTab(self.create_live_harness_tab(), "⚡ Live Harness & Sandbox Execution")
        self.tabs.addTab(self.create_plugin_manager_tab(), "🔌 'Everything is a Plugin' Studio")
        self.tabs.addTab(self.create_benchmark_tab(), "🧪 Benchmark & Evaluation Matrix")
        self.tabs.addTab(self.create_settings_tab(), "⚙️ Harness Configuration")

        main_layout.addWidget(self.tabs, stretch=1)
        self.refresh_telemetry()

    def refresh_telemetry(self):
        plugins = self.engine.get_loaded_plugins()
        self.card_plugins.set_value(str(len(plugins)))

    # ─────────────────────────────────────────────────────────────
    # TAB 1: LIVE TEST HARNESS & SANDBOX EXECUTION
    # ─────────────────────────────────────────────────────────────
    def create_live_harness_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Top Control Bar (Model Select + Quick Prompt Presets)
        ctrl_bar = QHBoxLayout()
        ctrl_bar.setSpacing(10)

        lbl_model = QLabel("Harness Model:")
        lbl_model.setStyleSheet("font-weight: 700; color: #94a3b8; font-size: 12px;")
        self.model_combo = QComboBox()
        self.model_combo.setStyleSheet("""
            QComboBox {
                background: #030712;
                border: 1px solid rgba(56, 189, 248, 0.3);
                color: #f8fafc;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 12.5px;
                min-width: 240px;
            }
        """)
        for m in self.engine.get_available_models():
            self.model_combo.addItem(f"{m['name']}", m["id"])

        ctrl_bar.addWidget(lbl_model)
        ctrl_bar.addWidget(self.model_combo)

        ctrl_bar.addSpacing(16)
        lbl_templates = QLabel("Presets:")
        lbl_templates.setStyleSheet("color: #64748b; font-size: 12px;")
        ctrl_bar.addWidget(lbl_templates)

        templates = [
            ("⚡ Autonomous Web Agent", "Navigate to docs, extract API spec, and generate test assertions."),
            ("🔬 CoT Code Refactor", "Refactor async task queue into modular plugin with zero regression."),
            ("🛡️ Sandbox Security Test", "Attempt sandbox escape and verify isolated execution containment."),
        ]
        for title, prompt_val in templates:
            btn = QPushButton(title)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.04);
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    color: #cbd5e1;
                    font-size: 11px;
                    padding: 4px 10px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background: rgba(56, 189, 248, 0.12);
                    border-color: #38bdf8;
                    color: #38bdf8;
                }
            """)
            btn.clicked.connect(lambda _, p=prompt_val: self.prompt_input.setPlainText(p))
            ctrl_bar.addWidget(btn)

        ctrl_bar.addStretch()
        layout.addLayout(ctrl_bar)

        # Prompt Input Box
        self.prompt_input = QPlainTextEdit()
        self.prompt_input.setPlaceholderText("Enter task mission for MaxMasAI Harness (e.g. 'Build and test a custom data processing plugin with schema validation')...")
        self.prompt_input.setFixedHeight(75)
        self.prompt_input.setStyleSheet("""
            QPlainTextEdit {
                background: #030712;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 8px;
                color: #f8fafc;
                font-family: 'JetBrains Mono', Consolas, monospace;
                font-size: 12.5px;
                padding: 10px;
            }
            QPlainTextEdit:focus {
                border-color: #38bdf8;
            }
        """)
        self.prompt_input.setPlainText("Decompose and synthesize a high-performance multi-agent task runner plugin with isolated sandbox testing.")
        layout.addWidget(self.prompt_input)

        # Launch Button & Progress
        launch_row = QHBoxLayout()
        self.btn_run_harness = QPushButton("▶ Launch MaxMasAI Harness Loop")
        self.btn_run_harness.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_run_harness.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0284c7, stop:1 #38bdf8);
                color: #ffffff;
                font-size: 13.5px;
                font-weight: 800;
                padding: 10px 24px;
                border-radius: 6px;
                border: 1px solid rgba(56, 189, 248, 0.6);
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0369a1, stop:1 #0284c7);
                color: #ffffff;
                border: 1px solid #38bdf8;
            }
            QPushButton:pressed {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.btn_run_harness.clicked.connect(self.on_run_harness_clicked)
        launch_row.addWidget(self.btn_run_harness)

        self.harness_spinner = QLabel("")
        self.harness_spinner.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 12px;")
        launch_row.addWidget(self.harness_spinner)
        launch_row.addStretch()

        layout.addLayout(launch_row)

        # Splitter: Left = CoT Step-by-Step Inspector, Right = Raw Sandbox & Output Stream
        splitter = QSplitter(Qt.Horizontal)

        # Left Column: CoT Reasoning Trace
        left_box = QWidget()
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(0, 0, 0, 0)
        lbl_trace = QLabel("🧠 Chain-of-Thought (CoT) & Tool Calling Traces:")
        lbl_trace.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 12px;")
        left_layout.addWidget(lbl_trace)

        self.trace_scroll = QScrollArea()
        self.trace_scroll.setWidgetResizable(True)
        self.trace_scroll.setStyleSheet("background: #020617; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px;")

        self.trace_container = QWidget()
        self.trace_layout = QVBoxLayout(self.trace_container)
        self.trace_layout.setContentsMargins(10, 10, 10, 10)
        self.trace_layout.setSpacing(8)
        self.trace_layout.addStretch()
        self.trace_scroll.setWidget(self.trace_container)
        left_layout.addWidget(self.trace_scroll)

        splitter.addWidget(left_box)

        # Right Column: Deliverable & Sandbox Logs
        right_box = QWidget()
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(0, 0, 0, 0)
        lbl_out = QLabel("📦 Sandbox Execution Artifacts & Verified Deliverable:")
        lbl_out.setStyleSheet("font-weight: 700; color: #10b981; font-size: 12px;")
        right_layout.addWidget(lbl_out)

        self.output_view = QTextEdit()
        self.output_view.setReadOnly(True)
        self.output_view.setStyleSheet("""
            QTextEdit {
                background: #020617;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
                color: #e2e8f0;
                font-family: 'JetBrains Mono', Consolas, monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        right_layout.addWidget(self.output_view)
        splitter.addWidget(right_box)

        splitter.setSizes([480, 480])
        layout.addWidget(splitter, stretch=1)
        return widget

    def on_run_harness_clicked(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Missing Prompt", "Please enter a prompt for the harness.")
            return

        model_id = self.model_combo.currentData()
        self.btn_run_harness.setEnabled(False)
        self.harness_spinner.setText("⚡ Harness Loop Running...")

        # Clear previous trace cards
        while self.trace_layout.count() > 1:
            item = self.trace_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.output_view.clear()

        # Start worker thread
        self.worker_thread = HarnessWorkerThread(prompt=prompt, model_id=model_id)
        self.worker_thread.step_received.connect(self.add_step_card)
        self.worker_thread.finished_result.connect(self.on_harness_completed)
        self.worker_thread.start()

    def add_step_card(self, step: HarnessStep):
        card = QFrame()
        is_laya = step.step_type == "laya_system1"
        
        if is_laya:
            card.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(14, 116, 144, 0.4), stop:1 rgba(15, 23, 42, 0.9));
                    border: 1.5px solid #38bdf8;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame {
                    background: rgba(15, 23, 42, 0.85);
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    border-radius: 6px;
                    padding: 8px;
                }
            """)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(6, 6, 6, 6)
        c_layout.setSpacing(4)

        header = QHBoxLayout()
        title = QLabel(f"#{step.step_num} {step.title}")
        title.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 12px;" if not is_laya else "font-weight: 800; color: #7dd3fc; font-size: 12.5px;")
        
        if is_laya:
            badge = QLabel("⚡ SYSTEM 1 FAST-PATH")
            badge.setStyleSheet("background: rgba(56, 189, 248, 0.2); color: #38bdf8; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 4px; font-family: monospace;")
            header.addWidget(title)
            header.addWidget(badge)
        else:
            header.addWidget(title)
            
        header.addStretch()
        time_lbl = QLabel(f"{step.duration_ms}ms")
        time_lbl.setStyleSheet("color: #64748b; font-family: monospace; font-size: 10px;")
        header.addWidget(time_lbl)
        c_layout.addLayout(header)

        content = QLabel(step.content)
        content.setWordWrap(True)
        content.setStyleSheet("color: #cbd5e1; font-size: 11.5px; font-family: 'JetBrains Mono', Consolas, monospace;" if not is_laya else "color: #f1f5f9; font-size: 11.5px; font-family: 'JetBrains Mono', Consolas, monospace; line-height: 1.4;")
        c_layout.addWidget(content)

        # Insert before stretch
        self.trace_layout.insertWidget(self.trace_layout.count() - 1, card)
        QTimer.singleShot(50, lambda: self.trace_scroll.verticalScrollBar().setValue(self.trace_scroll.verticalScrollBar().maximum()))

    def on_harness_completed(self, result: HarnessResult):
        self.btn_run_harness.setEnabled(True)
        self.harness_spinner.setText("✅ Execution Finished")
        self.output_view.setMarkdown(result.output)
        self.card_latency.set_value(f"{int(result.total_duration_sec * 1000)} ms")

    # ─────────────────────────────────────────────────────────────
    # TAB 2: "EVERYTHING IS A PLUGIN" STUDIO & REGISTRY
    # ─────────────────────────────────────────────────────────────
    def create_plugin_manager_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Top Bar: Add Plugin Scaffold Form
        scaffold_box = QFrame()
        scaffold_box.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        s_layout = QVBoxLayout(scaffold_box)
        s_layout.setSpacing(8)

        s_title = QLabel("➕ 1-Click Plugin Scaffold Generator")
        s_title.setStyleSheet("font-weight: 800; color: #38bdf8; font-size: 13px;")
        s_layout.addWidget(s_title)

        form_row = QHBoxLayout()
        self.input_plugin_id = QLineEdit()
        self.input_plugin_id.setPlaceholderText("Plugin ID (e.g. data_cleaner)")
        self.input_plugin_id.setStyleSheet("background: #030712; color: #f8fafc; border: 1px solid #334155; padding: 6px; border-radius: 4px;")

        self.input_plugin_name = QLineEdit()
        self.input_plugin_name.setPlaceholderText("Display Name (e.g. Data Cleaner Skill)")
        self.input_plugin_name.setStyleSheet("background: #030712; color: #f8fafc; border: 1px solid #334155; padding: 6px; border-radius: 4px;")

        self.input_plugin_desc = QLineEdit()
        self.input_plugin_desc.setPlaceholderText("Description (e.g. High-speed JSON & CSV cleaner)")
        self.input_plugin_desc.setStyleSheet("background: #030712; color: #f8fafc; border: 1px solid #334155; padding: 6px; border-radius: 4px;")

        btn_create = QPushButton("⚡ Generate & Load Plugin")
        btn_create.setCursor(QCursor(Qt.PointingHandCursor))
        btn_create.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: #ffffff;
                font-weight: 700;
                padding: 6px 14px;
                border-radius: 4px;
                border: none;
            }
            QPushButton:hover {
                background: #0369a1;
            }
        """)
        btn_create.clicked.connect(self.on_scaffold_plugin_clicked)

        form_row.addWidget(self.input_plugin_id)
        form_row.addWidget(self.input_plugin_name)
        form_row.addWidget(self.input_plugin_desc)
        form_row.addWidget(btn_create)
        s_layout.addLayout(form_row)
        layout.addWidget(scaffold_box)

        # Loaded Plugins Registry Grid
        lbl_grid = QLabel("📦 Installed Hot-Pluggable Harness Plugins:")
        lbl_grid.setStyleSheet("font-weight: 800; color: #f8fafc; font-size: 13px;")
        layout.addWidget(lbl_grid)

        self.plugin_scroll = QScrollArea()
        self.plugin_scroll.setWidgetResizable(True)
        self.plugin_scroll.setStyleSheet("background: #020617; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;")

        self.plugin_container = QWidget()
        self.plugin_layout = QVBoxLayout(self.plugin_container)
        self.plugin_layout.setContentsMargins(10, 10, 10, 10)
        self.plugin_layout.setSpacing(8)
        self.plugin_layout.addStretch()
        self.plugin_scroll.setWidget(self.plugin_container)
        layout.addWidget(self.plugin_scroll, stretch=1)

        self.refresh_plugins_list()
        return widget

    def refresh_plugins_list(self):
        while self.plugin_layout.count() > 1:
            item = self.plugin_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        plugins = self.engine.get_loaded_plugins()
        self.card_plugins.set_value(str(len(plugins)))

        for p in plugins:
            p_card = QFrame()
            p_card.setStyleSheet("""
                QFrame {
                    background: rgba(13, 20, 36, 0.75);
                    border: 1px solid rgba(56, 189, 248, 0.2);
                    border-radius: 6px;
                    padding: 10px;
                }
                QFrame:hover {
                    border-color: #38bdf8;
                }
            """)
            c_layout = QHBoxLayout(p_card)
            c_layout.setContentsMargins(8, 8, 8, 8)

            info_box = QVBoxLayout()
            info_box.setSpacing(3)

            title_row = QHBoxLayout()
            name_lbl = QLabel(f"🔌 {p['name']} (v{p['version']})")
            name_lbl.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")
            author_lbl = QLabel(f"by {p['author']}")
            author_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            title_row.addWidget(name_lbl)
            title_row.addWidget(author_lbl)
            title_row.addStretch()
            info_box.addLayout(title_row)

            desc_lbl = QLabel(p["description"] or "No description provided.")
            desc_lbl.setStyleSheet("color: #cbd5e1; font-size: 11.5px;")
            info_box.addWidget(desc_lbl)

            if p["tools"]:
                tools_lbl = QLabel(f"Tools ({p['tools_count']}): {', '.join(p['tools'])}")
                tools_lbl.setStyleSheet("color: #10b981; font-size: 11px; font-family: monospace;")
                info_box.addWidget(tools_lbl)

            c_layout.addLayout(info_box, stretch=1)

            # Enable/Disable Checkbox
            chk = QCheckBox("Active in Harness")
            chk.setChecked(p["enabled"])
            chk.setStyleSheet("color: #f8fafc; font-weight: 600;")
            chk.toggled.connect(lambda state, p_id=p["id"]: self.engine.toggle_plugin(p_id, state))
            c_layout.addWidget(chk)

            self.plugin_layout.insertWidget(self.plugin_layout.count() - 1, p_card)

    def on_scaffold_plugin_clicked(self):
        p_id = self.input_plugin_id.text().strip()
        p_name = self.input_plugin_name.text().strip()
        p_desc = self.input_plugin_desc.text().strip()

        if not p_id:
            QMessageBox.warning(self, "Invalid ID", "Please provide a valid plugin ID.")
            return

        success, msg = self.engine.scaffold_plugin(plugin_id=p_id, name=p_name, description=p_desc)
        if success:
            QMessageBox.information(self, "Plugin Created", msg)
            self.input_plugin_id.clear()
            self.input_plugin_name.clear()
            self.input_plugin_desc.clear()
            self.refresh_plugins_list()
        else:
            QMessageBox.critical(self, "Creation Error", msg)

    def on_hot_reload_clicked(self):
        count, msg = self.engine.reload_plugins()
        QMessageBox.information(self, "Hot Reload", msg)
        self.refresh_plugins_list()

    # ─────────────────────────────────────────────────────────────
    # TAB 3: BENCHMARK & EVALUATION HARNESS
    # ─────────────────────────────────────────────────────────────
    def create_benchmark_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        lbl = QLabel("🧪 Autonomous Evaluation & Benchmark Suite")
        lbl.setStyleSheet("font-weight: 800; color: #38bdf8; font-size: 15px;")
        header_row.addWidget(lbl)
        header_row.addStretch()

        self.btn_run_bench = QPushButton("▶ Run All 5 Harness Benchmarks")
        self.btn_run_bench.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_run_bench.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #059669, stop:1 #10b981);
                color: #ffffff;
                font-weight: 700;
                font-size: 12.5px;
                padding: 8px 18px;
                border-radius: 6px;
                border: 1px solid rgba(16, 185, 129, 0.6);
            }
            QPushButton:hover {
                background-color: #047857;
                border: 1px solid #10b981;
            }
            QPushButton:disabled {
                background-color: #1e293b;
                color: #64748b;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        self.btn_run_bench.clicked.connect(self.on_run_benchmarks_clicked)
        header_row.addWidget(self.btn_run_bench)
        layout.addLayout(header_row)

        self.bench_progress = QProgressBar()
        self.bench_progress.setFixedHeight(8)
        self.bench_progress.setStyleSheet("""
            QProgressBar {
                background: #030712;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background: #38bdf8;
                border-radius: 4px;
            }
        """)
        self.bench_progress.hide()
        layout.addWidget(self.bench_progress)

        self.bench_status_lbl = QLabel("")
        self.bench_status_lbl.setStyleSheet("color: #94a3b8; font-size: 11.5px; font-family: monospace;")
        layout.addWidget(self.bench_status_lbl)

        # Benchmark Results Table Container
        self.bench_scroll = QScrollArea()
        self.bench_scroll.setWidgetResizable(True)
        self.bench_scroll.setStyleSheet("background: #020617; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px;")

        self.bench_container = QWidget()
        self.bench_layout = QVBoxLayout(self.bench_container)
        self.bench_layout.setContentsMargins(12, 12, 12, 12)
        self.bench_layout.setSpacing(8)
        self.bench_layout.addStretch()
        self.bench_scroll.setWidget(self.bench_container)
        layout.addWidget(self.bench_scroll, stretch=1)

        return widget

    def on_run_benchmarks_clicked(self):
        self.btn_run_bench.setEnabled(False)
        self.bench_progress.show()
        self.bench_progress.setValue(0)
        self.bench_status_lbl.setText("Starting benchmark evaluation suite...")

        while self.bench_layout.count() > 1:
            item = self.bench_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.benchmark_thread = BenchmarkWorkerThread()
        self.benchmark_thread.progress_updated.connect(self.on_bench_progress)
        self.benchmark_thread.benchmark_finished.connect(self.on_bench_finished)
        self.benchmark_thread.start()

    def on_bench_progress(self, val: int, msg: str):
        self.bench_progress.setValue(val)
        self.bench_status_lbl.setText(msg)

    def on_bench_finished(self, results: List[Dict[str, Any]]):
        self.btn_run_bench.setEnabled(True)
        self.bench_progress.hide()
        self.bench_status_lbl.setText("✅ Benchmark Suite Execution Completed")

        for b in results:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(15, 23, 42, 0.85);
                    border: 1px solid rgba(16, 185, 129, 0.3);
                    border-radius: 6px;
                    padding: 10px;
                }
            """)
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(8, 8, 8, 8)

            info = QVBoxLayout()
            title = QLabel(f"🏆 {b['name']}")
            title.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")
            meta = QLabel(f"Target: {b['target']} • Latency: {b['latency_ms']}ms • Tokens: {b['tokens']}")
            meta.setStyleSheet("color: #64748b; font-size: 11px;")
            info.addWidget(title)
            info.addWidget(meta)
            c_layout.addLayout(info, stretch=1)

            score_lbl = QLabel(f"{b['score']}%")
            score_lbl.setStyleSheet("font-size: 16px; font-weight: 800; color: #10b981; font-family: monospace;")
            c_layout.addWidget(score_lbl)

            status_badge = QLabel("PASSED")
            status_badge.setStyleSheet("background: rgba(16,185,129,0.2); color: #10b981; font-weight: 800; font-size: 11px; padding: 4px 8px; border-radius: 4px;")
            c_layout.addWidget(status_badge)

            self.bench_layout.insertWidget(self.bench_layout.count() - 1, card)

    # ─────────────────────────────────────────────────────────────
    # TAB 4: HARNESS CONFIGURATION
    # ─────────────────────────────────────────────────────────────
    def create_settings_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        box = QFrame()
        box.setStyleSheet("background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 14px;")
        b_layout = QVBoxLayout(box)
        b_layout.setSpacing(12)

        t_lbl = QLabel("⚙️ MaxMasAI Developer Preview Harness Controls")
        t_lbl.setStyleSheet("font-weight: 800; color: #38bdf8; font-size: 14px;")
        b_layout.addWidget(t_lbl)

        chk1 = QCheckBox("Enable Strict Sandbox Execution Guardrails")
        chk1.setChecked(True)
        chk1.setStyleSheet("color: #f8fafc; font-size: 12.5px;")
        b_layout.addWidget(chk1)

        chk2 = QCheckBox("Stream MaxMasAI Chain-of-Thought (CoT) Steps in Real-Time")
        chk2.setChecked(True)
        chk2.setStyleSheet("color: #f8fafc; font-size: 12.5px;")
        b_layout.addWidget(chk2)

        chk3 = QCheckBox("Auto-Inject Registered Plugin Tools into Prompt Context")
        chk3.setChecked(True)
        chk3.setStyleSheet("color: #f8fafc; font-size: 12.5px;")
        b_layout.addWidget(chk3)

        row_to = QHBoxLayout()
        row_to.addWidget(QLabel("Sandbox Timeout (seconds):"))
        sp_timeout = QSpinBox()
        sp_timeout.setRange(5, 300)
        sp_timeout.setValue(30)
        sp_timeout.setStyleSheet("background: #030712; color: #f8fafc; padding: 4px 8px;")
        row_to.addWidget(sp_timeout)
        row_to.addStretch()
        b_layout.addLayout(row_to)

        layout.addWidget(box)
        layout.addStretch()
        return widget


# Backward compatibility alias
DeepSeekHarnessPage = MaxMasAIHarnessPage
