"""
gui/pages/playground.py - Playground Studio & Live Code Sandbox
"""

import os
import sys
import re
import time
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QPlainTextEdit, QTextEdit, QComboBox,
    QFrame, QMessageBox, QTextBrowser
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QKeySequence, QShortcut

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


class PlaygroundPage(QWidget):
    dispatch_refactor_requested = Signal(str, str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_tasks = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🎮 PLAYGROUND STUDIO")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Interactive Code & Web Sandbox, Live HTML/CSS/JS Previewer, Python Runner & Mission Visualizer")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_web_sandbox_tab(), "🌐 Web App & HTML/CSS/JS Live Sandbox")
        self.tabs.addTab(self.create_python_sandbox_tab(), "🐍 Python Execution Sandbox")
        self.tabs.addTab(self.create_extractor_tab(), "📋 Task Code Extractor & Live Renderer")

        # Shortcuts
        self.exec_sc = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.exec_sc.setContext(Qt.WidgetWithChildrenShortcut)
        self.exec_sc.activated.connect(self._on_shortcut_exec)

        self.save_sc = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_sc.setContext(Qt.WidgetWithChildrenShortcut)
        self.save_sc.activated.connect(self.export_preview_html)

        main_layout.addWidget(self.tabs)

    def _on_shortcut_exec(self):
        if self.tabs.currentIndex() == 1:
            self.run_python_code()
        elif self.tabs.currentIndex() == 0:
            self.on_dispatch_refactor()

    # ──────────────────────────────────────────
    #  Tab 1: Web App & Live HTML/CSS/JS Sandbox
    # ──────────────────────────────────────────
    def create_web_sandbox_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Source Selection Bar
        src_row = QHBoxLayout()
        src_row.addWidget(QLabel("<b>Code Source:</b>"))
        self.source_combo = QComboBox()
        self.source_combo.addItems(["⚡ Latest Agent Mission Deliverable", "📂 Select from Mission Archive", "📝 Blank Scratchpad"])
        self.source_combo.currentIndexChanged.connect(self.on_source_changed)
        src_row.addWidget(self.source_combo, stretch=2)

        self.archive_task_combo = QComboBox()
        self.archive_task_combo.currentIndexChanged.connect(self.on_archive_task_picked)
        self.archive_task_combo.hide()
        src_row.addWidget(self.archive_task_combo, stretch=3)

        src_row.addStretch()
        layout.addLayout(src_row)

        # Split: Editor on Left, Live Render on Right
        split = QHBoxLayout()
        split.setSpacing(14)

        # Left: Code Editor
        left_v = QVBoxLayout()
        left_v.addWidget(QLabel("<b>HTML / CSS / JavaScript Code Editor:</b>"))

        self.html_editor = QPlainTextEdit()
        self.html_editor.setProperty("class", "code-editor")
        self.html_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #030712;
                color: #38bdf8;
                font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.html_editor.textChanged.connect(self.render_live_web_preview)
        left_v.addWidget(self.html_editor, stretch=1)

        btn_row = QHBoxLayout()
        self.export_html_btn = QPushButton("💾 Export to downloads/preview.html")
        self.export_html_btn.setToolTip("Export Sandboxed Web HTML to downloads/ (Ctrl+S)")
        self.export_html_btn.clicked.connect(self.export_preview_html)
        btn_row.addWidget(self.export_html_btn)

        self.refactor_btn = QPushButton("🚀 Dispatch to DeepSeek to Refactor")
        self.refactor_btn.setProperty("class", "primary-btn")
        self.refactor_btn.setToolTip("Dispatch code to DeepSeek for AI Refactor (Ctrl+Enter)")
        self.refactor_btn.clicked.connect(self.on_dispatch_refactor)
        btn_row.addWidget(self.refactor_btn)
        left_v.addLayout(btn_row)

        split.addLayout(left_v, stretch=1)

        # Right: Live Render
        right_v = QVBoxLayout()
        right_v.addWidget(QLabel("<b>🖥️ Real-Time Live Sandbox Preview:</b>"))

        if HAS_WEBENGINE:
            self.web_view = QWebEngineView()
            self.web_view.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px;")
            right_v.addWidget(self.web_view, stretch=1)
        else:
            self.web_view = QTextBrowser()
            self.web_view.setOpenExternalLinks(True)
            self.web_view.setStyleSheet("background: #030712; color: #f8fafc; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px;")
            right_v.addWidget(self.web_view, stretch=1)

        split.addLayout(right_v, stretch=1)
        layout.addLayout(split)

        self.set_blank_starter()
        return tab

    def set_blank_starter(self):
        starter = (
            "<!DOCTYPE html>\n<html>\n<head>\n"
            "<style>\n"
            "  body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', sans-serif; padding: 30px; text-align: center; }\n"
            "  h2 { color: #38bdf8; font-size: 26px; }\n"
            "  p { color: #cbd5e1; font-size: 15px; }\n"
            "  .btn { background: #38bdf8; color: #080b11; border: none; padding: 10px 20px; font-weight: 700; border-radius: 8px; cursor: pointer; }\n"
            "</style>\n</head>\n<body>\n"
            "  <h2>⚡ PySide6 Interactive Web Sandbox</h2>\n"
            "  <p>Write your HTML, CSS, and JS code here or load from mission deliverables!</p>\n"
            "  <button class='btn' onclick='alert(\"Hello from PySide6 Sandbox!\")'>Click Me</button>\n"
            "</body>\n</html>"
        )
        self.html_editor.setPlainText(starter)

    def render_live_web_preview(self):
        code = self.html_editor.toPlainText()
        if HAS_WEBENGINE:
            self.web_view.setHtml(code)
            try:
                from browser.agent_cursor import ANTIGRAVITY_CURSOR_JS
                self.web_view.loadFinished.connect(lambda ok: self.web_view.page().runJavaScript(ANTIGRAVITY_CURSOR_JS) if ok else None)
            except Exception:
                pass
        else:
            self.web_view.setHtml(code)

    def on_source_changed(self):
        idx = self.source_combo.currentIndex()
        if idx == 0:  # Latest Deliverable
            self.archive_task_combo.hide()
            self.load_latest_deliverable()
        elif idx == 1:  # Archive Picker
            self.archive_task_combo.show()
            self.on_archive_task_picked()
        else:  # Blank
            self.archive_task_combo.hide()
            self.set_blank_starter()

    def load_latest_deliverable(self):
        for t in self.all_tasks:
            combined = t.get("final_output", "") + "\n" + "\n".join(t.get("worker_outputs", {}).values())
            matches = re.findall(r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?|<html[\s\S]*?)```", combined, re.IGNORECASE)
            if matches:
                self.html_editor.setPlainText(matches[0])
                return
        self.set_blank_starter()

    def on_archive_task_picked(self):
        idx = self.archive_task_combo.currentIndex()
        if 0 <= idx < len(self.all_tasks):
            t = self.all_tasks[idx]
            combined = t.get("final_output", "") + "\n" + "\n".join(t.get("worker_outputs", {}).values())
            matches = re.findall(r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?|<html[\s\S]*?)```", combined, re.IGNORECASE)
            if matches:
                self.html_editor.setPlainText(matches[0])
            else:
                self.html_editor.setPlainText(f"<!-- No HTML block in this task outcome -->\n{t.get('final_output', '')}")

    def export_preview_html(self):
        os.makedirs("downloads", exist_ok=True)
        out_path = os.path.join("downloads", "preview.html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(self.html_editor.toPlainText())
        QMessageBox.information(self, "Exported", f"Successfully saved to {out_path}")

    def on_dispatch_refactor(self):
        code = self.html_editor.toPlainText()
        if not code.strip():
            return
        prompt = f"Refactor and enhance this code to senior engineering standards:\n{code[:400]}..."
        self.dispatch_refactor_requested.emit(prompt, "deepseek,claude", f"Refactor @ {time.strftime('%H:%M:%S')}")

    # ──────────────────────────────────────────
    #  Tab 2: Python Code Execution Sandbox
    # ──────────────────────────────────────────
    def create_python_sandbox_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        split = QHBoxLayout()
        split.setSpacing(14)

        # Left: Python Editor
        left_v = QVBoxLayout()
        left_v.addWidget(QLabel("<b>Write Python Code to Execute in Sandbox:</b>"))

        self.py_editor = QPlainTextEdit()
        self.py_editor.setProperty("class", "code-editor")
        self.py_editor.setPlainText(
            "# Test Python execution in sandboxed subprocess\n"
            "import math\nimport sys\nimport platform\n\n"
            "print(f\"Python Runtime: {platform.python_version()} on {platform.system()}\")\n"
            "squares = [x**2 for x in range(1, 11)]\n"
            "print(f\"First 10 Squares: {squares}\")\n"
            "print(f\"Sum: {sum(squares)}, Mean: {sum(squares)/len(squares)}\")\n"
        )
        self.py_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #030712;
                color: #fde68a;
                font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        left_v.addWidget(self.py_editor, stretch=1)

        self.run_py_btn = QPushButton("⚡ Run Python Code Live")
        self.run_py_btn.setProperty("class", "primary-btn")
        self.run_py_btn.setFixedHeight(36)
        self.run_py_btn.setToolTip("Run Python Code in Subprocess Sandbox (Ctrl+Enter / F5)")
        self.run_py_btn.clicked.connect(self.run_python_code)
        left_v.addWidget(self.run_py_btn)
        split.addLayout(left_v, stretch=1)

        # Right: Python Output
        right_v = QVBoxLayout()
        right_v.addWidget(QLabel("<b>📡 Python Sandbox Execution Output:</b>"))

        self.py_output = QPlainTextEdit()
        self.py_output.setReadOnly(True)
        self.py_output.setStyleSheet("""
            QPlainTextEdit {
                background-color: #030712;
                color: #4ade80;
                font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        right_v.addWidget(self.py_output, stretch=1)
        split.addLayout(right_v, stretch=1)

        layout.addLayout(split)
        return tab

    def run_python_code(self):
        code = self.py_editor.toPlainText().strip()
        if not code:
            return
        self.py_output.setPlainText("Executing script in isolated sandbox...")
        try:
            res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                self.py_output.setPlainText(f"=== SUCCESS (Exit Code: 0) ===\n\n{res.stdout}")
            else:
                self.py_output.setPlainText(f"=== EXECUTION ERROR (Exit Code: {res.returncode}) ===\n\n{res.stderr}\n\nSTDOUT:\n{res.stdout}")
        except Exception as e:
            self.py_output.setPlainText(f"Failed to execute: {e}")

    # ──────────────────────────────────────────
    #  Tab 3: Task Code Extractor
    # ──────────────────────────────────────────
    def create_extractor_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("<b>Select Mission:</b>"))
        self.ext_task_combo = QComboBox()
        self.ext_task_combo.currentIndexChanged.connect(self.on_extractor_task_selected)
        top_row.addWidget(self.ext_task_combo, stretch=3)
        top_row.addStretch()
        layout.addLayout(top_row)

        self.ext_status_lbl = QLabel()
        self.ext_status_lbl.setStyleSheet("color: #38bdf8; font-weight: 700;")
        layout.addWidget(self.ext_status_lbl)

        split = QHBoxLayout()
        split.setSpacing(14)

        # Extracted Code Preview
        l_v = QVBoxLayout()
        l_v.addWidget(QLabel("<b>Extracted Code Block:</b>"))
        self.ext_code_view = QPlainTextEdit()
        self.ext_code_view.setProperty("class", "code-editor")
        self.ext_code_view.setStyleSheet("background: #030712; color: #4ade80; font-family: monospace; border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px;")
        l_v.addWidget(self.ext_code_view, stretch=1)

        self.load_to_editor_btn = QPushButton("📥 Load Code into Web Studio Editor")
        self.load_to_editor_btn.setProperty("class", "primary-btn")
        self.load_to_editor_btn.clicked.connect(self.load_extracted_to_studio)
        l_v.addWidget(self.load_to_editor_btn)
        split.addLayout(l_v, stretch=1)

        # Extracted Live Render Preview
        r_v = QVBoxLayout()
        r_v.addWidget(QLabel("<b>Rendered Visual Preview:</b>"))
        if HAS_WEBENGINE:
            self.ext_web_view = QWebEngineView()
            self.ext_web_view.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px;")
            r_v.addWidget(self.ext_web_view, stretch=1)
        else:
            self.ext_web_view = QTextBrowser()
            self.ext_web_view.setStyleSheet("background: #030712; color: #f8fafc; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px;")
            r_v.addWidget(self.ext_web_view, stretch=1)
        split.addLayout(r_v, stretch=1)

        layout.addLayout(split)
        return tab

    def on_extractor_task_selected(self):
        idx = self.ext_task_combo.currentIndex()
        if 0 <= idx < len(self.all_tasks):
            t = self.all_tasks[idx]
            combined = t.get("final_output", "") + "\n" + "\n".join(t.get("worker_outputs", {}).values())
            matches = re.findall(r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?|<html[\s\S]*?)```", combined, re.IGNORECASE)
            if matches:
                self.ext_status_lbl.setText(f"✅ Found {len(matches)} live HTML website deliverable(s) in this mission!")
                self.ext_code_view.setPlainText(matches[0])
                if HAS_WEBENGINE:
                    self.ext_web_view.setHtml(matches[0])
                else:
                    self.ext_web_view.setHtml(matches[0])
            else:
                self.ext_status_lbl.setText("ℹ️ No HTML web app deliverable detected in this mission outcome.")
                self.ext_code_view.setPlainText(t.get("final_output", ""))
                self.ext_web_view.setHtml(f"<pre style='color:#f8fafc;background:#0f172a;padding:12px;'>{t.get('final_output', '')}</pre>")

    def load_extracted_to_studio(self):
        code = self.ext_code_view.toPlainText()
        if code.strip():
            self.html_editor.setPlainText(code)
            self.tabs.setCurrentIndex(0)
            QMessageBox.information(self, "Loaded", "Code deliverable loaded into Web Studio!")

    def set_editor_code(self, code_str: str):
        self.html_editor.setPlainText(code_str)
        self.tabs.setCurrentIndex(0)

    def refresh_tasks(self, tasks: list):
        self.all_tasks = tasks
        self.archive_task_combo.blockSignals(True)
        self.ext_task_combo.blockSignals(True)

        self.archive_task_combo.clear()
        self.ext_task_combo.clear()

        for i, t in enumerate(tasks):
            lbl = f"#{len(tasks)-i}  {t.get('task', 'Task')[:45]}..."
            self.archive_task_combo.addItem(lbl)
            self.ext_task_combo.addItem(lbl)

        self.archive_task_combo.blockSignals(False)
        self.ext_task_combo.blockSignals(False)

        if self.source_combo.currentIndex() == 0:
            self.load_latest_deliverable()
