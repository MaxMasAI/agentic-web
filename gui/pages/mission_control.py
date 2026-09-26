"""
gui/pages/mission_control.py - Mission Control (Home Page)
Conforms strictly to design_system_ui_theme_documentation.md
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QScrollArea,
    QFrame
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
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setProperty("class", "card")

        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)

        # Header Title Banner
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        
        main_title = QLabel("AGENT MISSION CONTROL")
        main_title.setProperty("class", "metric-value")
        
        subtitle = QLabel("Autonomous Leader-Worker Collaborative Operations Console")
        subtitle.setProperty("class", "metric-label")
        
        title_box.addWidget(main_title)
        title_box.addWidget(subtitle)
        self.layout.addLayout(title_box)

        # Interactive Telemetry Metric Cards (Clean 4x2 Grid to prevent horizontal overflow)
        self.cards_layout = QGridLayout()
        self.cards_layout.setSpacing(10)

        self.card_tokens = MetricCard("1.019B+", "Free Tokens", is_clickable=True)
        self.card_tokens.clicked.connect(lambda *args: self.navigate_requested.emit("tokens"))

        self.card_tasks = MetricCard("0", "Tasks Done", is_clickable=True)
        self.card_tasks.clicked.connect(lambda *args: self.navigate_requested.emit("history"))

        self.card_mem = MetricCard("0", "Memories", is_clickable=True)
        self.card_mem.clicked.connect(lambda *args: self.navigate_requested.emit("memory"))

        self.card_play = MetricCard("LIVE", "Playground", is_clickable=True)
        self.card_play.clicked.connect(lambda *args: self.navigate_requested.emit("playground"))

        self.card_squads = MetricCard("0", "Squad Roster", is_clickable=True)
        self.card_squads.clicked.connect(lambda *args: self.navigate_requested.emit("subagents"))

        self.card_skills = MetricCard("0", "Skills", is_clickable=True)
        self.card_skills.clicked.connect(self.on_open_skills_vault)

        self.card_assets = MetricCard("0", "Assets", is_clickable=True)
        self.card_assets.clicked.connect(lambda *args: self.navigate_requested.emit("explorer"))

        self.card_active = MetricCard("0", "Active Runs", is_clickable=True)
        self.card_active.clicked.connect(lambda *args: self.navigate_requested.emit("launch"))

        # Row 0: Operations & Storage
        self.cards_layout.addWidget(self.card_tokens, 0, 0)
        self.cards_layout.addWidget(self.card_tasks, 0, 1)
        self.cards_layout.addWidget(self.card_mem, 0, 2)
        self.cards_layout.addWidget(self.card_play, 0, 3)

        # Row 1: Ecosystem & Capabilities
        self.cards_layout.addWidget(self.card_squads, 1, 0)
        self.cards_layout.addWidget(self.card_skills, 1, 1)
        self.cards_layout.addWidget(self.card_assets, 1, 2)
        self.cards_layout.addWidget(self.card_active, 1, 3)

        self.layout.addLayout(self.cards_layout)

        # Section: Multi-Agent Command Hierarchy & Pool Monitor
        sec_hdr = QLabel("COMMAND HIERARCHY & LIVE POOL")
        sec_hdr.setProperty("class", "sidebar-group-label")
        self.layout.addWidget(sec_hdr)

        self.pool_monitor = PoolMonitor()
        self.pool_monitor.direct_task_submitted.connect(self.direct_task_submitted.emit)
        self.pool_monitor.multi_tasks_submitted.connect(self.multi_tasks_submitted.emit)
        self.pool_monitor.goto_launch_requested.connect(lambda *args: self.navigate_requested.emit("launch"))
        self.layout.addWidget(self.pool_monitor)

        # Section: Recent Completed Missions
        sec_hist = QLabel("RECENT COMPLETED MISSIONS")
        sec_hist.setProperty("class", "sidebar-group-label")
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
            no_tasks_lbl.setProperty("class", "metric-label")
            self.recent_missions_layout.addWidget(no_tasks_lbl)
        else:
            for i, t in enumerate(tasks[:5]):
                card = QFrame()
                card.setProperty("class", "card")
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(12, 8, 12, 8)

                left_v = QVBoxLayout()
                t_lbl = QLabel(f"#{len(tasks)-i}  {t.get('task', 'Untitled Mission')}")
                t_lbl.setProperty("class", "metric-value")
                time_lbl = QLabel(t.get('timestamp', ''))
                time_lbl.setProperty("class", "metric-label")
                left_v.addWidget(t_lbl)
                left_v.addWidget(time_lbl)

                badge = QLabel("COMPLETED")
                badge.setProperty("class", "badge-idle")

                c_layout.addLayout(left_v)
                c_layout.addStretch()
                c_layout.addWidget(badge)
                self.recent_missions_layout.addWidget(card)

    def on_open_skills_vault(self):
        try:
            from gui.widgets.skill_importer_dialog import SkillImporterDialog
            dialog = SkillImporterDialog(self)
            dialog.skills_updated.connect(lambda: self.card_skills.set_value(str(get_skills_count())))
            dialog.exec()
        except Exception:
            self.navigate_requested.emit("mcp")

    def update_running_processes(self, procs: dict):
        if hasattr(self, "pool_monitor") and self.pool_monitor:
            self.pool_monitor.update_running_processes(procs)
