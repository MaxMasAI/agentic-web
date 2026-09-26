"""
gui/pages/file_explorer.py - Fast & Safe Project Folder & File Explorer
"""

import os
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QScrollArea, QFrame, QPlainTextEdit, QMessageBox,
    QApplication
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from gui.widgets.lightbox import LightboxDialog


class FileExplorerPage(QWidget):
    PROTECTED_GLOBAL = {"README.md", "readme.md", "streamlit.log", "run.log", "__init__.py"}
    PROTECTED_JSON = {"mcp_config.json", "agent_status.json", "memory.json", "subagents.json", "latency_config.json", "tracked_pids.json"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tab_widgets = {}
        self._loaded_tabs = set()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("📁 PROJECT FOLDER & FILE EXPLORER")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Direct Access, File Analytics, In-App Previews & Safe Directory Management")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Folder Tabs
        self.tabs = QTabWidget()
        self.folder_configs = [
            ("json", "📂 json/ (Configurations)"),
            ("tasks", "📂 tasks/ (Reports)"),
            ("logs", "📜 logs/ (Execution Logs)"),
            ("downloads", "⬇️ downloads/ (Assets)"),
            ("visuals", "🖼️ visuals/ (Screenshots)"),
            ("plugins", "🧩 plugins/ (Extensions)"),
        ]

        for folder_key, folder_label in self.folder_configs:
            tab_w = self.create_folder_tab(folder_key)
            self.tab_widgets[folder_key] = tab_w
            self.tabs.addTab(tab_w, folder_label)

        self.tabs.currentChanged.connect(self.on_tab_changed)
        main_layout.addWidget(self.tabs, stretch=1)

        # Lazy load only the first tab initially
        self.refresh_folder("json")
        self._loaded_tabs.add("json")

    def on_tab_changed(self, index: int):
        if 0 <= index < len(self.folder_configs):
            folder_key = self.folder_configs[index][0]
            self.refresh_folder(folder_key)
            self._loaded_tabs.add(folder_key)

    def create_folder_tab(self, folder_name: str):
        tab = QWidget()
        v_layout = QVBoxLayout(tab)
        v_layout.setContentsMargins(12, 12, 12, 12)
        v_layout.setSpacing(10)

        # Top Bar
        top_bar = QHBoxLayout()
        count_lbl = QLabel(f"<b>0 items</b> in `{folder_name}/`")
        count_lbl.setStyleSheet("font-size: 13px; color: #f8fafc;")
        top_bar.addWidget(count_lbl)
        top_bar.addStretch()

        if folder_name != "tests":
            purge_btn = QPushButton(f"🗑️ Delete All {folder_name}/ Files")
            purge_btn.setProperty("class", "danger-btn")
            purge_btn.clicked.connect(lambda _, f=folder_name: self.purge_folder(f))
            top_bar.addWidget(purge_btn)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setToolTip("Refresh Directory (F5 / Ctrl+R)")
        refresh_btn.clicked.connect(lambda _, f=folder_name: self.refresh_folder(f))
        top_bar.addWidget(refresh_btn)

        v_layout.addLayout(top_bar)

        # Scroll Area with File Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.setSpacing(8)
        scroll.setWidget(container)

        v_layout.addWidget(scroll, stretch=1)

        tab.count_lbl = count_lbl
        tab.cards_layout = c_layout
        return tab

    def refresh_folder(self, folder_name: str):
        tab = self.tab_widgets.get(folder_name)
        if not tab:
            return

        os.makedirs(folder_name, exist_ok=True)
        files = sorted(os.listdir(folder_name), reverse=True)

        while tab.cards_layout.count():
            item = tab.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        deletable_count = 0
        for f in files:
            if folder_name == "tests" or f in self.PROTECTED_GLOBAL:
                continue
            if folder_name == "json" and f in self.PROTECTED_JSON:
                continue
            deletable_count += 1

        tab.count_lbl.setText(f"<b>{len(files)} items</b> in `{folder_name}/` ({deletable_count} deletable)")

        if not files:
            empty_lbl = QLabel(f"No files currently in `{folder_name}/`.")
            empty_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 12px;")
            tab.cards_layout.addWidget(empty_lbl)
            return

        # Show up to 40 latest files for fast rendering
        for fname in files[:40]:
            fpath = os.path.join(folder_name, fname)
            if not os.path.isfile(fpath):
                continue

            size_kb = os.path.getsize(fpath) / 1024.0
            mod_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(fpath)))
            ext = os.path.splitext(fname)[1].lower()

            is_protected = (folder_name == "tests") or (fname in self.PROTECTED_GLOBAL) or (folder_name == "json" and fname in self.PROTECTED_JSON)

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #0f172a;
                    border: 1px solid rgba(255, 255, 255, 0.06);
                    border-radius: 8px;
                    padding: 8px;
                }
                QFrame:hover {
                    border-color: rgba(56, 189, 248, 0.35);
                    background: #131d33;
                }
            """)
            c_v = QVBoxLayout(card)
            c_v.setContentsMargins(8, 8, 8, 8)
            c_v.setSpacing(4)

            # Top File Row
            row = QHBoxLayout()
            name_lbl = QLabel(f"📄 <b>{fname}</b>")
            name_lbl.setStyleSheet("font-size: 13px; color: #f8fafc;")
            row.addWidget(name_lbl)

            badge_text = "PROTECTED" if is_protected else (ext.replace(".", "").upper() or "FILE")
            badge_col = "#38bdf8" if is_protected else "#818cf8"
            bg_col = "rgba(56, 189, 248, 0.15)" if is_protected else "rgba(129, 140, 248, 0.15)"
            border_col = "rgba(56, 189, 248, 0.35)" if is_protected else "rgba(129, 140, 248, 0.35)"
            badge = QLabel(badge_text)
            badge.setStyleSheet(f"background: {bg_col}; color: {badge_col}; border: 1px solid {border_col}; border-radius: 10px; padding: 2px 8px; font-size: 9px; font-weight: 800;")
            row.addWidget(badge)
            row.addStretch()

            meta_lbl = QLabel(f"{size_kb:.1f} KB  |  {mod_time}")
            meta_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-family: monospace;")
            row.addWidget(meta_lbl)

            copy_btn = QPushButton("🔗 Copy Path")
            copy_btn.setFixedHeight(24)
            copy_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
            copy_btn.clicked.connect(lambda _, p=fpath: QApplication.clipboard().setText(os.path.abspath(p)))
            row.addWidget(copy_btn)

            if not is_protected:
                del_btn = QPushButton("🗑️ Del")
                del_btn.setProperty("class", "danger-btn")
                del_btn.setFixedHeight(24)
                del_btn.setStyleSheet("font-size: 10px; padding: 2px 8px;")
                del_btn.clicked.connect(lambda _, p=fpath, fn=folder_name: self.delete_single_file(p, fn))
                row.addWidget(del_btn)

            c_v.addLayout(row)
            tab.cards_layout.addWidget(card)

    def delete_single_file(self, file_path: str, folder_name: str):
        try:
            os.remove(file_path)
            self.refresh_folder(folder_name)
        except Exception as e:
            QMessageBox.critical(self, "Deletion Error", f"Could not delete file: {e}")

    def purge_folder(self, folder_name: str):
        if not os.path.exists(folder_name):
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Purge",
            f"Are you sure you want to delete all non-protected files in '{folder_name}/'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        files = os.listdir(folder_name)
        deleted = 0
        for f in files:
            if folder_name == "tests" or f in self.PROTECTED_GLOBAL:
                continue
            if folder_name == "json" and f in self.PROTECTED_JSON:
                continue
            fp = os.path.join(folder_name, f)
            if os.path.isfile(fp):
                try:
                    os.remove(fp)
                    deleted += 1
                except Exception:
                    pass

        self.refresh_folder(folder_name)
        QMessageBox.information(self, "Purge Complete", f"Deleted {deleted} file(s) from '{folder_name}/'.")
