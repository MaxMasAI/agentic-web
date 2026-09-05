"""
gui/tools/scheduler_view.py - Task Scheduler & Crontab Management
"""

import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QSpinBox, QScrollArea, QFrame,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal

from services.scheduler_service import (
    load_scheduler_jobs, save_scheduler_jobs,
    add_scheduler_job, delete_scheduler_job
)


class SchedulerPage(QWidget):
    trigger_job_requested = Signal(str, str, str)

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
        title = QLabel("⏰ TASK SCHEDULER & CRONTAB")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Automated Recurring AI Missions, Scheduled Web Monitors & Background Jobs")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Split: Add Job Form vs Active Jobs List
        split = QHBoxLayout()
        split.setSpacing(18)

        # Left: Add Job Form
        left_v = QVBoxLayout()
        left_v.setSpacing(10)

        left_v.addWidget(QLabel("<b>Job Codename:</b>"))
        self.job_name_edit = QLineEdit()
        self.job_name_edit.setPlaceholderText("e.g. Daily Tech News Digest, Hourly Crypto Scrape")
        left_v.addWidget(self.job_name_edit)

        left_v.addWidget(QLabel("<b>Mission Goal / Prompt:</b>"))
        self.job_task_edit = QTextEdit()
        self.job_task_edit.setPlaceholderText("Describe the scheduled task instructions...")
        self.job_task_edit.setFixedHeight(110)
        left_v.addWidget(self.job_task_edit)

        row_cfg = QHBoxLayout()
        row_cfg.addWidget(QLabel("<b>Run Every (Minutes):</b>"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 1440)
        self.interval_spin.setValue(60)
        row_cfg.addWidget(self.interval_spin)
        left_v.addLayout(row_cfg)

        left_v.addWidget(QLabel("<b>Agent Selection:</b>"))
        self.agents_edit = QLineEdit("auto")
        left_v.addWidget(self.agents_edit)

        self.btn_add_job = QPushButton("➕ Schedule Recurring Job")
        self.btn_add_job.setProperty("class", "primary-btn")
        self.btn_add_job.setFixedHeight(38)
        self.btn_add_job.clicked.connect(self.on_add_job)
        left_v.addWidget(self.btn_add_job)

        left_v.addStretch()
        split.addLayout(left_v, stretch=1)

        # Right: Active Jobs List
        right_v = QVBoxLayout()
        right_v.setSpacing(10)
        right_v.addWidget(QLabel("<b>📋 Active Scheduled Cron Jobs:</b>"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.jobs_container = QWidget()
        self.jobs_layout = QVBoxLayout(self.jobs_container)
        self.jobs_layout.setContentsMargins(0, 0, 0, 0)
        self.jobs_layout.setSpacing(10)
        scroll.setWidget(self.jobs_container)

        right_v.addWidget(scroll, stretch=1)
        split.addLayout(right_v, stretch=1)

        main_layout.addLayout(split)
        self.refresh_jobs()

    def on_add_job(self):
        name = self.job_name_edit.text().strip()
        task = self.job_task_edit.toPlainText().strip()
        if not name or not task:
            QMessageBox.warning(self, "Missing Fields", "Please enter a Job name and Mission instructions.")
            return

        interval = self.interval_spin.value()
        agents = self.agents_edit.text().strip() or "auto"

        add_scheduler_job(name, task, interval, agents)
        self.job_name_edit.clear()
        self.job_task_edit.clear()
        self.refresh_jobs()
        QMessageBox.information(self, "Scheduled", f"Job '{name}' scheduled to run every {interval} minute(s)!")

    def refresh_jobs(self):
        while self.jobs_layout.count():
            item = self.jobs_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        jobs = load_scheduler_jobs()
        if not jobs:
            empty = QLabel("No active scheduled jobs.")
            empty.setStyleSheet("color: #64748b; font-style: italic; padding: 12px;")
            self.jobs_layout.addWidget(empty)
            return

        for j in jobs:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(15, 23, 42, 0.75);
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    border-left: 4px solid #38bdf8;
                    border-radius: 8px;
                    padding: 8px;
                }
            """)
            c_v = QVBoxLayout(card)
            c_v.setContentsMargins(8, 8, 8, 8)
            c_v.setSpacing(4)

            hdr = QHBoxLayout()
            title = QLabel(f"⏰ <b>{j.get('name', 'Job')}</b>")
            title.setStyleSheet("font-size: 13.5px; color: #f8fafc;")
            hdr.addWidget(title)
            hdr.addStretch()

            badge = QLabel(f"EVERY {j.get('interval_minutes', 60)}m")
            badge.setStyleSheet("background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf866; border-radius: 10px; padding: 2px 8px; font-size: 9px; font-weight: 800;")
            hdr.addWidget(badge)
            c_v.addLayout(hdr)

            meta = QLabel(f"<b>Next Run:</b> {j.get('next_run','')}  |  <b>Agents:</b> <code>{j.get('agents','auto')}</code>")
            meta.setStyleSheet("font-size: 11px; color: #94a3b8; font-family: monospace;")
            c_v.addWidget(meta)

            task_lbl = QLabel(f"<b>Task:</b> {j.get('task','')[:90]}...")
            task_lbl.setStyleSheet("font-size: 11.5px; color: #cbd5e1;")
            c_v.addWidget(task_lbl)

            btn_row = QHBoxLayout()
            btn_run = QPushButton("⚡ Trigger Immediately")
            btn_run.setProperty("class", "primary-btn")
            btn_run.setFixedHeight(26)
            btn_run.clicked.connect(lambda _, job=j: self.trigger_job(job))
            btn_row.addWidget(btn_run)

            btn_del = QPushButton("🗑️ Remove")
            btn_del.setProperty("class", "danger-btn")
            btn_del.setFixedHeight(26)
            btn_del.clicked.connect(lambda _, jid=j["id"]: self.delete_job(jid))
            btn_row.addWidget(btn_del)

            c_v.addLayout(btn_row)
            self.jobs_layout.addWidget(card)

    def trigger_job(self, job_dict: dict):
        label = f"Scheduled: {job_dict.get('name')} @ {time.strftime('%H:%M:%S')}"
        self.trigger_job_requested.emit(job_dict.get("task", ""), job_dict.get("agents", "auto"), label)

    def delete_job(self, job_id: str):
        delete_scheduler_job(job_id)
        self.refresh_jobs()
