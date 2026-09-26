"""
gui/widgets/pool_monitor.py - Real-Time Multi-Agent Command Hierarchy & Live Pool Monitor
Conforms strictly to design_system_ui_theme_documentation.md
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
from gui.widgets.slash_autocomplete import attach_slash_autocomplete
from gui.widgets.popout_dispatcher_widget import PopoutDispatcherWidget, PopoutDispatcherDialog


class AddAgentCard(QFrame):
    add_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AddAgentCard")
        self.setProperty("class", "card")
        self.init_ui()

    def init_ui(self):
        self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        title_lbl = QLabel("+ Register New Agent")
        title_lbl.setAlignment(Qt.AlignCenter)
        title_lbl.setProperty("class", "metric-value")
        layout.addWidget(title_lbl)

        sub_lbl = QLabel("Custom Model Persona Schema")
        sub_lbl.setAlignment(Qt.AlignCenter)
        sub_lbl.setProperty("class", "metric-label")
        layout.addWidget(sub_lbl)

        layout.addSpacing(4)

        btn_add = QPushButton("Add Agent")
        btn_add.setProperty("class", "btn-secondary")
        btn_add.setCursor(QCursor(Qt.PointingHandCursor))
        btn_add.clicked.connect(lambda *args: self.add_clicked.emit())
        layout.addWidget(btn_add)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.add_clicked.emit()
        super().mousePressEvent(event)


class AgentCard(QFrame):
    inspect_clicked = Signal(str)

    def __init__(self, agent_id: str, info: dict, parent=None):
        super().__init__(parent)
        self.setObjectName("AgentCard")
        self.agent_id = agent_id
        self.info = info
        self.init_ui()

    def init_ui(self):
        state = self.info.get("state", "FREE").upper()
        theme = MODEL_THEMES.get(self.agent_id, {
            "name": self.info.get("name", self.agent_id),
            "role": self.info.get("role", "Specialist"),
            "color": "#38BDF8",
            "vendor": "AI Specialist"
        })

        is_leader = self.agent_id == "gemini" or state in ("LEADER", "REVIEWING")
        is_busy = state == "BUSY"

        self.setProperty("class", "card-featured" if is_leader else "card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        # Header Row
        header = QHBoxLayout()
        name_lbl = QLabel(self.info.get('name', theme['name']))
        name_lbl.setProperty("class", "metric-value")
        header.addWidget(name_lbl)
        header.addStretch()

        badge_class = "badge-busy" if is_busy else "badge-idle"
        badge_lbl = QLabel(state)
        badge_lbl.setProperty("class", badge_class)
        header.addWidget(badge_lbl)
        layout.addLayout(header)

        # Vendor & Role
        meta_lbl = QLabel(f"{theme['vendor']} · {self.info.get('role', theme['role'])}")
        meta_lbl.setProperty("class", "metric-label")
        layout.addWidget(meta_lbl)

        # Activity
        task_text = self.info.get("current_task", "Idle")
        activity_lbl = QLabel(f"Activity: {task_text}")
        activity_lbl.setWordWrap(True)
        activity_lbl.setProperty("class", "metric-label")
        layout.addWidget(activity_lbl)

        layout.addSpacing(4)

        # Inspect Button
        inspect_btn = QPushButton(f"Inspect {self.info.get('name', theme['name'])}")
        inspect_btn.setProperty("class", "btn-secondary")
        inspect_btn.setCursor(QCursor(Qt.PointingHandCursor))
        inspect_btn.clicked.connect(lambda *args, aid=self.agent_id: self.inspect_clicked.emit(aid))
        layout.addWidget(inspect_btn)


class PoolMonitor(QWidget):
    direct_task_submitted = Signal(str)
    multi_tasks_submitted = Signal(list)
    goto_launch_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.inspected_agent_id = None
        self.view_mode = "tree"  # "tree" or "grid"
        self.running_procs = {}
        self.popout_dialogs = []
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(14)

        # Telemetry Metrics Header Row
        self.telemetry_layout = QHBoxLayout()
        self.telemetry_layout.setSpacing(10)

        self.card_free = QFrame()
        self.card_free.setProperty("class", "card")
        self.card_free_layout = QVBoxLayout(self.card_free)
        self.val_free = QLabel("0")
        self.val_free.setProperty("class", "metric-value")
        self.lbl_free = QLabel("FREE SPECIALISTS")
        self.lbl_free.setProperty("class", "metric-label")
        self.card_free_layout.addWidget(self.val_free, alignment=Qt.AlignCenter)
        self.card_free_layout.addWidget(self.lbl_free, alignment=Qt.AlignCenter)

        self.card_busy = QFrame()
        self.card_busy.setProperty("class", "card")
        self.card_busy_layout = QVBoxLayout(self.card_busy)
        self.val_busy = QLabel("0")
        self.val_busy.setProperty("class", "metric-value")
        self.lbl_busy = QLabel("BUSY MODELS")
        self.lbl_busy.setProperty("class", "metric-label")
        self.card_busy_layout.addWidget(self.val_busy, alignment=Qt.AlignCenter)
        self.card_busy_layout.addWidget(self.lbl_busy, alignment=Qt.AlignCenter)

        self.card_leader = QFrame()
        self.card_leader.setProperty("class", "card-featured")
        self.card_leader_layout = QVBoxLayout(self.card_leader)
        self.val_leader = QLabel("1")
        self.val_leader.setProperty("class", "metric-value")
        self.lbl_leader = QLabel("MASTER LEADER")
        self.lbl_leader.setProperty("class", "metric-label")
        self.card_leader_layout.addWidget(self.val_leader, alignment=Qt.AlignCenter)
        self.card_leader_layout.addWidget(self.lbl_leader, alignment=Qt.AlignCenter)

        self.card_total = QFrame()
        self.card_total.setProperty("class", "card")
        self.card_total_layout = QVBoxLayout(self.card_total)
        self.val_total = QLabel("0")
        self.val_total.setProperty("class", "metric-value")
        self.lbl_total = QLabel("TOTAL ROSTER")
        self.lbl_total.setProperty("class", "metric-label")
        self.card_total_layout.addWidget(self.val_total, alignment=Qt.AlignCenter)
        self.card_total_layout.addWidget(self.lbl_total, alignment=Qt.AlignCenter)

        for c in [self.card_free, self.card_busy, self.card_leader, self.card_total]:
            self.telemetry_layout.addWidget(c)

        self.main_layout.addLayout(self.telemetry_layout)

        # Mode Selector
        mode_row = QHBoxLayout()
        mode_lbl = QLabel("LAYOUT FORMAT:")
        mode_lbl.setProperty("class", "sidebar-group-label")
        mode_row.addWidget(mode_lbl)

        self.rb_tree = QRadioButton("Hierarchy Tree")
        self.rb_tree.setChecked(True)
        self.rb_tree.toggled.connect(self.on_mode_toggled)
        
        self.rb_grid = QRadioButton("Symmetrical Grid")
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
        self.inspector_frame.setObjectName("InspectorFrame")
        self.inspector_frame.setProperty("class", "card-featured")
        self.inspector_layout = QVBoxLayout(self.inspector_frame)
        self.inspector_layout.setContentsMargins(14, 14, 14, 14)
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
        self.val_free.setText(str(free_count))
        self.lbl_free.setText(f"FREE SPECIALISTS ({free_count}/{len(worker_statuses)})")
        
        self.val_busy.setText(str(busy_count))
        self.lbl_busy.setText(f"BUSY MODELS ({busy_count}/{len(worker_statuses)})")
        
        self.val_leader.setText(str(leader_count))
        self.lbl_leader.setText(f"MASTER LEADER ({lead_name})")
        
        self.val_total.setText(str(total_count))
        self.lbl_total.setText("TOTAL ACTIVE ROSTER")

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
        leader_box.setObjectName("LeaderBox")
        leader_box.setProperty("class", "card-featured")
        l_layout = QVBoxLayout(leader_box)
        l_layout.setContentsMargins(14, 14, 14, 14)
        l_layout.setSpacing(8)

        top_l = QHBoxLayout()
        title_l = QLabel(lead_info.get('name', 'Google Gemini'))
        title_l.setProperty("class", "metric-value")
        top_l.addWidget(title_l)
        top_l.addStretch()

        b_lbl = QLabel("MASTER ORCHESTRATOR")
        b_lbl.setProperty("class", "badge-idle")
        top_l.addWidget(b_lbl)
        l_layout.addLayout(top_l)

        vendor = "Google DeepMind" if lead_id == "gemini" else "Custom Orchestrator"
        desc_l = QLabel(f"{vendor} · {lead_info.get('role', 'Master Leader')}")
        desc_l.setProperty("class", "metric-label")
        l_layout.addWidget(desc_l)

        act_l = QLabel(f"State: {lead_info.get('current_task', 'Orchestrating Specialist Workers')}")
        act_l.setProperty("class", "metric-label")
        l_layout.addWidget(act_l)

        # Direct Task Assignment Bar
        direct_row = QHBoxLayout()
        direct_row.setSpacing(8)
        self.direct_input = QLineEdit()
        self.direct_input.setPlaceholderText("Enter goal or control via /{names} - task (e.g. /deepseek - code app, /claude,chatgpt - review, /all - dispatch)...")
        self.direct_input.returnPressed.connect(self.submit_direct_task)
        attach_slash_autocomplete(self.direct_input)
        direct_row.addWidget(self.direct_input, stretch=3)

        btn_assign = QPushButton("Dispatch Task")
        btn_assign.setProperty("class", "btn-primary")
        btn_assign.setCursor(QCursor(Qt.PointingHandCursor))
        btn_assign.clicked.connect(self.submit_direct_task)
        direct_row.addWidget(btn_assign, stretch=1)

        btn_popout_disp = QPushButton("Pop-out Dispatcher")
        btn_popout_disp.setProperty("class", "btn-secondary")
        btn_popout_disp.setCursor(QCursor(Qt.PointingHandCursor))
        btn_popout_disp.clicked.connect(self.toggle_popout_dispatcher)
        direct_row.addWidget(btn_popout_disp, stretch=1)

        btn_insp_gem = QPushButton(f"Inspect {lead_info.get('name', 'Leader')}")
        btn_insp_gem.setProperty("class", "btn-secondary")
        btn_insp_gem.setCursor(QCursor(Qt.PointingHandCursor))
        btn_insp_gem.clicked.connect(lambda *args, lid=lead_id: self.inspect_agent(lid))
        direct_row.addWidget(btn_insp_gem, stretch=1)

        l_layout.addLayout(direct_row)

        # Embedded Pop-out Task Dispatcher Section
        self.popout_dispatcher = PopoutDispatcherWidget(self)
        self.popout_dispatcher.hide()
        self.popout_dispatcher.task_dispatched.connect(lambda t, a, l: self.direct_task_submitted.emit(t))
        self.popout_dispatcher.multi_tasks_dispatched.connect(self.multi_tasks_submitted.emit)
        if self.running_procs:
            self.popout_dispatcher.update_running_processes(self.running_procs)
        l_layout.addWidget(self.popout_dispatcher)

        self.pool_layout.addWidget(leader_box)

        # Header for Specialists
        workers = [aid for aid in statuses.keys() if aid != lead_id]
        spec_hdr = QLabel(f"SPECIALIST WORKER ROSTER ({len(workers)} MODELS)")
        spec_hdr.setAlignment(Qt.AlignCenter)
        spec_hdr.setProperty("class", "sidebar-group-label")
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

    def open_add_agent_dialog(self, *args):
        dialog = AddAgentDialog(self)
        dialog.agent_added.connect(lambda *_: self.refresh_pool())
        dialog.exec()

    def open_in_agents_tab(self):
        txt = self.direct_input.text().strip() if hasattr(self, 'direct_input') and self.direct_input else ""
        if txt:
            self.direct_input.clear()
            self.direct_task_submitted.emit(txt)
        else:
            self.goto_launch_requested.emit("launch")

    def toggle_popout_dispatcher(self):
        self.open_popout_dispatcher()

    def open_popout_dispatcher(self, initial_text: str = ""):
        if not initial_text and hasattr(self, 'direct_input') and self.direct_input.text().strip():
            initial_text = self.direct_input.text().strip()
            self.direct_input.clear()

        dialog = PopoutDispatcherDialog(parent=self, initial_text=initial_text, running_procs=self.running_procs)
        dialog.task_dispatched.connect(lambda t, a, l: self.direct_task_submitted.emit(t))
        dialog.multi_tasks_dispatched.connect(self.multi_tasks_submitted.emit)
        dialog.new_window_requested.connect(lambda: self.open_popout_dispatcher())
        self.popout_dialogs.append(dialog)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def update_running_processes(self, procs: dict):
        self.running_procs = procs
        if hasattr(self, 'popout_dispatcher') and self.popout_dispatcher:
            self.popout_dispatcher.update_running_processes(procs)
        # Update all active multi-window dialogs
        for dlg in list(getattr(self, 'popout_dialogs', [])):
            try:
                if dlg.isVisible():
                    dlg.update_running_processes(procs)
            except Exception:
                pass
        for dlg in list(PopoutDispatcherDialog._active_dialogs):
            try:
                if dlg.isVisible():
                    dlg.update_running_processes(procs)
            except Exception:
                pass

    def submit_direct_task(self):
        if not hasattr(self, 'direct_input') or not self.direct_input:
            return
        txt = self.direct_input.text().strip()
        if txt:
            self.direct_input.clear()
            self.direct_task_submitted.emit(txt)

    def inspect_agent(self, agent_id: str):
        self.inspected_agent_id = str(agent_id).strip()
        statuses = get_all_agent_status()
        if self.inspected_agent_id in statuses:
            self.render_inspector(statuses[self.inspected_agent_id])
        else:
            from core import agentlist
            agent_meta = agentlist.get_agent_by_id(self.inspected_agent_id) or {}
            info = {
                "id": self.inspected_agent_id,
                "name": agent_meta.get("name", self.inspected_agent_id),
                "role": agent_meta.get("role", "Specialist"),
                "specialization": agent_meta.get("specialization", ""),
                "state": "FREE",
                "current_task": "Idle - Ready for assignment"
            }
            self.render_inspector(info)

    def _clear_inspector_layout(self):
        while self.inspector_layout.count():
            item = self.inspector_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
            l = item.layout()
            if l is not None:
                while l.count():
                    sub = l.takeAt(0)
                    if sub.widget() is not None:
                        sub.widget().deleteLater()

    def render_inspector(self, info: dict):
        self._clear_inspector_layout()
        self.inspector_frame.show()

        state = info.get("state", "FREE")

        hdr = QHBoxLayout()
        title = QLabel(f"Live Activity Inspector: {info.get('name', self.inspected_agent_id)}")
        title.setProperty("class", "metric-value")
        hdr.addWidget(title)
        hdr.addStretch()

        badge_class = "badge-busy" if state == "BUSY" else "badge-idle"
        badge = QLabel(state)
        badge.setProperty("class", badge_class)
        hdr.addWidget(badge)
        self.inspector_layout.addLayout(hdr)

        details = QLabel(f"Role: {info.get('role', 'Specialist')}\nStatus: {info.get('current_task', 'Idle')}")
        details.setProperty("class", "metric-label")
        self.inspector_layout.addWidget(details)

        btn_row = QHBoxLayout()
        btn_launch = QPushButton("Open Mission Console")
        btn_launch.setProperty("class", "btn-primary")
        btn_launch.clicked.connect(lambda *args: self.goto_launch_requested.emit("launch"))
        btn_row.addWidget(btn_launch)

        btn_reset = QPushButton("Reset State")
        btn_reset.setProperty("class", "btn-secondary")
        btn_reset.clicked.connect(lambda *args: self.reset_agent_state())
        btn_row.addWidget(btn_reset)

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "btn-secondary")
        btn_close.clicked.connect(lambda *args: self.close_inspector())
        btn_row.addWidget(btn_close)

        self.inspector_layout.addLayout(btn_row)

    def reset_agent_state(self, *args):
        if self.inspected_agent_id:
            set_agent_state(self.inspected_agent_id, "FREE", "Idle - Ready for assignment")
            self.refresh_pool()

    def close_inspector(self, *args):
        self.inspected_agent_id = None
        self.inspector_frame.hide()
