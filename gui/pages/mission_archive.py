"""
gui/pages/mission_archive.py - Mission Archive, Deliverable Inspector & Screenshot Lightboxes
"""

import os
import re
import glob
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QTabWidget, QTextEdit, QPlainTextEdit, QPushButton, QScrollArea,
    QFrame, QMessageBox, QTextBrowser
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QCursor

from gui.widgets.lightbox import LightboxDialog

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    HAS_WEBENGINE = True
except ImportError:
    HAS_WEBENGINE = False


class ClickableImageLabel(QLabel):
    clicked = Signal(str)

    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setToolTip("Click to inspect full resolution in Lightbox")

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and os.path.exists(self.image_path):
            self.clicked.emit(self.image_path)
        super().mousePressEvent(event)


class MissionArchivePage(QWidget):
    open_in_playground_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_tasks = []
        self.filtered_tasks = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("📋 MISSION ARCHIVE")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Audit Completed Missions, Agent Plans, Worker Outputs & Deliverable Sandboxes")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Search & Selector Bar
        search_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search Archive by keyword...")
        self.search_edit.textChanged.connect(self.filter_tasks)
        search_row.addWidget(self.search_edit, stretch=1)

        self.task_combo = QComboBox()
        self.task_combo.currentIndexChanged.connect(self.display_selected_task)
        search_row.addWidget(self.task_combo, stretch=2)

        main_layout.addLayout(search_row)

        # Selected Mission Header Card
        self.mission_card = QFrame()
        self.mission_card.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        m_layout = QVBoxLayout(self.mission_card)
        self.card_task_lbl = QLabel("No mission selected")
        self.card_task_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        self.card_time_lbl = QLabel()
        self.card_time_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-family: monospace;")
        m_layout.addWidget(self.card_task_lbl)
        m_layout.addWidget(self.card_time_lbl)
        main_layout.addWidget(self.mission_card)

        # 5 Inspection Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: Gemini Plan
        self.tab_plan = QWidget()
        self.plan_layout = QHBoxLayout(self.tab_plan)
        self.plan_text = QTextEdit()
        self.plan_text.setReadOnly(True)
        self.plan_img = ClickableImageLabel("")
        self.plan_img.setAlignment(Qt.AlignCenter)
        self.plan_img.clicked.connect(self.open_lightbox)
        self.plan_layout.addWidget(self.plan_text, stretch=2)
        self.plan_layout.addWidget(self.plan_img, stretch=1)
        self.tabs.addTab(self.tab_plan, "📐 Gemini Plan")

        # Tab 2: Worker Outputs
        self.tab_workers = QWidget()
        self.workers_scroll = QScrollArea(self.tab_workers)
        self.workers_scroll.setWidgetResizable(True)
        self.workers_scroll.setStyleSheet("border: none; background: transparent;")
        self.workers_container = QWidget()
        self.workers_layout = QVBoxLayout(self.workers_container)
        self.workers_layout.setSpacing(12)
        self.workers_scroll.setWidget(self.workers_container)
        w_main_v = QVBoxLayout(self.tab_workers)
        w_main_v.setContentsMargins(0, 0, 0, 0)
        w_main_v.addWidget(self.workers_scroll)
        self.tabs.addTab(self.tab_workers, "🛠️ Worker Outputs")

        # Tab 3: Final Approved Result
        self.tab_final = QWidget()
        self.final_layout = QHBoxLayout(self.tab_final)
        self.final_text = QTextEdit()
        self.final_text.setReadOnly(True)
        self.final_img = ClickableImageLabel("")
        self.final_img.setAlignment(Qt.AlignCenter)
        self.final_img.clicked.connect(self.open_lightbox)
        self.final_layout.addWidget(self.final_text, stretch=2)
        self.final_layout.addWidget(self.final_img, stretch=1)
        self.tabs.addTab(self.tab_final, "✅ Final Approved Result")

        # Tab 4: Live Sandbox Preview
        self.tab_live = QWidget()
        self.live_layout = QVBoxLayout(self.tab_live)
        if HAS_WEBENGINE:
            self.live_web_view = QWebEngineView()
            self.live_web_view.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px;")
            self.live_layout.addWidget(self.live_web_view, stretch=1)
        else:
            self.live_web_view = QTextBrowser()
            self.live_web_view.setStyleSheet("background: #030712; color: #f8fafc; border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px;")
            self.live_layout.addWidget(self.live_web_view, stretch=1)

        self.btn_open_play = QPushButton("🎮 Open Deliverable in Playground Studio")
        self.btn_open_play.setProperty("class", "primary-btn")
        self.btn_open_play.clicked.connect(self.on_open_in_playground)
        self.live_layout.addWidget(self.btn_open_play)
        self.tabs.addTab(self.tab_live, "🖥️ Live Sandbox Preview")

        # Tab 5: Downloaded Assets
        self.tab_assets = QWidget()
        self.assets_scroll = QScrollArea(self.tab_assets)
        self.assets_scroll.setWidgetResizable(True)
        self.assets_scroll.setStyleSheet("border: none; background: transparent;")
        self.assets_container = QWidget()
        self.assets_layout = QVBoxLayout(self.assets_container)
        self.assets_layout.setSpacing(10)
        self.assets_scroll.setWidget(self.assets_container)
        a_main_v = QVBoxLayout(self.tab_assets)
        a_main_v.setContentsMargins(0, 0, 0, 0)
        a_main_v.addWidget(self.assets_scroll)
        self.tabs.addTab(self.tab_assets, "📁 Downloaded Assets")

        main_layout.addWidget(self.tabs, stretch=1)

    def refresh_tasks(self, tasks: list):
        self.all_tasks = tasks
        self.filter_tasks()

    def filter_tasks(self):
        query = self.search_edit.text().strip().lower()
        if not query:
            self.filtered_tasks = self.all_tasks
        else:
            self.filtered_tasks = [t for t in self.all_tasks if query in t.get("task", "").lower()]

        self.task_combo.blockSignals(True)
        self.task_combo.clear()
        for i, t in enumerate(self.filtered_tasks):
            lbl = f"#{len(self.filtered_tasks)-i}  {t.get('task', 'Untitled')}"
            self.task_combo.addItem(lbl)
        self.task_combo.blockSignals(False)

        if self.filtered_tasks:
            self.task_combo.setCurrentIndex(0)
            self.display_selected_task()
        else:
            self.card_task_lbl.setText("No missions found.")
            self.card_time_lbl.setText("")
            self.plan_text.clear()
            self.final_text.clear()

    def display_selected_task(self):
        idx = self.task_combo.currentIndex()
        if not (0 <= idx < len(self.filtered_tasks)):
            return

        t = self.filtered_tasks[idx]
        self.current_task_dict = t
        self.card_task_lbl.setText(f"🎯 {t.get('task', 'Untitled Mission')}")
        self.card_time_lbl.setText(t.get('timestamp', ''))

        # 1. Gemini Plan
        self.plan_text.setPlainText(t.get("gemini_plan", "No plan recorded."))
        plan_img_path = self.find_screenshot("gemini_plan")
        if plan_img_path and os.path.exists(plan_img_path):
            pix = QPixmap(plan_img_path).scaled(300, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.plan_img.setPixmap(pix)
            self.plan_img.image_path = plan_img_path
            self.plan_img.show()
        else:
            self.plan_img.hide()

        # 2. Worker Outputs
        while self.workers_layout.count():
            item = self.workers_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        worker_outputs = t.get("worker_outputs", {})
        if not worker_outputs:
            no_w = QLabel("No worker outputs recorded.")
            no_w.setStyleSheet("color: #64748b; font-style: italic;")
            self.workers_layout.addWidget(no_w)
        else:
            for ag_name, out_text in worker_outputs.items():
                card = QFrame()
                card.setStyleSheet("background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 8px;")
                c_v = QVBoxLayout(card)
                c_v.addWidget(QLabel(f"<b>🔹 {ag_name.upper()} OUTPUT</b>"))

                split_w = QHBoxLayout()
                txt_w = QTextEdit()
                txt_w.setReadOnly(True)
                txt_w.setPlainText(out_text)
                txt_w.setFixedHeight(200)
                split_w.addWidget(txt_w, stretch=2)

                ss_path = self.find_screenshot(ag_name)
                if ss_path and os.path.exists(ss_path):
                    img_w = ClickableImageLabel(ss_path)
                    pix = QPixmap(ss_path).scaled(240, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    img_w.setPixmap(pix)
                    img_w.clicked.connect(self.open_lightbox)
                    split_w.addWidget(img_w, stretch=1)

                c_v.addLayout(split_w)
                self.workers_layout.addWidget(card)

        # 3. Final Approved Result
        self.final_text.setPlainText(t.get("final_output", "No final output recorded."))
        final_img_path = self.find_screenshot("gemini_final") or self.find_screenshot("gemini_review")
        if final_img_path and os.path.exists(final_img_path):
            pix = QPixmap(final_img_path).scaled(300, 220, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.final_img.setPixmap(pix)
            self.final_img.image_path = final_img_path
            self.final_img.show()
        else:
            self.final_img.hide()

        # 4. Live Rendered Deliverable Preview
        combined = t.get("final_output", "") + "\n" + "\n".join(t.get("worker_outputs", {}).values())
        matches = re.findall(r"```(?:html)?\s*(<!DOCTYPE html[\s\S]*?|<html[\s\S]*?)```", combined, re.IGNORECASE)
        if matches:
            self.current_html = matches[0]
            if HAS_WEBENGINE:
                self.live_web_view.setHtml(self.current_html)
            else:
                self.live_web_view.setHtml(self.current_html)
            self.btn_open_play.show()
        else:
            self.current_html = ""
            if HAS_WEBENGINE:
                self.live_web_view.setHtml(f"<div style='color:#cbd5e1;font-family:sans-serif;padding:20px;'>No full HTML website code detected in this mission outcome.</div>")
            else:
                self.live_web_view.setHtml("<div style='color:#cbd5e1;font-family:sans-serif;padding:20px;'>No full HTML website code detected in this mission outcome.</div>")
            self.btn_open_play.hide()

        # 5. Downloaded Assets
        while self.assets_layout.count():
            item = self.assets_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        slug = re.sub(r"[^\w\s-]", "", t.get("task", "")).strip().lower()
        slug = re.sub(r"[\s-]+", "_", slug)[:50]
        folder = os.path.join("downloads", slug)
        
        downloads = []
        if os.path.isdir(folder):
            downloads = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]

        if not downloads:
            no_a = QLabel("No assets auto-downloaded for this mission.")
            no_a.setStyleSheet("color: #64748b; font-style: italic; padding: 10px;")
            self.assets_layout.addWidget(no_a)
        else:
            for fpath in downloads:
                fname = os.path.basename(fpath)
                ext = os.path.splitext(fname)[1].lower()
                card = QFrame()
                card.setStyleSheet("background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 8px;")
                c_v = QVBoxLayout(card)
                c_v.addWidget(QLabel(f"📎 <code>downloads/{slug}/{fname}</code>"))
                if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                    img_lbl = ClickableImageLabel(fpath)
                    pix = QPixmap(fpath).scaled(350, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    img_lbl.setPixmap(pix)
                    img_lbl.clicked.connect(self.open_lightbox)
                    c_v.addWidget(img_lbl)
                self.assets_layout.addWidget(card)

    def find_screenshot(self, agent_id: str):
        for fname in [
            f"visuals/step_{agent_id}_fixed.png",
            f"visuals/step_{agent_id}.png",
            "visuals/step_gemini_plan.png",
            "visuals/step_gemini_review.png",
            "visuals/step_gemini_final.png",
        ]:
            if os.path.exists(fname):
                return fname
        return None

    def open_lightbox(self, image_path: str):
        dlg = LightboxDialog(image_path, self)
        dlg.exec()

    def on_open_in_playground(self):
        if getattr(self, "current_html", ""):
            self.open_in_playground_requested.emit(self.current_html)
