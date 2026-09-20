"""
gui/widgets/add_agent_dialog.py - Cyber-styled Quick Agent Registration Dialog
"""

import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QFont

from core.agentlist import parse_agent_text_format, add_custom_agent, reload_agents


DEFAULT_TEMPLATE = """{
  "id": "qwen_coder",
  "name": "Qwen 2.5 Coder",
  "role": "Polyglot Software Architect & Senior Engineer",
  "specialization": "Full-stack code generation, architectural refactoring, algorithm design, and automated testing.",
  "official_url": "https://chat.qwenlm.ai",
  "is_leader": false,
  "routing_tag": "[SEND_TO: qwen_coder]"
}"""

LEADER_TEMPLATE = """{
  "id": "custom_leader",
  "name": "Custom Master Leader",
  "role": "Master Orchestrator & Leadership Lead",
  "specialization": "Strategic task decomposition, subagent delegation, quality control, and executive editorial approval.",
  "official_url": "https://example.com",
  "is_leader": true,
  "routing_tag": "[SEND_TO: custom_leader]"
}"""

RESEARCH_TEMPLATE = """{
  "id": "deep_researcher",
  "name": "Deep Researcher Pro",
  "role": "Academic Literature & Fact Synthesis Specialist",
  "specialization": "Live citation gathering, deep scientific cross-referencing, multi-step chain-of-thought verification.",
  "official_url": "https://example.com",
  "is_leader": false,
  "routing_tag": "[SEND_TO: deep_researcher]"
}"""

LOCAL_OLLAMA_TEMPLATE = """{
  "id": "ollama_llama",
  "name": "Ollama Llama 3.3 Local",
  "role": "Air-Gapped Private Local Compute Specialist",
  "specialization": "Offline privacy-first code execution, document summarization, and zero-latency local prompt evaluation.",
  "official_url": "http://localhost:11434",
  "is_leader": false,
  "routing_tag": "[SEND_TO: ollama_llama]"
}"""


class AddAgentDialog(QDialog):
    agent_added = Signal(dict)
    agent_registered = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✨ Register & Add New AI Agent")
        self.resize(620, 560)
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: #0b1120;
                color: #f8fafc;
                border: 2px solid #38bdf8;
                border-radius: 12px;
            }
            QLabel {
                color: #f8fafc;
            }
            QTextEdit {
                background-color: #030712;
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 8px;
                padding: 10px;
                font-family: 'Consolas', 'Fira Code', monospace;
                font-size: 12px;
                selection-background-color: #0284c7;
            }
            QTextEdit:focus {
                border: 1px solid #38bdf8;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Header Title
        hdr_layout = QHBoxLayout()
        icon_lbl = QLabel("➕")
        icon_lbl.setStyleSheet("font-size: 22px; color: #38bdf8;")
        hdr_layout.addWidget(icon_lbl)

        title_vbox = QVBoxLayout()
        title_vbox.setSpacing(2)
        main_title = QLabel("Register New AI Agent")
        main_title.setStyleSheet("font-size: 16px; font-weight: 800; color: #38bdf8;")
        sub_title = QLabel("Provide agent configuration in JSON, Python dictionary, or key-value text.")
        sub_title.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_vbox.addWidget(main_title)
        title_vbox.addWidget(sub_title)
        hdr_layout.addLayout(title_vbox)
        hdr_layout.addStretch()
        layout.addLayout(hdr_layout)

        # Presets Bar
        preset_box = QFrame()
        preset_box.setObjectName("PresetBox")
        preset_box.setStyleSheet("""
            QFrame#PresetBox {
                background-color: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
                padding: 6px 10px;
            }
        """)
        preset_lay = QHBoxLayout(preset_box)
        preset_lay.setContentsMargins(4, 4, 4, 4)
        preset_lay.setSpacing(8)

        lbl_presets = QLabel("⚡ Quick Presets:")
        lbl_presets.setStyleSheet("font-size: 11px; font-weight: 700; color: #cbd5e1;")
        preset_lay.addWidget(lbl_presets)

        def make_preset_btn(label: str, template: str):
            btn = QPushButton(label)
            btn.setFixedHeight(24)
            btn.setCursor(QCursor(Qt.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(56, 189, 248, 0.12);
                    color: #38bdf8;
                    border: 1px solid rgba(56, 189, 248, 0.3);
                    border-radius: 4px;
                    padding: 2px 8px;
                    font-size: 10.5px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: #38bdf8;
                    color: #0b1120;
                }
            """)
            btn.clicked.connect(lambda *args, tmpl=template: self.editor.setPlainText(tmpl))
            return btn

        preset_lay.addWidget(make_preset_btn("🤖 Specialist", DEFAULT_TEMPLATE))
        preset_lay.addWidget(make_preset_btn("👑 Master Leader", LEADER_TEMPLATE))
        preset_lay.addWidget(make_preset_btn("🔬 Researcher", RESEARCH_TEMPLATE))
        preset_lay.addWidget(make_preset_btn("🌐 Local Ollama", LOCAL_OLLAMA_TEMPLATE))
        preset_lay.addStretch()
        layout.addWidget(preset_box)

        # Editor
        self.editor = QTextEdit()
        self.editor.setPlainText(DEFAULT_TEMPLATE)
        self.editor.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.editor, stretch=1)

        # Status & Validation Feedback
        self.status_lbl = QLabel("✅ Ready to validate schema.")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #34d399; padding: 2px 4px;")
        layout.addWidget(self.status_lbl)

        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_cancel = QPushButton("✖ Cancel")
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: rgba(30, 41, 59, 0.8);
                color: #cbd5e1;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 0 16px;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.2);
                color: #ef4444;
                border-color: #ef4444;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(self.btn_cancel)

        btn_row.addStretch()

        self.btn_save = QPushButton("✨ Save & Register Agent")
        self.btn_save.setFixedHeight(34)
        self.btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0ea5e9);
            }
        """)
        self.btn_save.clicked.connect(self.save_agent)
        btn_row.addWidget(self.btn_save)

        layout.addLayout(btn_row)

    def on_text_changed(self):
        txt = self.editor.toPlainText().strip()
        if not txt:
            self.status_lbl.setText("⚠️ Editor is empty.")
            self.status_lbl.setStyleSheet("font-size: 11px; color: #fbbf24;")
            return

        parsed, err = parse_agent_text_format(txt)
        if parsed:
            is_leader = parsed.get("is_leader", False)
            leader_tag = "👑 [Master Leader Mode]" if is_leader else "🤖 [Specialist Agent]"
            self.status_lbl.setText(f"✅ Valid Schema: <b>{parsed.get('name')}</b> ({parsed.get('id')}) · {leader_tag}")
            self.status_lbl.setStyleSheet("font-size: 11px; color: #34d399;")
        else:
            self.status_lbl.setText(f"❌ Syntax/Validation Error: {err}")
            self.status_lbl.setStyleSheet("font-size: 11px; color: #ef4444;")

    def save_agent(self):
        txt = self.editor.toPlainText().strip()
        parsed, err = parse_agent_text_format(txt)
        if not parsed:
            QMessageBox.warning(self, "Invalid Agent Schema", f"Please resolve schema validation error:\n\n{err}")
            return

        success, msg = add_custom_agent(parsed)
        if success:
            QMessageBox.information(self, "Agent Registered", msg)
            self.agent_added.emit(parsed)
            self.agent_registered.emit(parsed)
            self.accept()
        else:
            QMessageBox.critical(self, "Registration Failed", f"Failed to register custom agent:\n\n{msg}")
