"""
gui/widgets/workflow_hud_widget.py - Real-Time Multi-Agent Workflow & Activity HUD
Visualizes all working agents in real-time with:
- Antigravity-styled agent pill badges (e.g. • Gemini • agent ✓ Done, • DeepSeek • agent ⚡ Working...)
- Step-by-step pipeline stages (Spec -> Plan -> Build -> Review -> Deliver)
- Live Browser Window Focus Manager (Click any agent card to bring that Chrome/Edge window in front)
- Live execution output ticker & telemetry status
"""

import time
from typing import Dict, List, Optional, Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QProgressBar, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QFont, QCursor

from browser.agent_cursor import AGENT_CURSOR_COLORS


class HorizontalScrollArea(QScrollArea):
    """Smooth horizontal scroll area that routes mouse wheel events to horizontal scroll."""
    def wheelEvent(self, event):
        if event.angleDelta().y() != 0:
            delta = event.angleDelta().y()
            # Scroll left-to-right smoothly on mouse wheel
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
            event.accept()
        elif event.angleDelta().x() != 0:
            delta = event.angleDelta().x()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta)
            event.accept()
        else:
            super().wheelEvent(event)


class AgentWorkflowCard(QFrame):
    """Visual card for a single active agent in the workflow pipeline."""
    focus_requested = Signal(str)

    def __init__(self, agent_id: str, name: str, role: str, is_leader: bool = False, parent=None):
        super().__init__(parent)
        self.agent_id = agent_id
        self.agent_name = name
        self.agent_role = role
        self.is_leader = is_leader
        self.status = "IDLE"  # IDLE, WORKING, DONE, WAITING
        self.color_hex = AGENT_CURSOR_COLORS.get(agent_id.lower(), "#2e6f54")

        self.setFixedWidth(270)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(f"""
            AgentWorkflowCard {{
                background-color: #0b1120;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 4px;
            }}
            AgentWorkflowCard:hover {{
                border: 1px solid {self.color_hex};
            }}
        """)
        v_box = QVBoxLayout(self)
        v_box.setContentsMargins(10, 8, 10, 8)
        v_box.setSpacing(6)

        # Header Row (Antigravity Pill Badge)
        h_top = QHBoxLayout()
        h_top.setSpacing(6)

        # Pill Badge Frame matching screenshot
        self.badge_frame = QFrame()
        self.badge_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color_hex};
                border-radius: 6px;
                padding: 3px 8px;
                border: 1px solid rgba(255, 255, 255, 0.15);
            }}
        """)
        b_lay = QHBoxLayout(self.badge_frame)
        b_lay.setContentsMargins(6, 2, 6, 2)
        b_lay.setSpacing(6)

        self.dot_lbl = QLabel("●")
        self.dot_lbl.setStyleSheet("color: #4ade80; font-size: 10px;")
        b_lay.addWidget(self.dot_lbl)

        self.name_lbl = QLabel(f"{self.agent_name} • agent")
        self.name_lbl.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 11px; font-family: monospace;")
        b_lay.addWidget(self.name_lbl)

        self.action_chip = QLabel("⏳ Queued")
        self.action_chip.setStyleSheet("""
            background-color: rgba(0, 0, 0, 0.35);
            color: #94a3b8;
            font-size: 10px;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: 4px;
        """)
        b_lay.addWidget(self.action_chip)

        h_top.addWidget(self.badge_frame)
        h_top.addStretch()

        # Window Focus Switcher Button
        self.pop_btn = QPushButton("👁️ View Tab")
        self.pop_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.pop_btn.setStyleSheet("""
            QPushButton {
                background: #1e293b;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #030712;
            }
        """)
        self.pop_btn.clicked.connect(lambda: self.focus_requested.emit(self.agent_id))
        h_top.addWidget(self.pop_btn)

        v_box.addLayout(h_top)

        # Role & Task status line
        self.role_lbl = QLabel(f"Role: {self.agent_role}")
        self.role_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
        v_box.addWidget(self.role_lbl)

        self.status_detail = QLabel("Ready in pipeline pool.")
        self.status_detail.setStyleSheet("color: #94a3b8; font-size: 11px; font-family: monospace;")
        v_box.addWidget(self.status_detail)

    def set_state(self, status: str, detail: str = ""):
        self.status = status.upper()
        if self.status == "WORKING":
            self.dot_lbl.setStyleSheet("color: #38bdf8; font-size: 10px;")
            self.action_chip.setText("⚡ Working...")
            self.action_chip.setStyleSheet("background-color: rgba(0, 0, 0, 0.35); color: #38bdf8; font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 4px;")
            self.setStyleSheet(f"AgentWorkflowCard {{ background-color: #0f172a; border: 1.5px solid {self.color_hex}; border-radius: 8px; padding: 4px; }}")
        elif self.status == "DONE":
            self.dot_lbl.setStyleSheet("color: #4ade80; font-size: 10px;")
            self.action_chip.setText("✓ Done")
            self.action_chip.setStyleSheet("background-color: rgba(0, 0, 0, 0.35); color: #86efac; font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 4px;")
            self.setStyleSheet("AgentWorkflowCard {{ background-color: #0b1120; border: 1px solid #10b981; border-radius: 8px; padding: 4px; }}")
        elif self.status == "IDLE":
            self.dot_lbl.setStyleSheet("color: #94a3b8; font-size: 10px;")
            self.action_chip.setText("⏳ Queued")
            self.action_chip.setStyleSheet("background-color: rgba(0, 0, 0, 0.35); color: #94a3b8; font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 4px;")
            self.setStyleSheet("AgentWorkflowCard {{ background-color: #0b1120; border: 1px solid #1e293b; border-radius: 8px; padding: 4px; }}")

        if detail:
            self.status_detail.setText(detail)


class WorkflowHUDWidget(QFrame):
    """
    Multi-Agent Workflow HUD showing all participating agents with
    Antigravity cursor status pills, live stage progression, and browser focus management.
    Features dedicated horizontal left-to-right scrolling without resizing the entire app.
    """
    agent_tab_focus_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.agent_cards: Dict[str, AgentWorkflowCard] = {}
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: #070d18; border: 1px solid #1e293b; border-radius: 10px;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 10)
        main_layout.setSpacing(8)

        # Header Title + Nav Controls
        hdr = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🤖 MULTI-AGENT WORKFLOW & BROWSER HUD")
        title.setStyleSheet("font-size: 13.5px; font-weight: 800; color: #38bdf8; letter-spacing: 0.8px;")
        sub = QLabel("Antigravity Collaborative Pipeline • Window Focus Controls • Live Step Tracking")
        sub.setStyleSheet("font-size: 10.5px; color: #64748b; font-family: monospace;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        hdr.addLayout(title_box)
        hdr.addStretch()

        # Mini Scroll Left / Right buttons
        self.scroll_left_btn = QPushButton("<")
        self.scroll_left_btn.setFixedSize(26, 26)
        self.scroll_left_btn.setToolTip("Scroll Left")
        self.scroll_left_btn.setStyleSheet("""
            QPushButton {
                background: #1e293b;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: 900;
                font-size: 13px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #030712;
            }
        """)
        self.scroll_left_btn.clicked.connect(self.scroll_left)
        hdr.addWidget(self.scroll_left_btn)

        self.scroll_right_btn = QPushButton(">")
        self.scroll_right_btn.setFixedSize(26, 26)
        self.scroll_right_btn.setToolTip("Scroll Right")
        self.scroll_right_btn.setStyleSheet("""
            QPushButton {
                background: #1e293b;
                color: #38bdf8;
                border: 1px solid #334155;
                border-radius: 4px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-weight: 900;
                font-size: 13px;
                padding-bottom: 2px;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #030712;
            }
        """)
        self.scroll_right_btn.clicked.connect(self.scroll_right)
        hdr.addWidget(self.scroll_right_btn)

        # Global Focus App Button
        self.app_focus_btn = QPushButton("🖥️ Bring App in Front")
        self.app_focus_btn.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: #ffffff;
                border: none;
                padding: 5px 12px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #030712;
            }
        """)
        hdr.addWidget(self.app_focus_btn)
        main_layout.addLayout(hdr)

        # Horizontal Scroll Area (Only scrolls the agent cards row, not the app!)
        self.scroll_area = HorizontalScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFixedHeight(108)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:horizontal {
                height: 4px;
                background: #030712;
                border-radius: 2px;
                margin: 0px 4px;
            }
            QScrollBar::handle:horizontal {
                background: #1e293b;
                border-radius: 2px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #38bdf8;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
            }
        """)

        # Container widget inside scroll area
        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QHBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(2, 2, 2, 2)
        self.cards_layout.setSpacing(10)

        self.scroll_area.setWidget(self.cards_container)
        main_layout.addWidget(self.scroll_area)

        # Set default active agents (Gemini Leader, DeepSeek Builder, Claude Reviewer, ChatGPT Synthesizer)
        self.set_active_squad([
            {"id": "gemini", "name": "Gemini", "role": "Master Orchestrator", "is_leader": True},
            {"id": "deepseek", "name": "DeepSeek", "role": "Senior Build Specialist", "is_leader": False},
            {"id": "claude", "name": "Claude", "role": "Architectural Reviewer", "is_leader": False},
            {"id": "chatgpt", "name": "ChatGPT", "role": "Deliverable Synthesizer", "is_leader": False},
        ])

    def scroll_left(self):
        """Scrolls the agent cards left by 280px."""
        bar = self.scroll_area.horizontalScrollBar()
        bar.setValue(max(0, bar.value() - 280))

    def scroll_right(self):
        """Scrolls the agent cards right by 280px."""
        bar = self.scroll_area.horizontalScrollBar()
        bar.setValue(min(bar.maximum(), bar.value() + 280))

    def set_active_squad(self, agents_list: List[Dict[str, Any]]):
        """Reconfigures the HUD cards to match the participating agents for a task."""
        # Clear existing cards
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.agent_cards.clear()

        for a in agents_list:
            card = AgentWorkflowCard(
                agent_id=a["id"],
                name=a["name"],
                role=a.get("role", "Specialist"),
                is_leader=a.get("is_leader", False)
            )
            card.focus_requested.connect(self.on_agent_focus_requested)
            self.agent_cards[a["id"]] = card
            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def update_agent_status(self, agent_id: str, status: str, detail: str = ""):
        card = self.agent_cards.get(agent_id.lower())
        if card:
            card.set_state(status, detail)

    def on_agent_focus_requested(self, agent_id: str):
        self.agent_tab_focus_requested.emit(agent_id)
