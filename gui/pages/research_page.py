"""
gui/pages/research_page.py - Deep Research & Live Citation Search (Perplexity / Web)
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal

from services.web_search import search_duckduckgo
from services.llm_provider import generate_chat_response


class ResearchWorker(QThread):
    finished = Signal(dict)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    def run(self):
        search_results = search_duckduckgo(self.query, max_results=6)
        
        web_context = "\n\n".join([
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['snippet']}"
            for r in search_results
        ])

        system_prompt = (
            "You are an expert research analyst. Synthesize a comprehensive, well-structured research briefing "
            "based on the following real-time web search results. Include bullet points, takeaways, and citation links.\n\n"
            f"WEB SEARCH RESULTS:\n{web_context}"
        )

        resp = generate_chat_response(
            [{"role": "user", "content": self.query}],
            model_id="gemini-2.5-flash",
            system_prompt=system_prompt
        )

        self.finished.emit({
            "answer": resp.get("content", ""),
            "results": search_results
        })


class ResearchPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🔍 DEEP RESEARCH & CITATION ENGINE")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Real-Time Internet Search, Fact Verification & Synthesized Research Briefings")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Search Input Bar
        input_bar = QHBoxLayout()
        input_bar.setSpacing(10)

        self.search_input = QTextEdit()
        self.search_input.setPlaceholderText("Enter any topic, company, medical question, live news, or market research topic...")
        self.search_input.setFixedHeight(75)
        input_bar.addWidget(self.search_input, stretch=1)

        self.btn_search = QPushButton("🌐 Deep Research")
        self.btn_search.setProperty("class", "primary-btn")
        self.btn_search.setFixedSize(140, 75)
        self.btn_search.clicked.connect(self.run_research)
        input_bar.addWidget(self.btn_search)

        main_layout.addLayout(input_bar)

        # Split: Left (Synthesized Briefing) vs Right (Web Citations)
        split = QHBoxLayout()
        split.setSpacing(16)

        # Left: Briefing
        left_v = QVBoxLayout()
        left_v.addWidget(QLabel("<b>📑 Synthesized Research Briefing:</b>"))

        self.briefing_scroll = QScrollArea()
        self.briefing_scroll.setWidgetResizable(True)
        self.briefing_scroll.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; background: #080b11;")
        
        self.briefing_lbl = QLabel("Enter a topic above and click 'Deep Research' to generate a live synthesized briefing.")
        self.briefing_lbl.setWordWrap(True)
        self.briefing_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.briefing_lbl.setStyleSheet("color: #cbd5e1; font-size: 13px; padding: 14px; line-height: 1.6;")
        self.briefing_scroll.setWidget(self.briefing_lbl)

        left_v.addWidget(self.briefing_scroll, stretch=1)
        split.addLayout(left_v, stretch=2)

        # Right: Citations List
        right_v = QVBoxLayout()
        right_v.addWidget(QLabel("<b>🔗 Live Citations & Source Links:</b>"))

        self.citations_scroll = QScrollArea()
        self.citations_scroll.setWidgetResizable(True)
        self.citations_scroll.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; background: #080b11;")
        
        self.citations_container = QWidget()
        self.citations_layout = QVBoxLayout(self.citations_container)
        self.citations_layout.setContentsMargins(10, 10, 10, 10)
        self.citations_layout.setSpacing(8)
        self.citations_scroll.setWidget(self.citations_container)

        right_v.addWidget(self.citations_scroll, stretch=1)
        split.addLayout(right_v, stretch=1)

        main_layout.addLayout(split)

    def run_research(self):
        query = self.search_input.toPlainText().strip()
        if not query:
            return

        self.btn_search.setEnabled(False)
        self.btn_search.setText("Searching...")
        self.briefing_lbl.setText("📡 Conducting real-time web search and synthesizing citations...")

        self.worker = ResearchWorker(query)
        self.worker.finished.connect(self.on_research_ready)
        self.worker.start()

    def on_research_ready(self, data: dict):
        answer = data.get("answer", "No response.")
        results = data.get("results", [])

        self.briefing_lbl.setText(answer)

        while self.citations_layout.count():
            item = self.citations_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not results:
            self.citations_layout.addWidget(QLabel("No web citations found."))
        else:
            for r in results:
                card = QFrame()
                card.setStyleSheet("background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 8px;")
                c_v = QVBoxLayout(card)
                c_v.setContentsMargins(6, 6, 6, 6)

                t_lbl = QLabel(f"<b><a href='{r['url']}' style='color:#38bdf8;'>{r['title']}</a></b>")
                t_lbl.setOpenExternalLinks(True)
                c_v.addWidget(t_lbl)

                s_lbl = QLabel(r['snippet'])
                s_lbl.setWordWrap(True)
                s_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
                c_v.addWidget(s_lbl)

                self.citations_layout.addWidget(card)

        self.btn_search.setEnabled(True)
        self.btn_search.setText("🌐 Deep Research")
