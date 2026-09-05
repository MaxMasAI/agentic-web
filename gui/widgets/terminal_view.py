"""
gui/widgets/terminal_view.py - High-Tech Live Log Streaming Terminal View
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCursor


class TerminalView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Terminal Top Bar
        top_bar = QHBoxLayout()
        term_title = QLabel("📡 LIVE EXECUTION TELEMETRY LOG")
        term_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #38bdf8; letter-spacing: 0.8px;")
        top_bar.addWidget(term_title)
        top_bar.addStretch()

        self.copy_btn = QPushButton("📋 Copy Log")
        self.copy_btn.setFixedHeight(26)
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background: rgba(15, 23, 42, 0.8);
                color: #cbd5e1;
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
            }
        """)
        self.copy_btn.clicked.connect(self.copy_log)
        top_bar.addWidget(self.copy_btn)

        self.clear_btn = QPushButton("🗑 Clear")
        self.clear_btn.setFixedHeight(26)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(15, 23, 42, 0.8);
                color: #cbd5e1;
                border: 1px solid rgba(239, 68, 68, 0.2);
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.15);
                color: #f87171;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_log)
        top_bar.addWidget(self.clear_btn)

        layout.addLayout(top_bar)

        # Terminal Text View
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
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
        layout.addWidget(self.text_edit)

    def set_text(self, text: str):
        self.text_edit.setPlainText(text)
        self.text_edit.moveCursor(QTextCursor.End)

    def append_text(self, text: str):
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.insertPlainText(text)
        self.text_edit.moveCursor(QTextCursor.End)

    def clear_log(self):
        self.text_edit.clear()

    def copy_log(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
