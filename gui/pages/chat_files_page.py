"""
gui/pages/chat_files_page.py - Chat with Files & Document Knowledge Retrieval (RAG)
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QFileDialog, QScrollArea, QFrame, QSplitter,
    QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from services.rag_engine import query_indexed_documents
from services.llm_provider import generate_chat_response


class RAGWorker(QThread):
    finished = Signal(dict)

    def __init__(self, query: str, file_paths: list, model_id: str = "gemini-2.5-flash"):
        super().__init__()
        self.query = query
        self.file_paths = file_paths
        self.model_id = model_id

    def run(self):
        chunks = query_indexed_documents(self.query, self.file_paths, top_k=4)
        
        context_str = "\n\n---\n\n".join([
            f"[Source File: {c['file']}]\n{c['chunk']}" for c in chunks
        ])

        system_prompt = (
            "You are a specialized document analysis AI. Answer the user's question accurately using ONLY "
            "the provided document excerpts. Cite the source files and sections when explaining.\n\n"
            f"DOCUMENT CONTEXT:\n{context_str}"
        )

        resp = generate_chat_response(
            [{"role": "user", "content": self.query}],
            model_id=self.model_id,
            system_prompt=system_prompt
        )

        self.finished.emit({
            "response": resp.get("content", ""),
            "chunks": chunks
        })


class ChatFilesPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.attached_files = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("📄 CHAT WITH YOUR FILES & DATA (RAG)")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Deep Document Indexing & Q&A for PDF, TXT, CSV, HTML, MD, DOCX, and JSON")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Splitter: Files Sidebar on Left, Q&A on Right
        splitter = QSplitter(Qt.Horizontal)

        # Left: Attached Files Manager
        left_widget = QWidget()
        left_v = QVBoxLayout(left_widget)
        left_v.setContentsMargins(0, 0, 0, 0)
        left_v.setSpacing(8)

        left_v.addWidget(QLabel("<b>📁 Attached & Indexed Files:</b>"))

        btn_add_files = QPushButton("➕ Attach Documents (PDF, TXT, CSV...)")
        btn_add_files.setProperty("class", "primary-btn")
        btn_add_files.clicked.connect(self.attach_files)
        left_v.addWidget(btn_add_files)

        self.files_scroll = QScrollArea()
        self.files_scroll.setWidgetResizable(True)
        self.files_scroll.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; background: #080b11;")
        
        self.files_container = QWidget()
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.setContentsMargins(8, 8, 8, 8)
        self.files_layout.setSpacing(6)
        self.files_scroll.setWidget(self.files_container)

        left_v.addWidget(self.files_scroll, stretch=1)
        splitter.addWidget(left_widget)

        # Right: Chat Q&A View
        right_widget = QWidget()
        right_v = QVBoxLayout(right_widget)
        right_v.setContentsMargins(0, 0, 0, 0)
        right_v.setSpacing(10)

        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; background: #080b11;")
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 12)
        self.chat_layout.setSpacing(12)
        self.chat_layout.addStretch()
        self.chat_scroll.setWidget(self.chat_container)
        right_v.addWidget(self.chat_scroll, stretch=1)

        # Input Bar
        input_bar = QHBoxLayout()
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Ask any question about your attached files and documents...")
        self.input_edit.setFixedHeight(70)
        input_bar.addWidget(self.input_edit, stretch=1)

        self.btn_ask = QPushButton("🔍 Ask RAG")
        self.btn_ask.setProperty("class", "primary-btn")
        self.btn_ask.setFixedSize(100, 70)
        self.btn_ask.clicked.connect(self.ask_question)
        input_bar.addWidget(self.btn_ask)

        right_v.addLayout(input_bar)
        splitter.addWidget(right_widget)

        splitter.setSizes([320, 700])
        main_layout.addWidget(splitter, stretch=1)
        self.render_file_list()

    def attach_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Attach Documents for RAG",
            "",
            "Documents (*.pdf *.txt *.csv *.json *.md *.html *.py *.log);;All Files (*)"
        )
        if files:
            for f in files:
                if f not in self.attached_files:
                    self.attached_files.append(f)
            self.render_file_list()

    def render_file_list(self):
        while self.files_layout.count():
            item = self.files_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self.attached_files:
            empty = QLabel("No files attached.\nClick 'Attach Documents' to begin.")
            empty.setStyleSheet("color: #64748b; font-style: italic; padding: 10px;")
            self.files_layout.addWidget(empty)
            return

        for idx, fpath in enumerate(self.attached_files):
            fname = os.path.basename(fpath)
            card = QFrame()
            card.setStyleSheet("background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 6px; padding: 6px;")
            c_h = QHBoxLayout(card)
            c_h.setContentsMargins(4, 4, 4, 4)

            lbl = QLabel(f"📄 {fname}")
            lbl.setStyleSheet("font-size: 12px; color: #f8fafc;")
            c_h.addWidget(lbl, stretch=1)

            del_btn = QPushButton("✖")
            del_btn.setProperty("class", "danger-btn")
            del_btn.setFixedSize(20, 20)
            del_btn.clicked.connect(lambda _, i=idx: self.remove_file(i))
            c_h.addWidget(del_btn)

            self.files_layout.addWidget(card)

    def remove_file(self, index: int):
        if 0 <= index < len(self.attached_files):
            self.attached_files.pop(index)
            self.render_file_list()

    def ask_question(self):
        query = self.input_edit.toPlainText().strip()
        if not query:
            return

        if not self.attached_files:
            QMessageBox.warning(self, "No Files", "Please attach at least one document on the left.")
            return

        self.input_edit.clear()
        self.add_qa_bubble("🧑 Question", query, is_user=True)

        self.btn_ask.setEnabled(False)
        self.btn_ask.setText("Retrieving...")

        self.rag_worker = RAGWorker(query, self.attached_files)
        self.rag_worker.finished.connect(self.on_rag_result)
        self.rag_worker.start()

    def on_rag_result(self, result: dict):
        response_text = result.get("response", "No answer found.")
        chunks = result.get("chunks", [])

        citation_lines = []
        for i, c in enumerate(chunks):
            snippet = c.get("chunk", "")[:120].replace("\n", " ")
            citation_lines.append(f"• <b>[{c.get('file', '')}]</b>: <i>\"{snippet}...\"</i>")

        citations_html = "<br><b>Retrieved Source Excerpts:</b><br>" + "<br>".join(citation_lines) if citation_lines else ""
        full_html = f"{response_text}<br>{citations_html}"

        self.add_qa_bubble("🤖 Document AI", full_html, is_user=False)
        self.btn_ask.setEnabled(True)
        self.btn_ask.setText("🔍 Ask RAG")

    def add_qa_bubble(self, title: str, text: str, is_user: bool = False):
        bubble = QFrame()
        bg_col = "rgba(56, 189, 248, 0.12)" if is_user else "rgba(15, 23, 42, 0.85)"
        border_col = "#38bdf8" if is_user else "rgba(255, 255, 255, 0.08)"

        bubble.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 10px;
                padding: 10px 14px;
            }}
        """)
        b_layout = QVBoxLayout(bubble)
        b_layout.setContentsMargins(6, 6, 6, 6)

        t_lbl = QLabel(f"<b>{title}</b>")
        t_lbl.setStyleSheet(f"font-size: 11px; color: {'#38bdf8' if is_user else '#34d399'}; font-weight: 700;")
        b_layout.addWidget(t_lbl)

        msg_lbl = QLabel(text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        msg_lbl.setStyleSheet("font-size: 13px; color: #f8fafc; line-height: 1.5;")
        b_layout.addWidget(msg_lbl)

        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
