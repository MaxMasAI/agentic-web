"""
gui/widgets/popout_chat_widget.py - Real-Time Mission Control Pop-Out Live Chat & Tool Stream
Provides an interactive pop-out chat drawer and detachable floating window directly connected
to Google Gemini Leader, specialist models, and autonomous internal tool executions.
"""

import time
import json
from typing import Dict, Any, List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QLineEdit,
    QPushButton, QComboBox, QScrollArea, QFrame, QSizePolicy, QDialog,
    QApplication, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint
from PySide6.QtGui import QCursor, QFont, QColor

from services.llm_provider import get_available_models, generate_chat_response
from core.internal_tool_executor import InternalToolExecutor
from gui.widgets.slash_autocomplete import attach_slash_autocomplete


class PopoutChatWorker(QThread):
    finished = Signal(dict)

    def __init__(self, messages: list, model_id: str, system_prompt: str = ""):
        super().__init__()
        self.messages = messages
        self.model_id = model_id
        self.system_prompt = system_prompt

    def run(self):
        try:
            res = generate_chat_response(
                self.messages,
                self.model_id,
                self.system_prompt or "You are Google Gemini / Leader AI in the Mission Control workstation. Answer accurately and assist with tasks."
            )
            self.finished.emit(res)
        except Exception as e:
            self.finished.emit({"success": False, "content": f"Error generating response: {e}"})


