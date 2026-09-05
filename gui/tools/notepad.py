"""
gui/tools/notepad.py - Smart Notepad, Day Notes & Calendar Scratchpad
"""

import os
import json
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QCalendarWidget, QLineEdit, QSplitter,
    QFrame, QMessageBox, QTabWidget
)
from PySide6.QtCore import Qt, QDate

NOTES_FILE = os.path.join("json", "day_notes.json")


class NotepadPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.day_notes = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("📝 SMART NOTEPAD & DAY NOTES")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Integrated Calendar Notes, Contextual Journal & Quick Scratchpad")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_day_notes_tab(), "📅 Calendar & Day Notes")
        self.tabs.addTab(self.create_scratchpad_tab(), "📝 General Scratchpad")

        main_layout.addWidget(self.tabs, stretch=1)
        self.load_notes()

    def create_day_notes_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Left: Calendar
        left_v = QVBoxLayout()
        left_v.addWidget(QLabel("<b>Select Calendar Date:</b>"))
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget {
                background-color: #0b0f19;
                color: #f8fafc;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: #cbd5e1;
                background-color: #090d16;
                selection-background-color: #38bdf8;
                selection-color: #080b11;
            }
        """)
        self.calendar.selectionChanged.connect(self.on_date_selected)
        left_v.addWidget(self.calendar)
        layout.addLayout(left_v, stretch=1)

        # Right: Note Editor for selected date
        right_v = QVBoxLayout()
        self.date_label = QLabel(f"<b>Notes for:</b> {QDate.currentDate().toString('yyyy-MM-dd')}")
        self.date_label.setStyleSheet("font-size: 14px; color: #38bdf8;")
        right_v.addWidget(self.date_label)

        self.day_note_edit = QTextEdit()
        self.day_note_edit.setPlaceholderText("Write notes, journal entries, or mission goals for this date...")
        self.day_note_edit.textChanged.connect(self.auto_save_day_note)
        right_v.addWidget(self.day_note_edit, stretch=1)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾 Save Day Note")
        btn_save.setProperty("class", "primary-btn")
        btn_save.clicked.connect(self.save_notes)
        btn_row.addWidget(btn_save)

        btn_clear = QPushButton("🗑️ Clear Note")
        btn_clear.clicked.connect(self.clear_day_note)
        btn_row.addWidget(btn_clear)

        right_v.addLayout(btn_row)
        layout.addLayout(right_v, stretch=2)

        return tab

    def create_scratchpad_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.scratchpad_edit = QTextEdit()
        self.scratchpad_edit.setPlaceholderText("Quick unstructured notes, code snippets, prompt drafts...")
        self.scratchpad_edit.textChanged.connect(self.auto_save_day_note)
        layout.addWidget(self.scratchpad_edit, stretch=1)

        btn_export = QPushButton("📥 Export Scratchpad to NOTEPAD.md")
        btn_export.clicked.connect(self.export_scratchpad)
        layout.addWidget(btn_export)

        return tab

    def on_date_selected(self):
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.date_label.setText(f"<b>Notes for:</b> {date_str}")
        self.day_note_edit.blockSignals(True)
        self.day_note_edit.setPlainText(self.day_notes.get(date_str, ""))
        self.day_note_edit.blockSignals(False)

    def auto_save_day_note(self):
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.day_notes[date_str] = self.day_note_edit.toPlainText()
        self.day_notes["__scratchpad__"] = self.scratchpad_edit.toPlainText()

    def clear_day_note(self):
        date_str = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.day_notes[date_str] = ""
        self.day_note_edit.clear()
        self.save_notes()

    def load_notes(self):
        if os.path.exists(NOTES_FILE):
            try:
                with open(NOTES_FILE, "r", encoding="utf-8") as f:
                    self.day_notes = json.load(f)
            except Exception:
                self.day_notes = {}
        self.on_date_selected()
        self.scratchpad_edit.setPlainText(self.day_notes.get("__scratchpad__", ""))

    def save_notes(self):
        os.makedirs("json", exist_ok=True)
        self.auto_save_day_note()
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            json.dump(self.day_notes, f, indent=2)
        QMessageBox.information(self, "Saved", "Notes saved successfully!")

    def export_scratchpad(self):
        with open("NOTEPAD.md", "w", encoding="utf-8") as f:
            f.write("# Notepad Scratchpad\n\n" + self.scratchpad_edit.toPlainText())
        QMessageBox.information(self, "Exported", "Saved to NOTEPAD.md!")
