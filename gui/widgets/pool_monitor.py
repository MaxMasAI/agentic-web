"""
gui/widgets/pool_monitor.py - Real-Time Multi-Agent Command Hierarchy & Live Pool Monitor
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QRadioButton, QButtonGroup, QScrollArea, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from gui.theme import MODEL_THEMES
from core.agent_status import get_all_agent_status, set_agent_state
from core.agentlist import get_lead_agent
from gui.widgets.add_agent_dialog import AddAgentDialog


class AddAgentCard(QFrame):
    add_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.45);
                border: 2px dashed rgba(56, 189, 248, 0.4);
                border-radius: 10px;
                padding: 10px;
                min-height: 120px;
            }
            QFrame:hover {
                border-color: #38bdf8;
                background-color: rgba(56, 189, 248, 0.1);
            }
        """)
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        icon_lbl = QLabel("➕")
        icon_lbl.setAlignment(Qt.AlignCenter)
        icon_lbl.setStyleSheet("font-size: 24px; color: #38bdf8;")
        layout.addWidget(icon_lbl)

        title_lbl = QLabel("Add New AI Agent")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #ffffff;")
        layout.addWidget(title_lbl)

        sub_lbl = QLabel("Register custom model schema")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        layout.addWidget(sub_lbl)

        btn_add = QPushButton("✨ Add Agent")
        btn_add.setFixedHeight(26)
        btn_add.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.2);
                color: #38bdf8;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 5px;
                font-size: 11px;
                font-weight: 700;
                padding: 0 12px;
            }
            QPushButton:hover {
                background-color: #38bdf8;
                color: #0b1120;
            }
        """)
        btn_add.clicked.connect(self.add_clicked.emit)
        layout.addWidget(btn_add)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.add_clicked.emit()
        super().mousePressEvent(event)


class AgentCard(QFrame):
    inspect_clicked = Signal(str)

    def __init__(self, agent_id: str, info: dict, parent=None):
        super().__init__(parent)
        self.agent_id = agent_id
        self.info = info
        self.init_ui()

    def init_ui(self):
        state = self.info.get("state", "FREE").upper()
        theme = MODEL_THEMES.get(self.agent_id, {
            "name": self.info.get("name", self.agent_id),
            "role": self.info.get("role", "Specialist"),
            "icon": "🤖",
            "color": "#38bdf8",
            "vendor": "AI Specialist"
        })

        is_leader = self.agent_id == "gemini" or state in ("LEADER", "REVIEWING")
        is_busy = state == "BUSY"

        border_color = "#38bdf8" if is_leader else ("#f59e0b" if is_busy else "#10b981")
        bg_color = "rgba(12, 38, 56, 0.65)" if is_leader else ("rgba(41, 29, 10, 0.6)" if is_busy else "rgba(15, 23, 42, 0.75)")

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-left: 4px solid {border_color};
                border-radius: 10px;
                padding: 10px;
            }}
            QFrame:hover {{
                border-color: {border_color};
                background-color: rgba(19, 29, 49, 0.9);
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header Row
        header = QHBoxLayout()
        name_lbl = QLabel(f"{theme['icon']}  {self.info.get('name', theme['name'])}")
        name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: #ffffff;")
        header.addWidget(name_lbl)
        header.addStretch()

        badge_color = "#38bdf8" if is_leader else ("#fbbf24" if is_busy else "#34d399")
        badge_bg = "rgba(56, 189, 248, 0.15)" if is_leader else ("rgba(245, 158, 11, 0.15)" if is_busy else "rgba(16, 185, 129, 0.15)")
        badge_lbl = QLabel(state)
        badge_lbl.setStyleSheet(f"""
            background-color: {badge_bg};
            color: {badge_color};
            border: 1px solid {badge_color}55;
            border-radius: 10px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 800;
        """)
        header.addWidget(badge_lbl)
        layout.addLayout(header)

        # Vendor & Role
        meta_lbl = QLabel(f"{theme['vendor']} · {self.info.get('role', theme['role'])}")
        meta_lbl.setStyleSheet(f"font-size: 11px; color: {theme['color']}; font-family: monospace;")
        layout.addWidget(meta_lbl)

        # Activity
        task_text = self.info.get("current_task", "Idle")
        activity_lbl = QLabel(f"<b>Activity:</b> {task_text}")
        activity_lbl.setWordWrap(True)
        activity_lbl.setStyleSheet(f"font-size: 11.5px; color: {'#fbbf24' if is_busy else '#cbd5e1'};")
        layout.addWidget(activity_lbl)

        layout.addSpacing(4)

        # Inspect Button
        inspect_btn = QPushButton(f"🔍 Inspect {self.info.get('name', theme['name'])}")
        inspect_btn.setFixedHeight(26)
        inspect_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(15, 23, 42, 0.8);
                color: #cbd5e1;
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 5px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.2);
                color: #38bdf8;
                border-color: #38bdf8;
            }
        """)
        inspect_btn.setCursor(QCursor(Qt.PointingHandCursor))
        inspect_btn.clicked.connect(lambda: self.inspect_clicked.emit(self.agent_id))
        layout.addWidget(inspect_btn)