class ChatMessageBubble(QFrame):
    """Rich visual chat bubble supporting user, assistant, and internal tool cards."""
    def __init__(self, role: str, text: str, sender_name: str = "", tool_meta: Optional[dict] = None, parent=None):
        super().__init__(parent)
        self.role = role
        self.init_ui(text, sender_name, tool_meta)

    def init_ui(self, text: str, sender_name: str, tool_meta: Optional[dict]):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        is_user = self.role == "user"
        is_tool = self.role == "tool"

        # Theme styling
        if is_user:
            bg_col = "rgba(255, 75, 75, 0.18)"
            border_col = "#ff4b4b"
            title_txt = "👤 YOU (Operator)"
            title_col = "#ff4b4b"
        elif is_tool:
            bg_col = "rgba(16, 185, 129, 0.15)"
            border_col = "#10b981"
            tool_name = (tool_meta or {}).get("tool", "internal_tool").upper()
            title_txt = f"🛠️ INTERNAL TOOL EXECUTED: {tool_name}"
            title_col = "#10b981"
        else:
            bg_col = "rgba(15, 23, 42, 0.85)"
            border_col = "#38bdf8"
            title_txt = f"👑 {sender_name or 'Google Gemini'}"
            title_col = "#38bdf8"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_col};
                border: 1px solid {border_col}44;
                border-left: 3px solid {border_col};
                border-radius: 8px;
            }}
        """)

        # Title Row
        hdr_row = QHBoxLayout()
        hdr_lbl = QLabel(title_txt)
        hdr_lbl.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {title_col}; background: transparent; border: none;")
        hdr_row.addWidget(hdr_lbl)
        hdr_row.addStretch()

        time_lbl = QLabel(time.strftime("%H:%M:%S"))
        time_lbl.setStyleSheet("font-size: 9.5px; color: #64748b; background: transparent; border: none; font-family: monospace;")
        hdr_row.addWidget(time_lbl)
        layout.addLayout(hdr_row)

        # Message Content
        content_lbl = QLabel(text)
        content_lbl.setWordWrap(True)
        content_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        content_lbl.setStyleSheet("font-size: 12.5px; color: #f8fafc; background: transparent; border: none; line-height: 1.5;")
        layout.addWidget(content_lbl)


class PopoutChatWidget(QFrame):
    """
    Collapsible and detachable pop-out chat interface for Mission Control.
    """
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PopoutChatWidget")
        self.messages: List[Dict[str, str]] = []
        self.is_detached = False
        self.detached_window: Optional[QDialog] = None
        self.current_worker: Optional[PopoutChatWorker] = None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame#PopoutChatWidget {
                background-color: #0b1120;
                border: 1.5px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
            }
        """)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # 1. Header Controls Row
        hdr_row = QHBoxLayout()
        hdr_row.setSpacing(8)

        t_lbl = QLabel("💬 Mission Control Live Chat & Autonomous Tool Stream")
        t_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #38bdf8;")
        hdr_row.addWidget(t_lbl)
        hdr_row.addStretch()

        # Model Selector Dropdown
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(220)
        self.model_combo.setStyleSheet("""
            QComboBox {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
            }
        """)
        self._populate_models()
        hdr_row.addWidget(self.model_combo)

        # Clear Chat Button
        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.setCursor(QCursor(Qt.PointingHandCursor))
        btn_clear.setStyleSheet("background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid #ef444444; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 700;")
        btn_clear.clicked.connect(self.clear_chat)
        hdr_row.addWidget(btn_clear)

        # Pop-out / Detach Toggle
        self.btn_detach = QPushButton("⤢ Pop Out Window")
        self.btn_detach.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_detach.setStyleSheet("background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf844; border-radius: 6px; padding: 4px 10px; font-size: 11px; font-weight: 700;")
        self.btn_detach.clicked.connect(self.toggle_detach_window)
        hdr_row.addWidget(self.btn_detach)

        # Close Drawer Button
        btn_close = QPushButton("✕")
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setStyleSheet("background: transparent; color: #94a3b8; border: none; font-size: 14px; font-weight: 800; padding: 2px 6px;")
        btn_close.clicked.connect(self.close_chat)
        hdr_row.addWidget(btn_close)

        self.main_layout.addLayout(hdr_row)

        # 2. Scroll Area with Chat Messages Feed
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(240)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: rgba(15, 23, 42, 0.5);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
            }
        """)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(10, 10, 10, 10)
        self.messages_layout.setSpacing(8)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_container)
        self.main_layout.addWidget(self.scroll_area)

        # 3. Interactive Input Bar
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("💬 Type message, question, or slash command (/search, /file, /os, /mcp)...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1.5px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #38bdf8;
            }
        """)
        self.chat_input.returnPressed.connect(self.send_message)
        attach_slash_autocomplete(self.chat_input)
        input_row.addWidget(self.chat_input, stretch=4)

        self.btn_send = QPushButton("🚀 Send")
        self.btn_send.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_send.setStyleSheet("""
            QPushButton {
                background-color: #ff4b4b;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: 800;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
            }
        """)
        self.btn_send.clicked.connect(self.send_message)
        input_row.addWidget(self.btn_send, stretch=1)

        self.main_layout.addLayout(input_row)

        # Welcome message
        self.add_message("assistant", "Hello! I am your Master Orchestrator and Live Assistant. You can chat with me, ask questions, or run any internal tools (/search, /file, /os, /wiki, /mcp) directly from this pop-out console.", sender_name="Google Gemini")

    def _populate_models(self):
        models = get_available_models()
        self.model_combo.clear()
        for m in models:
            self.model_combo.addItem(m.get("name", m.get("id")), m.get("id"))

    def clear_chat(self):
        self.messages.clear()
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.add_message("assistant", "Chat feed cleared. Ready for your next query or tool execution.", sender_name="Google Gemini")

    def add_message(self, role: str, text: str, sender_name: str = "", tool_meta: Optional[dict] = None):
        """Adds a new message card to the feed and scrolls to bottom."""
        bubble = ChatMessageBubble(role, text, sender_name=sender_name, tool_meta=tool_meta)
        # Insert before bottom stretch
        self.messages_layout.insertWidget(self.messages_layout.count() - 1, bubble)
        self.messages.append({"role": role if role != "tool" else "system", "content": text})

        # Scroll to bottom
        QApplication.processEvents()
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def send_message(self, direct_text: Optional[str] = None):
        text = direct_text if isinstance(direct_text, str) else self.chat_input.text()
        text = text.strip()
        if not text:
            return

        self.chat_input.clear()
        self.add_message("user", text)

        # 1. Autonomous Internal Tool Detection & Execution
        tool_exec = InternalToolExecutor.get_instance()
        auto_tool = tool_exec.detect_and_auto_execute_tools(text)
        tool_injected_context = ""

        if auto_tool:
            tool_name = auto_tool.get("tool", "tool")
            out = auto_tool.get("output") or auto_tool.get("error") or ""
            self.add_message("tool", out, tool_meta=auto_tool)
            tool_injected_context = f"\n\n[Internal Tool Executed: {tool_name.upper()}]\n{out}\n"

        # 2. Dispatch LLM Chat Worker
        model_id = self.model_combo.currentData() or "gemini-2.0-flash"
        model_name = self.model_combo.currentText().replace("✨", "").replace("🟢", "").replace("🟣", "").strip()

        # Build prompt payload
        prompt_payload = list(self.messages)
        if tool_injected_context:
            prompt_payload[-1]["content"] += tool_injected_context

        self.btn_send.setEnabled(False)
        self.btn_send.setText("⏳ Generating...")

        self.current_worker = PopoutChatWorker(prompt_payload, model_id)
        self.current_worker.finished.connect(lambda res, m_name=model_name: self._on_chat_response(res, m_name))
        self.current_worker.start()

    def _on_chat_response(self, res: dict, model_name: str):
        self.btn_send.setEnabled(True)
        self.btn_send.setText("🚀 Send")

        content = res.get("content", "No response generated.")
        self.add_message("assistant", content, sender_name=model_name)

    def toggle_detach_window(self):
        """Detaches chat widget into a floating pop-out top-level window or docks back."""
        if not self.is_detached:
            # Create detached floating dialog
            self.detached_window = QDialog(self.window())
            self.detached_window.setWindowTitle("💬 Mission Control · Pop-Out AI Live Chat & Tool Stream")
            self.detached_window.setMinimumSize(680, 520)
            self.detached_window.resize(760, 580)
            self.detached_window.setStyleSheet("""
                QDialog {
                    background-color: #0b1120;
                    border: 1.5px solid #38bdf8;
                    border-radius: 10px;
                }
            """)
            
            d_lay = QVBoxLayout(self.detached_window)
            d_lay.setContentsMargins(10, 10, 10, 10)
            d_lay.addWidget(self)

            self.btn_detach.setText("⤡ Dock In Page")
            self.is_detached = True
            self.detached_window.finished.connect(self._on_detached_window_closed)
            self.detached_window.show()
        else:
            if self.detached_window:
                self.detached_window.close()

    def _on_detached_window_closed(self, result):
        self.is_detached = False
        self.btn_detach.setText("⤢ Pop Out Window")
        if self.parent():
            p_lay = self.parent().layout()
            if p_lay:
                p_lay.addWidget(self)
        self.show()

    def close_chat(self):
        self.hide()
        if self.is_detached and self.detached_window:
            self.detached_window.close()
        self.closed.emit()
