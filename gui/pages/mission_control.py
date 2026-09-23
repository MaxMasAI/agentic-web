"""
gui/pages/mission_control.py - Mission Control (Home Page)
"""

import os
import glob
import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from gui.widgets.metric_card import MetricCard
from gui.widgets.pool_monitor import PoolMonitor
from utils.mcp_service import get_skills_count


class MissionControlPage(QWidget):
    navigate_requested = Signal(str)
    direct_task_submitted = Signal(str)
    multi_tasks_submitted = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(18)

        # Header Title Banner
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        main_title = QLabel("⚡ AGENT MISSION CONTROL")
        main_title.setStyleSheet("""
            font-size: 26px;
            font-weight: 800;
            color: #38bdf8;
            letter-spacing: 1.2px;
            font-family: 'Segoe UI', sans-serif;
        """)
        
        subtitle = QLabel("Autonomous Leader-Worker Collaborative Operations Console")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 8px;")
        
        title_box.addWidget(main_title)
        title_box.addWidget(subtitle)
        self.layout.addLayout(title_box)

        # 7 Top Interactive Telemetry Metric Cards
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setSpacing(10)

        self.card_tokens = MetricCard("1.019B+", "Free Tokens", "#ff4b4b", is_clickable=True)
        self.card_tokens.clicked.connect(lambda *args: self.navigate_requested.emit("tokens"))

        self.card_tasks = MetricCard("0", "Tasks Done", "#38bdf8", is_clickable=True)
        self.card_tasks.clicked.connect(lambda *args: self.navigate_requested.emit("history"))

        self.card_mem = MetricCard("0", "Memories", "#fbbf24", is_clickable=True)
        self.card_mem.clicked.connect(lambda *args: self.navigate_requested.emit("memory"))

        self.card_play = MetricCard("LIVE", "Playground", "#10b981", is_clickable=True)
        self.card_play.clicked.connect(lambda *args: self.navigate_requested.emit("playground"))

        self.card_squads = MetricCard("0", "Squad Roster", "#818cf8", is_clickable=True)
        self.card_squads.clicked.connect(lambda *args: self.navigate_requested.emit("subagents"))

        self.card_skills = MetricCard("0", "Skills", "#c084fc", is_clickable=True)
        self.card_skills.clicked.connect(lambda *args: self.navigate_requested.emit("mcp"))

        self.card_assets = MetricCard("0", "Assets", "#38bdf8", is_clickable=True)
        self.card_assets.clicked.connect(lambda *args: self.navigate_requested.emit("explorer"))

        self.card_active = MetricCard("0", "Active Runs", "#f87171", is_clickable=True)
        self.card_active.clicked.connect(lambda *args: self.navigate_requested.emit("launch"))

        for c in [self.card_tokens, self.card_tasks, self.card_mem, self.card_play, self.card_squads, self.card_skills, self.card_assets, self.card_active]:
            self.cards_layout.addWidget(c)

        self.layout.addLayout(self.cards_layout)

        # Section: Multi-Agent Command Hierarchy & Pool Monitor
        sec_hdr = QLabel("⚡ Multi-Agent Command Hierarchy & Live Pool")
        sec_hdr.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 4px; margin-top: 10px;")
        self.layout.addWidget(sec_hdr)

        self.pool_monitor = PoolMonitor()
        self.pool_monitor.direct_task_submitted.connect(self.direct_task_submitted.emit)
        self.pool_monitor.multi_tasks_submitted.connect(self.multi_tasks_submitted.emit)
        self.pool_monitor.goto_launch_requested.connect(lambda *args: self.navigate_requested.emit("launch"))
        self.layout.addWidget(self.pool_monitor)

        # Section: Recent Completed Missions
        sec_hist = QLabel("📋 Recent Completed Missions")
        sec_hist.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 4px; margin-top: 14px;")
        self.layout.addWidget(sec_hist)

        self.recent_missions_container = QWidget()
        self.recent_missions_layout = QVBoxLayout(self.recent_missions_container)
        self.recent_missions_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_missions_layout.setSpacing(8)
        self.layout.addWidget(self.recent_missions_container)

        self.layout.addStretch()
        scroll.setWidget(container)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(scroll)

    def refresh_data(self, tasks: list, memories: list, subagents: list, running_procs: dict):
        try:
            from services.token_manager import get_token_manager
            tm = get_token_manager()
            stats = tm.get_lifetime_stats()
            consumed = stats.get("lifetime_total_tokens", 0)
            if consumed > 0:
                self.card_tokens.set_value(f"{consumed/1000:.1f}k" if consumed < 1000000 else f"{consumed/1000000:.2f}M")
            else:
                self.card_tokens.set_value("1.019B+")
        except Exception:
            self.card_tokens.set_value("1.019B+")

        self.card_tasks.set_value(str(len(tasks)))
        self.card_mem.set_value(str(len(memories)))
        self.card_squads.set_value(str(len(subagents)))
        self.card_skills.set_value(str(get_skills_count()))

        active_count = sum(1 for v in running_procs.values() if v.get("status") == "running")
        self.card_active.set_value(str(active_count))

        self.pool_monitor.refresh_pool()

        # Only re-render recent missions if task list or count changed
        current_task_keys = tuple(t.get("filename", "") for t in tasks[:5])
        if getattr(self, "_last_task_keys", None) == current_task_keys:
            return
        self._last_task_keys = current_task_keys

        # Render recent missions
        while self.recent_missions_layout.count():
            item = self.recent_missions_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not tasks:
            no_tasks_lbl = QLabel("No missions executed yet. Dispatch a task to begin.")
            no_tasks_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 10px;")
            self.recent_missions_layout.addWidget(no_tasks_lbl)
        else:
            for i, t in enumerate(tasks[:5]):
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background: rgba(15, 23, 42, 0.6);
                        border: 1px solid rgba(255, 255, 255, 0.07);
                        border-radius: 8px;
                        padding: 10px;
                    }
                    QFrame:hover {
                        border-color: rgba(56, 189, 248, 0.35);
                    }
                """)
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(8, 8, 8, 8)

                left_v = QVBoxLayout()
                t_lbl = QLabel(f"<b>#{len(tasks)-i}</b>  {t.get('task', 'Untitled Mission')}")
                t_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #f8fafc;")
                time_lbl = QLabel(t.get('timestamp', ''))
                time_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-family: monospace;")
                left_v.addWidget(t_lbl)
                left_v.addWidget(time_lbl)

                badge = QLabel("COMPLETED")
                badge.setStyleSheet("background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b98155; border-radius: 10px; padding: 2px 10px; font-weight: 800; font-size: 10px;")

                c_layout.addLayout(left_v)
                c_layout.addStretch()
                c_layout.addWidget(badge)
                self.recent_missions_layout.addWidget(card)

    def update_running_processes(self, procs: dict):
        if hasattr(self, "pool_monitor") and self.pool_monitor:
            self.pool_monitor.update_running_processes(procs)