class PoolMonitor(QWidget):
    direct_task_submitted = Signal(str)
    goto_launch_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.inspected_agent_id = None
        self.view_mode = "tree"  # "tree" or "grid"
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(14)

        # Telemetry Metrics Header Row
        self.telemetry_layout = QHBoxLayout()
        self.m_free = QLabel()
        self.m_busy = QLabel()
        self.m_leader = QLabel()
        self.m_total = QLabel()

        for lbl, col in [(self.m_free, "#10b981"), (self.m_busy, "#f59e0b"), (self.m_leader, "#38bdf8"), (self.m_total, "#818cf8")]:
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"""
                background-color: rgba(15, 23, 42, 0.75);
                border: 1px solid {col}44;
                border-radius: 10px;
                padding: 10px;
                color: {col};
                font-weight: 700;
            """)
            self.telemetry_layout.addWidget(lbl)

        self.main_layout.addLayout(self.telemetry_layout)

        # Mode Selector
        mode_row = QHBoxLayout()
        mode_lbl = QLabel("Hierarchy Layout Display:")
        mode_lbl.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 12px;")
        mode_row.addWidget(mode_lbl)

        self.rb_tree = QRadioButton("🌳 Tree Hierarchy Format")
        self.rb_tree.setChecked(True)
        self.rb_tree.toggled.connect(self.on_mode_toggled)
        
        self.rb_grid = QRadioButton("🗂️ Symmetrical Grid Format")
        self.rb_grid.toggled.connect(self.on_mode_toggled)

        self.bg_mode = QButtonGroup(self)
        self.bg_mode.addButton(self.rb_tree)
        self.bg_mode.addButton(self.rb_grid)

        mode_row.addWidget(self.rb_tree)
        mode_row.addWidget(self.rb_grid)
        mode_row.addStretch()
        self.main_layout.addLayout(mode_row)

        # Content Container for Pool
        self.pool_container = QWidget()
        self.pool_layout = QVBoxLayout(self.pool_container)
        self.pool_layout.setContentsMargins(0, 0, 0, 0)
        self.pool_layout.setSpacing(10)
        self.main_layout.addWidget(self.pool_container)

        # Inspection Drawer Frame
        self.inspector_frame = QFrame()
        self.inspector_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(15, 23, 42, 0.95);
                border: 2px solid #38bdf8;
                border-radius: 12px;
                padding: 14px;
            }
        """)
        self.inspector_layout = QVBoxLayout(self.inspector_frame)
        self.inspector_layout.setContentsMargins(12, 12, 12, 12)
        self.inspector_layout.setSpacing(8)
        self.inspector_frame.hide()
        self.main_layout.addWidget(self.inspector_frame)

        self.refresh_pool()

    def on_mode_toggled(self):
        self.view_mode = "tree" if self.rb_tree.isChecked() else "grid"
        self.refresh_pool()

    def refresh_pool(self):
        statuses = get_all_agent_status()
        if not statuses:
            return

        lead_agent = get_lead_agent()
        lead_id = lead_agent["id"]

        worker_statuses = {aid: s for aid, s in statuses.items() if aid != lead_id}
        busy_count = sum(1 for s in worker_statuses.values() if s.get("state", "").upper() == "BUSY")
        free_count = len(worker_statuses) - busy_count
        leader_count = 1 if lead_id in statuses else 0
        total_count = len(statuses)

        lead_name = lead_agent.get("name", "Leader")
        self.m_free.setText(f"<div style='font-size:18px;font-weight:800;'>{free_count}</div><div style='font-size:10px;'>🟢 Free Specialists ({free_count}/{len(worker_statuses)})</div>")
        self.m_busy.setText(f"<div style='font-size:18px;font-weight:800;'>{busy_count}</div><div style='font-size:10px;'>🟡 Busy Models ({busy_count}/{len(worker_statuses)})</div>")
        self.m_leader.setText(f"<div style='font-size:18px;font-weight:800;'>{leader_count}</div><div style='font-size:10px;'>👑 Master Leader ({lead_name})</div>")
        self.m_total.setText(f"<div style='font-size:18px;font-weight:800;'>{total_count}</div><div style='font-size:10px;'>🤖 Total Active Roster</div>")

        # Clear pool layout safely
        while self.pool_layout.count():
            item = self.pool_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            l = item.layout()
            if l:
                while l.count():
                    sub = l.takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        if self.view_mode == "tree":
            self.render_tree_format(statuses)
        else:
            self.render_grid_format(statuses)

        if self.inspected_agent_id and self.inspected_agent_id in statuses:
            self.render_inspector(statuses[self.inspected_agent_id])
        else:
            self.inspector_frame.hide()

    def render_tree_format(self, statuses: dict):
        lead_agent = get_lead_agent()
        lead_id = lead_agent["id"]

        lead_info = statuses.get(lead_id, {
            "name": lead_agent.get("name", "Google Gemini"),
            "role": lead_agent.get("role", "Master Orchestrator & Leadership Lead"),
            "state": "LEADER",
            "current_task": "Master Orchestrator - Directing workflow"
        })

        # Master Leader Node
        leader_box = QFrame()
        leader_box.setStyleSheet("""
            QFrame {
                background-color: rgba(12, 38, 56, 0.85);
                border: 2px solid #38bdf8;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        l_layout = QVBoxLayout(leader_box)
        l_layout.setContentsMargins(12, 10, 12, 10)
        l_layout.setSpacing(6)

        top_l = QHBoxLayout()
        title_l = QLabel(f"👑 {lead_info.get('name', 'Google Gemini')}")
        title_l.setStyleSheet("font-size: 15px; font-weight: 800; color: #38bdf8;")
        top_l.addWidget(title_l)
        top_l.addStretch()

        b_lbl = QLabel("MASTER ORCHESTRATOR")
        b_lbl.setStyleSheet("background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf866; border-radius: 10px; padding: 2px 10px; font-size: 10px; font-weight: 800;")
        top_l.addWidget(b_lbl)
        l_layout.addLayout(top_l)

        vendor = "Google DeepMind" if lead_id == "gemini" else "Custom Orchestrator"
        desc_l = QLabel(f"{vendor} · {lead_info.get('role', 'Master Leader')}")
        desc_l.setStyleSheet("font-size: 11px; color: #94a3b8; font-family: monospace;")
        l_layout.addWidget(desc_l)

        act_l = QLabel(f"<b>State:</b> {lead_info.get('current_task', 'Orchestrating Specialist Workers')}")
        act_l.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        l_layout.addWidget(act_l)

        # Direct Task Assignment Bar
        direct_row = QHBoxLayout()
        self.direct_input = QLineEdit()
        self.direct_input.setPlaceholderText(f"🎯 Type mission goal here to directly assign task to {lead_info.get('name', 'Leader')} & workers...")
        self.direct_input.returnPressed.connect(self.submit_direct_task)
        direct_row.addWidget(self.direct_input, stretch=3)

        btn_assign = QPushButton(f"🚀 Assign to {lead_info.get('name', 'Leader')}")
        btn_assign.setProperty("class", "primary-btn")
        btn_assign.setCursor(QCursor(Qt.PointingHandCursor))
        btn_assign.clicked.connect(self.submit_direct_task)
        direct_row.addWidget(btn_assign, stretch=1)

        btn_insp_gem = QPushButton(f"🔍 Inspect {lead_info.get('name', 'Leader')}")
        btn_insp_gem.setCursor(QCursor(Qt.PointingHandCursor))
        btn_insp_gem.clicked.connect(lambda: self.inspect_agent(lead_id))
        direct_row.addWidget(btn_insp_gem, stretch=1)

        l_layout.addLayout(direct_row)
        self.pool_layout.addWidget(leader_box)

        # Flow Arrow
        arrow_lbl = QLabel("▼")
        arrow_lbl.setAlignment(Qt.AlignCenter)
        arrow_lbl.setStyleSheet("color: #38bdf8; font-size: 20px; font-weight: 800; margin: 2px 0;")
        self.pool_layout.addWidget(arrow_lbl)

        # Header for Specialists
        workers = [aid for aid in statuses.keys() if aid != lead_id]
        spec_hdr = QLabel(f"══ SPECIALIST WORKER ROSTER ({len(workers)} DISTINCT MODELS) ══")
        spec_hdr.setAlignment(Qt.AlignCenter)
        spec_hdr.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        self.pool_layout.addWidget(spec_hdr)

        # 3x3 Grid for Workers + Add Agent Card at the end
        grid = QGridLayout()
        grid.setSpacing(10)

        for idx, aid in enumerate(workers):
            card = AgentCard(aid, statuses[aid])
            card.inspect_clicked.connect(self.inspect_agent)
            row = idx // 3
            col = idx % 3
            grid.addWidget(card, row, col)

        # Append "+" Add Agent Card at the end of all workers
        add_idx = len(workers)
        add_card = AddAgentCard()
        add_card.add_clicked.connect(self.open_add_agent_dialog)
        grid.addWidget(add_card, add_idx // 3, add_idx % 3)

        self.pool_layout.addLayout(grid)

    def render_grid_format(self, statuses: dict):
        grid = QGridLayout()
        grid.setSpacing(10)
        items = list(statuses.items())

        for idx, (aid, info) in enumerate(items):
            card = AgentCard(aid, info)
            card.inspect_clicked.connect(self.inspect_agent)
            row = idx // 3
            col = idx % 3
            grid.addWidget(card, row, col)

        # Append "+" Add Agent Card at the end of all models
        add_idx = len(items)
        add_card = AddAgentCard()
        add_card.add_clicked.connect(self.open_add_agent_dialog)
        grid.addWidget(add_card, add_idx // 3, add_idx % 3)

        self.pool_layout.addLayout(grid)

    def open_add_agent_dialog(self):
        dialog = AddAgentDialog(self)
        dialog.agent_added.connect(lambda agent: self.refresh_pool())
        dialog.exec()

    def submit_direct_task(self):
        if not hasattr(self, 'direct_input') or not self.direct_input:
            return
        txt = self.direct_input.text().strip()
        if txt:
            # Clear text before emitting to prevent re-entrant C++ object destruction errors
            self.direct_input.clear()
            self.direct_task_submitted.emit(txt)

    def inspect_agent(self, agent_id: str):
        self.inspected_agent_id = agent_id
        statuses = get_all_agent_status()
        if agent_id in statuses:
            self.render_inspector(statuses[agent_id])

    def render_inspector(self, info: dict):
        while self.inspector_layout.count():
            item = self.inspector_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            l = item.layout()
            if l:
                while l.count():
                    sub = l.takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        self.inspector_frame.show()

        state = info.get("state", "FREE")
        theme = MODEL_THEMES.get(self.inspected_agent_id, {"icon": "🤖", "color": "#38bdf8"})

        hdr = QHBoxLayout()
        title = QLabel(f"🔍 Live Activity Inspector: <span style='color:#38bdf8;'>{info.get('name', self.inspected_agent_id)}</span>")
        title.setStyleSheet("font-size: 14px; font-weight: 800; color: #f8fafc;")
        hdr.addWidget(title)
        hdr.addStretch()

        b_color = "#f59e0b" if state == "BUSY" else "#10b981"
        badge = QLabel(state)
        badge.setStyleSheet(f"background:{b_color}22; color:{b_color}; border:1px solid {b_color}66; border-radius:10px; padding:2px 10px; font-weight:800; font-size:10px;")
        hdr.addWidget(badge)
        self.inspector_layout.addLayout(hdr)

        details = QLabel(f"<b>Role & Specialization:</b> {info.get('role', 'Specialist')}<br><b>Current Work Status:</b> <span style='color:{'#fbbf24' if state == 'BUSY' else '#34d399'};font-weight:600;'>{info.get('current_task', 'Idle')}</span>")
        details.setStyleSheet("font-size: 12px; color: #cbd5e1; line-height: 1.6;")
        self.inspector_layout.addWidget(details)

        btn_row = QHBoxLayout()
        btn_launch = QPushButton("🚀 Open Live Mission Console")
        btn_launch.setProperty("class", "primary-btn")
        btn_launch.clicked.connect(self.goto_launch_requested.emit)
        btn_row.addWidget(btn_launch)

        btn_reset = QPushButton("🔄 Force Reset State to FREE")
        btn_reset.clicked.connect(self.reset_agent_state)
        btn_row.addWidget(btn_reset)

        btn_close = QPushButton("✖ Close Inspector")
        btn_close.clicked.connect(self.close_inspector)
        btn_row.addWidget(btn_close)

        self.inspector_layout.addLayout(btn_row)

    def reset_agent_state(self):
        if self.inspected_agent_id:
            set_agent_state(self.inspected_agent_id, "FREE", "Idle - Ready for assignment")
            self.refresh_pool()

    def close_inspector(self):
        self.inspected_agent_id = None
        self.inspector_frame.hide()
