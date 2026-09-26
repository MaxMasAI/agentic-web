"""
gui/widgets/agency_agents_dialog.py - Agency Agents Explorer & Persona Inspector
Allows browsing, searching, and 1-click selection of 287+ specialized AI agent personas
from The Agency catalog across 18 specialized divisions.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QScrollArea, QWidget, QFrame, QTextEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal
from core.agency_agents_manager import agency_manager


class AgencyAgentsDialog(QDialog):
    """Interactive visual browser and inspector for 287+ Agency Agents."""
    agent_selected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎭 The Agency: 287+ Specialized AI Agents Catalog")
        self.resize(1100, 720)
        self.setStyleSheet("""
            QDialog {
                background-color: #0b1120;
                color: #f8fafc;
                font-family: 'Segoe UI', system-ui, sans-serif;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 10px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #38bdf8;
            }
            QPushButton {
                background-color: #1e293b;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
            }
            QPushButton.primary-btn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #818cf8);
                color: #0f172a;
                border: none;
                font-weight: 700;
            }
            QPushButton.primary-btn:hover {
                background: #38bdf8;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        self.current_division = "all"
        self.current_query = ""
        self.selected_agent = None

        self.init_ui()
        self.populate_divisions()
        self.refresh_agents()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Header
        hdr_box = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🎭 THE AGENCY: SPECIALIST ROSTER")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;")
        sub = QLabel(f"Browse, Inspect & Deploy across 287+ production-grade AI Specialists in 18 Divisions")
        sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        hdr_box.addLayout(title_box)
        hdr_box.addStretch()

        self.stats_lbl = QLabel(f"<b>{agency_manager.get_total_count()} Agents Ready</b>")
        self.stats_lbl.setStyleSheet("background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 4px 12px; font-size: 12px;")
        hdr_box.addWidget(self.stats_lbl)
        main_layout.addLayout(hdr_box)

        # Filter bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        filter_bar.addWidget(QLabel("<b>Division:</b>"))
        self.div_combo = QComboBox()
        self.div_combo.setMinimumWidth(200)
        self.div_combo.currentIndexChanged.connect(self.on_division_changed)
        filter_bar.addWidget(self.div_combo)

        filter_bar.addWidget(QLabel("<b>Search:</b>"))
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter by name, vibe, role, or keywords...")
        self.search_edit.textChanged.connect(self.on_search_changed)
        filter_bar.addWidget(self.search_edit, stretch=1)

        btn_clear = QPushButton("Reset")
        btn_clear.clicked.connect(self.on_reset_filters)
        filter_bar.addWidget(btn_clear)
        main_layout.addLayout(filter_bar)

        # Splitter: Left List, Right Inspector
        splitter = QSplitter(Qt.Horizontal)

        # Left: Scrollable Agent Cards
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(4, 4, 4, 4)
        self.cards_layout.setSpacing(8)
        self.scroll_area.setWidget(self.cards_container)
        left_layout.addWidget(self.scroll_area)
        splitter.addWidget(left_widget)

        # Right: Detail Inspector
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(8, 0, 0, 0)
        right_layout.setSpacing(10)

        self.detail_title = QLabel("Select an Agent to Inspect")
        self.detail_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc;")
        right_layout.addWidget(self.detail_title)

        self.detail_badge = QLabel("")
        self.detail_badge.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        right_layout.addWidget(self.detail_badge)

        self.detail_vibe = QLabel("")
        self.detail_vibe.setWordWrap(True)
        self.detail_vibe.setStyleSheet("font-size: 12px; color: #38bdf8; font-style: italic;")
        right_layout.addWidget(self.detail_vibe)

        self.detail_prompt = QTextEdit()
        self.detail_prompt.setReadOnly(True)
        self.detail_prompt.setPlaceholderText("Full persona instructions and deliverable guidelines will appear here...")
        right_layout.addWidget(self.detail_prompt, stretch=1)

        btn_action_row = QHBoxLayout()
        self.btn_select = QPushButton("🚀 Select & Deploy This Agent")
        self.btn_select.setProperty("class", "primary-btn")
        self.btn_select.setFixedHeight(36)
        self.btn_select.setEnabled(False)
        self.btn_select.clicked.connect(self.on_confirm_select)
        btn_action_row.addWidget(self.btn_select)

        right_layout.addLayout(btn_action_row)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        main_layout.addWidget(splitter, stretch=1)

    def populate_divisions(self):
        self.div_combo.blockSignals(True)
        self.div_combo.clear()
        self.div_combo.addItem("🌐 All Divisions (287 Agents)", "all")
        
        divisions = agency_manager.get_divisions()
        for div_key, info in sorted(divisions.items()):
            label = info.get("label", div_key.title())
            count = info.get("agent_count", 0)
            self.div_combo.addItem(f"{label} ({count})", div_key)
            
        self.div_combo.blockSignals(False)

    def on_division_changed(self, idx):
        self.current_division = self.div_combo.currentData()
        self.refresh_agents()

    def on_search_changed(self, text):
        self.current_query = text.strip()
        self.refresh_agents()

    def on_reset_filters(self):
        self.search_edit.clear()
        self.div_combo.setCurrentIndex(0)

    def refresh_agents(self):
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        results = agency_manager.search_agents(
            query=self.current_query,
            division=self.current_division,
            limit=80
        )

        if not results:
            empty_lbl = QLabel("No matching agents found.")
            empty_lbl.setStyleSheet("color: #64748b; font-size: 13px; padding: 20px;")
            self.cards_layout.addWidget(empty_lbl)
            return

        for agent in results:
            card = self.create_agent_card(agent)
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def create_agent_card(self, agent: dict) -> QFrame:
        card = QFrame()
        div_color = agent.get("division_color") or "#3b82f6"
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1e293b;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-left: 4px solid {div_color};
                border-radius: 8px;
                padding: 8px;
            }}
            QFrame:hover {{
                background-color: #273549;
                border: 1px solid #38bdf8;
            }}
        """)
        card.setCursor(Qt.PointingHandCursor)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Top Tag Row (Placed on top of the title)
        tag_row = QHBoxLayout()
        tag_row.setContentsMargins(0, 0, 0, 0)
        badge = QLabel(agent.get("division_label", "").upper())
        badge.setStyleSheet(f"background: {div_color}22; color: {div_color}; border: 1px solid {div_color}55; border-radius: 4px; padding: 2px 8px; font-size: 9.5px; font-weight: 700;")
        tag_row.addWidget(badge)
        tag_row.addStretch()
        layout.addLayout(tag_row)

        # Title
        name_lbl = QLabel(f"<b>{agent.get('emoji', '🤖')} {agent.get('name', 'Agent')}</b>")
        name_lbl.setStyleSheet("font-size: 13.5px; color: #f8fafc; font-weight: 700;")
        layout.addWidget(name_lbl)

        # Vibe / description
        if agent.get("vibe"):
            vibe_lbl = QLabel(f"⚡ {agent['vibe']}")
            vibe_lbl.setWordWrap(True)
            vibe_lbl.setStyleSheet("font-size: 11px; color: #38bdf8;")
            layout.addWidget(vibe_lbl)
        elif agent.get("description"):
            desc_lbl = QLabel(agent["description"][:100] + "...")
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
            layout.addWidget(desc_lbl)

        # Connect click
        card.mousePressEvent = lambda ev, a=agent: self.inspect_agent(a)
        return card

    def inspect_agent(self, agent: dict):
        self.selected_agent = agent
        self.detail_title.setText(f"{agent.get('emoji', '🤖')} {agent.get('name')}")
        self.detail_badge.setText(f"Division: {agent.get('division_label')} | ID: {agent.get('id')}")
        self.detail_vibe.setText(f"Vibe: \"{agent.get('vibe', 'Production Specialist')}\"")
        
        full_md = agency_manager.get_full_agent_markdown(agent["id"]) or agent.get("system_prompt", "")
        self.detail_prompt.setPlainText(full_md)
        self.btn_select.setEnabled(True)

    def on_confirm_select(self):
        if self.selected_agent:
            self.agent_selected.emit(self.selected_agent)
            self.accept()
