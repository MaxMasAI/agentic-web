"""
gui/pages/chat_page.py - Universal Multi-Turn AI Chat Interface with SQLite Context & Memory
Features continuous short & long-term memory, ChatGPT-like conversation sidebar,
auto-titling, and context toggling.
"""

import time
import uuid
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QComboBox, QScrollArea, QFrame, QSplitter,
    QListWidget, QListWidgetItem, QCheckBox, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QEvent
from PySide6.QtGui import QCursor, QIcon, QKeySequence, QShortcut, QKeyEvent

from services.llm_provider import get_available_models, generate_chat_response
from services.context_storage import (
    get_context_db, is_context_enabled, set_context_enabled
)


class ChatWorker(QThread):
    finished = Signal(dict)

    def __init__(self, messages: list, model_id: str, system_prompt: str, temperature: float):
        super().__init__()
        self.messages = messages
        self.model_id = model_id
        self.system_prompt = system_prompt
        self.temperature = temperature

    def run(self):
        result = generate_chat_response(
            self.messages,
            self.model_id,
            self.system_prompt,
            self.temperature
        )
        self.finished.emit(result)


class ChatPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = get_context_db()
        self.current_context_id = str(uuid.uuid4())
        self.messages = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Header Title & Model Bar
        header_box = QHBoxLayout()
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("💬 UNIVERSAL AI CHAT & MEMORY")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Multi-Turn AI Conversations with Persistent SQLite Memory & Context Isolation")
        subtitle.setStyleSheet("font-size: 11px; color: #64748b; font-family: monospace;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        header_box.addLayout(t_box)

        header_box.addStretch()

        header_box.addWidget(QLabel("<b>Model:</b>"))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(260)
        header_box.addWidget(self.model_combo)

        self.btn_refresh_models = QPushButton("🔄 Refresh")
        self.btn_refresh_models.setToolTip("Refresh Models (F5 / Ctrl+R)")
        self.btn_refresh_models.clicked.connect(self.refresh_models)
        header_box.addWidget(self.btn_refresh_models)

        main_layout.addLayout(header_box)

        # Splitter: Left Conversations Sidebar | Right Chat Area
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet("QSplitter::handle { background: rgba(56, 189, 248, 0.15); width: 2px; }")

        # --- LEFT SIDEBAR: CONVERSATION LIST ---
        left_panel = QFrame()
        left_panel.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 10px;
            }
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        left_layout.setSpacing(8)

        # New Chat Button
        self.btn_new_chat = QPushButton("➕ New Conversation")
        self.btn_new_chat.setProperty("class", "primary-btn")
        self.btn_new_chat.setFixedHeight(36)
        self.btn_new_chat.setToolTip("Start New Conversation (Ctrl+N)")
        self.btn_new_chat.clicked.connect(self.new_conversation)
        left_layout.addWidget(self.btn_new_chat)

        left_layout.addWidget(QLabel("<b>Past Conversations:</b>"))

        # Context List
        self.context_list = QListWidget()
        self.context_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: none;
                color: #f8fafc;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-radius: 6px;
                margin-bottom: 3px;
                background: rgba(30, 41, 59, 0.4);
            }
            QListWidget::item:hover {
                background: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
            }
            QListWidget::item:selected {
                background: rgba(56, 189, 248, 0.25);
                border-left: 3px solid #38bdf8;
                font-weight: bold;
                color: #ffffff;
            }
        """)
        self.context_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.context_list.customContextMenuRequested.connect(self.show_context_menu)
        self.context_list.itemClicked.connect(self.on_context_selected)
        left_layout.addWidget(self.context_list, stretch=1)

        # Bottom Context Settings Bar
        self.cb_use_context = QCheckBox("🧠 Use Context (Continuous Memory)")
        self.cb_use_context.setChecked(is_context_enabled())
        self.cb_use_context.toggled.connect(self.on_context_toggled)
        self.cb_use_context.setStyleSheet("font-size: 11px; color: #94a3b8;")
        left_layout.addWidget(self.cb_use_context)

        self.btn_clear_all = QPushButton("🗑️ Clear All History")
        self.btn_clear_all.setProperty("class", "danger-btn")
        self.btn_clear_all.setFixedHeight(30)
        self.btn_clear_all.setToolTip("Clear All History (Ctrl+Shift+L)")
        self.btn_clear_all.clicked.connect(self.clear_all_history)
        left_layout.addWidget(self.btn_clear_all)

        self.splitter.addWidget(left_panel)

        # --- RIGHT: ACTIVE CHAT THREAD ---
        right_panel = QFrame()
        right_panel.setStyleSheet("background: transparent; border: none;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Chat Message Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 10px; background: #080b11;")

        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(14, 14, 14, 14)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        self.scroll.setWidget(self.chat_container)

        right_layout.addWidget(self.scroll, stretch=1)

        # Message Input Bar
        input_bar = QHBoxLayout()
        input_bar.setSpacing(10)

        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Type a message or prompt... (Ctrl+Enter to Send, Enter for newline)")
        self.input_edit.setFixedHeight(70)
        self.input_edit.installEventFilter(self)
        input_bar.addWidget(self.input_edit, stretch=1)

        self.send_btn = QPushButton("🚀 Send")
        self.send_btn.setProperty("class", "primary-btn")
        self.send_btn.setFixedSize(90, 70)
        self.send_btn.setToolTip("Send Message (Ctrl+Enter)")
        self.send_btn.clicked.connect(self.send_message)
        input_bar.addWidget(self.send_btn)

        # Page Shortcuts
        self.new_chat_sc = QShortcut(QKeySequence("Ctrl+N"), self)
        self.new_chat_sc.setContext(Qt.WidgetWithChildrenShortcut)
        self.new_chat_sc.activated.connect(self.new_conversation)

        self.clear_sc = QShortcut(QKeySequence("Ctrl+Shift+L"), self)
        self.clear_sc.setContext(Qt.WidgetWithChildrenShortcut)
        self.clear_sc.activated.connect(self.clear_all_history)

        right_layout.addLayout(input_bar)
        self.splitter.addWidget(right_panel)

        # Splitter proportions: 260px sidebar, remainder chat
        self.splitter.setSizes([260, 800])
        main_layout.addWidget(self.splitter, stretch=1)

        # Initialize
        self.refresh_contexts()
        self.refresh_models()

    def eventFilter(self, obj, event):
        if obj == self.input_edit and event.type() == QEvent.KeyPress:
            key_event = event
            if key_event.key() in (Qt.Key_Return, Qt.Key_Enter) and (key_event.modifiers() & Qt.ControlModifier):
                self.send_message()
                return True
        return super().eventFilter(obj, event)

        # Initialize
        self.refresh_contexts()
        self.refresh_models()

    def showEvent(self, event):
        super().showEvent(event)
        self.refresh_models()
        self.refresh_contexts()

    def on_context_toggled(self, checked: bool):
        set_context_enabled(checked)

    def refresh_models(self):
        models = get_available_models(only_authenticated=True)
        current = self.model_combo.currentData()
        self.model_combo.clear()
        if not models:
            self.model_combo.addItem("⚠️ No Authenticated Models (Sign in under ⚙️ Settings)", "")
            if hasattr(self, "send_btn"):
                self.send_btn.setEnabled(False)
        else:
            if hasattr(self, "send_btn"):
                self.send_btn.setEnabled(True)
            for m in models:
                self.model_combo.addItem(f"{m['name']} [{m['badge']}]", m["id"])
            if current:
                idx = self.model_combo.findData(current)
                if idx >= 0:
                    self.model_combo.setCurrentIndex(idx)

    def refresh_contexts(self):
        self.context_list.blockSignals(True)
        self.context_list.clear()
        contexts = self.db.list_contexts()
        for ctx in contexts:
            item = QListWidgetItem(f"💬 {ctx['title']}")
            item.setData(Qt.UserRole, ctx["id"])
            self.context_list.addItem(item)
            if ctx["id"] == self.current_context_id:
                self.context_list.setCurrentItem(item)
        self.context_list.blockSignals(False)

    def new_conversation(self):
        self.current_context_id = str(uuid.uuid4())
        self.messages.clear()
        self.clear_chat_bubbles()
        self.refresh_contexts()

    def on_context_selected(self, item: QListWidgetItem):
        ctx_id = item.data(Qt.UserRole)
        if ctx_id:
            self.current_context_id = ctx_id
            self.load_context_messages(ctx_id)

    def load_context_messages(self, ctx_id: str):
        self.clear_chat_bubbles()
        self.messages.clear()
        msgs = self.db.get_messages(ctx_id)
        for m in msgs:
            self.messages.append({"role": m["role"], "content": m["content"]})
            self.add_message_bubble(m["role"], m["content"], m.get("model_tag", ""))

    def show_context_menu(self, pos: QPoint):
        item = self.context_list.itemAt(pos)
        if not item:
            return
        ctx_id = item.data(Qt.UserRole)
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        rename_act = menu.addAction("✏️ Rename Thread Title")
        delete_act = menu.addAction("🗑️ Delete Conversation")

        action = menu.exec(self.context_list.mapToGlobal(pos))
        if action == rename_act:
            new_title, ok = QInputDialog.getText(self, "Rename Thread", "Enter new conversation title:", text=item.text().replace("💬 ", ""))
            if ok and new_title.strip():
                self.db.update_title(ctx_id, new_title.strip())
                self.refresh_contexts()
        elif action == delete_act:
            self.db.delete_context(ctx_id)
            if self.current_context_id == ctx_id:
                self.new_conversation()
            else:
                self.refresh_contexts()

    def send_message(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        model_id = self.model_combo.currentData()
        if not model_id:
            self.add_message_bubble("assistant", "⚠️ **No authenticated models available.**\n\nPlease sign in or configure API keys in **⚙️ Settings**.")
            return

        self.input_edit.clear()
        self.add_message_bubble("user", text)

        # Store in SQLite
        self.db.add_message(self.current_context_id, "user", text, model_id)
        self.messages.append({"role": "user", "content": text})

        self.refresh_contexts()

        self.send_btn.setEnabled(False)
        self.send_btn.setText("Thinking...")

        # Build payload based on Config -> Settings -> Use context
        if self.cb_use_context.isChecked():
            payload_messages = list(self.messages)
        else:
            payload_messages = [{"role": "user", "content": text}]

        self.worker = ChatWorker(payload_messages, model_id, "You are a helpful and intelligent desktop AI assistant.", 0.7)
        self.worker.finished.connect(self.on_response_ready)
        self.worker.start()

    def on_response_ready(self, result: dict):
        content = result.get("content", "No response.")
        model_name = result.get("model", "")
        self.db.add_message(self.current_context_id, "assistant", content, model_name)
        self.messages.append({"role": "assistant", "content": content})

        self.add_message_bubble("assistant", content, model_name)
        self.send_btn.setEnabled(True)
        self.send_btn.setText("🚀 Send")
        self.refresh_contexts()

    def add_message_bubble(self, role: str, text: str, model_tag: str = ""):
        bubble = QFrame()
        is_user = role == "user"
        bg_col = "rgba(56, 189, 248, 0.12)" if is_user else "rgba(15, 23, 42, 0.85)"
        border_col = "#38bdf8" if is_user else "rgba(255, 255, 255, 0.08)"

        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 12px;
                padding: 10px 14px;
            }}
        """)
        b_layout = QVBoxLayout(bubble)
        b_layout.setContentsMargins(8, 8, 8, 8)
        b_layout.setSpacing(4)

        tag_text = "🧑 You" if is_user else f"🤖 Assistant ({model_tag or 'AI'})"
        tag_lbl = QLabel(f"<b>{tag_text}</b>")
        tag_lbl.setStyleSheet(f"font-size: 11px; color: {'#38bdf8' if is_user else '#818cf8'}; font-weight: 700;")
        b_layout.addWidget(tag_lbl)

        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg_lbl.setStyleSheet("font-size: 13px; color: #f8fafc; line-height: 1.5;")
        b_layout.addWidget(msg_lbl)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)

    def clear_chat_bubbles(self):
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def clear_all_history(self):
        reply = QMessageBox.question(
            self,
            "Clear Entire Chat History",
            "Are you sure you want to delete all saved conversations and clear memory?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.clear_all_history()
            self.new_conversation()
