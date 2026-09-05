"""
gui/pages/neural_memory.py - Neural Memory Bank & Knowledge Vault
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QLineEdit, QTextEdit, QSlider, QCheckBox,
    QComboBox, QScrollArea, QFrame, QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal

from gui.widgets.metric_card import MetricCard
from utils.enhanced_memory import (
    load_memories, save_memories, add_memory_item,
    deduplicate_and_consolidate_memories, MEMORY_CATEGORIES
)


class NeuralMemoryPage(QWidget):
    memories_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_memories = []
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🧠 NEURAL MEMORY BANK")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Cross-Mission Semantic Knowledge Vault, Categorized Guidelines & System Directives")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Telemetry Cards
        self.telemetry_layout = QHBoxLayout()
        self.card_total = MetricCard("0", "Total Nodes", "#38bdf8")
        self.card_pinned = MetricCard("0", "Pinned Priority", "#fbbf24")
        self.card_arch = MetricCard("0", "Arch & Security", "#10b981")
        self.card_prefs = MetricCard("0", "User Directives", "#818cf8")

        for c in [self.card_total, self.card_pinned, self.card_arch, self.card_prefs]:
            self.telemetry_layout.addWidget(c)
        main_layout.addLayout(self.telemetry_layout)

        # Action Toolbar
        action_bar = QHBoxLayout()
        self.btn_dedup = QPushButton("✨ Deduplicate & Consolidate")
        self.btn_dedup.clicked.connect(self.on_deduplicate)
        action_bar.addWidget(self.btn_dedup)

        self.btn_export = QPushButton("📥 Export to RULES.md")
        self.btn_export.clicked.connect(self.on_export_rules)
        action_bar.addWidget(self.btn_export)

        self.btn_wipe = QPushButton("🗑️ Wipe Memory Vault")
        self.btn_wipe.setProperty("class", "danger-btn")
        self.btn_wipe.clicked.connect(self.on_wipe_vault)
        action_bar.addWidget(self.btn_wipe)

        action_bar.addStretch()
        main_layout.addLayout(action_bar)

        # Add New Memory Form GroupBox
        add_grp = QGroupBox("➕ Add New Categorized Knowledge Node")
        add_layout = QVBoxLayout(add_grp)
        add_layout.setSpacing(8)

        row1 = QHBoxLayout()
        v_txt = QVBoxLayout()
        v_txt.addWidget(QLabel("<b>Memory Learning / Directive:</b>"))
        self.new_mem_text = QTextEdit()
        self.new_mem_text.setPlaceholderText("e.g. Always use vanilla CSS with glassmorphism tokens; avoid standard alert popups...")
        self.new_mem_text.setFixedHeight(80)
        v_txt.addWidget(self.new_mem_text)
        row1.addLayout(v_txt, stretch=2)

        v_opts = QVBoxLayout()
        v_opts.addWidget(QLabel("<b>Category:</b>"))
        self.cat_combo = QComboBox()
        for k, v in MEMORY_CATEGORIES.items():
            self.cat_combo.addItem(v, k)
        v_opts.addWidget(self.cat_combo)

        row_imp = QHBoxLayout()
        row_imp.addWidget(QLabel("Importance:"))
        self.imp_slider = QSlider(Qt.Horizontal)
        self.imp_slider.setRange(1, 5)
        self.imp_slider.setValue(3)
        row_imp.addWidget(self.imp_slider)
        v_opts.addLayout(row_imp)

        self.pin_checkbox = QCheckBox("📌 Pin as High Priority")
        v_opts.addWidget(self.pin_checkbox)

        self.btn_save_node = QPushButton("💾 Save Knowledge Node to Vault")
        self.btn_save_node.setProperty("class", "primary-btn")
        self.btn_save_node.clicked.connect(self.on_save_memory_node)
        v_opts.addWidget(self.btn_save_node)

        row1.addLayout(v_opts, stretch=1)
        add_layout.addLayout(row1)
        main_layout.addWidget(add_grp)

        # Search Bar
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("🔍 Search Memory Knowledge Vault...")
        self.search_edit.textChanged.connect(self.render_memories_list)
        main_layout.addWidget(self.search_edit)

        # Category Filter Tabs
        self.cat_tabs = QTabWidget()
        self.cat_tabs.addTab(QWidget(), "🌐 All Memories")
        for k, v in MEMORY_CATEGORIES.items():
            self.cat_tabs.addTab(QWidget(), v)
        self.cat_tabs.currentChanged.connect(self.render_memories_list)
        main_layout.addWidget(self.cat_tabs)

        # Scroll Area for Memory Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(10)
        scroll.setWidget(self.cards_container)

        main_layout.addWidget(scroll, stretch=1)
        self.refresh_memories()

    def refresh_memories(self):
        self.all_memories = load_memories()

        pinned_count = sum(1 for m in self.all_memories if m.get("pinned", False))
        arch_count = sum(1 for m in self.all_memories if m.get("category") in ("architecture", "security_qa"))
        pref_count = sum(1 for m in self.all_memories if m.get("category") == "user_pref")

        self.card_total.set_value(str(len(self.all_memories)))
        self.card_pinned.set_value(str(pinned_count))
        self.card_arch.set_value(str(arch_count))
        self.card_prefs.set_value(str(pref_count))

        self.render_memories_list()

    def render_memories_list(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        tab_idx = self.cat_tabs.currentIndex()
        target_cat = None if tab_idx == 0 else list(MEMORY_CATEGORIES.keys())[tab_idx - 1]

        query = self.search_edit.text().strip().lower()

        filtered = [
            m for m in self.all_memories
            if (target_cat is None or m.get("category") == target_cat) and (not query or query in m.get("content", "").lower())
        ]

        if not filtered:
            no_lbl = QLabel("No knowledge nodes found.")
            no_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 12px;")
            self.cards_layout.addWidget(no_lbl)
            return

        for m in filtered:
            is_pinned = m.get("pinned", False)
            cat_name = MEMORY_CATEGORIES.get(m.get("category"), "🧠 General")
            stars = "⭐" * m.get("importance", 3)
            border_col = "#f59e0b" if is_pinned else "#38bdf8"

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: rgba(15, 23, 42, 0.7);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-left: 4px solid {border_col};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
            c_v = QVBoxLayout(card)
            c_v.setContentsMargins(8, 8, 8, 8)
            c_v.setSpacing(4)

            top_r = QHBoxLayout()
            meta_lbl = QLabel(f"<span style='font-size:11px;color:#94a3b8;font-family:monospace;'>{cat_name}  |  {stars}  |  <code>Accessed {m.get('access_count',1)}x</code></span>")
            top_r.addWidget(meta_lbl)
            top_r.addStretch()

            if is_pinned:
                badge = QLabel("📌 PINNED")
                badge.setStyleSheet("background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid #f59e0b88; border-radius: 10px; padding: 2px 8px; font-size: 9px; font-weight: 800;")
                top_r.addWidget(badge)

            pin_btn = QPushButton("📍 Unpin" if is_pinned else "📌 Pin")
            pin_btn.setFixedHeight(22)
            pin_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
            pin_btn.clicked.connect(lambda _, item_id=m["id"]: self.toggle_pin(item_id))
            top_r.addWidget(pin_btn)

            del_btn = QPushButton("🗑️ Del")
            del_btn.setProperty("class", "danger-btn")
            del_btn.setFixedHeight(22)
            del_btn.setStyleSheet("font-size: 10px; padding: 2px 6px;")
            del_btn.clicked.connect(lambda _, item_id=m["id"]: self.delete_memory(item_id))
            top_r.addWidget(del_btn)

            c_v.addLayout(top_r)

            content_lbl = QLabel(m.get("content", ""))
            content_lbl.setWordWrap(True)
            content_lbl.setStyleSheet("font-size: 12.5px; color: #f8fafc; line-height: 1.4;")
            c_v.addWidget(content_lbl)

            src_lbl = QLabel(f"Source: <i>{m.get('source_mission','Unknown')}</i> · {m.get('created_at','')}")
            src_lbl.setStyleSheet("font-size: 10px; color: #64748b;")
            c_v.addWidget(src_lbl)

            self.cards_layout.addWidget(card)

    def on_save_memory_node(self):
        text = self.new_mem_text.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Missing Content", "Please enter memory learning content.")
            return

        cat = self.cat_combo.currentData()
        imp = self.imp_slider.value()
        pin = self.pin_checkbox.isChecked()

        add_memory_item(text, category=cat, source_mission="Manual Direct Entry", importance=imp, pinned=pin)
        self.new_mem_text.clear()
        self.pin_checkbox.setChecked(False)
        self.refresh_memories()
        self.memories_updated.emit()
        QMessageBox.information(self, "Memory Saved", "Knowledge node successfully saved to vault!")

    def toggle_pin(self, mem_id: str):
        for m in self.all_memories:
            if m["id"] == mem_id:
                m["pinned"] = not m.get("pinned", False)
                break
        save_memories(self.all_memories)
        self.refresh_memories()
        self.memories_updated.emit()

    def delete_memory(self, mem_id: str):
        self.all_memories = [m for m in self.all_memories if m["id"] != mem_id]
        save_memories(self.all_memories)
        self.refresh_memories()
        self.memories_updated.emit()

    def on_deduplicate(self):
        removed = deduplicate_and_consolidate_memories()
        self.refresh_memories()
        self.memories_updated.emit()
        if removed > 0:
            QMessageBox.information(self, "Deduplication", f"Cleaned and consolidated {removed} redundant memory entries!")
        else:
            QMessageBox.information(self, "Deduplication", "Memory bank is already fully optimized.")

    def on_export_rules(self):
        lines = ["# Agentic System Rules & Persistent Learnings\n"]
        for m in self.all_memories:
            lines.append(f"- **[{MEMORY_CATEGORIES.get(m.get('category'), 'General')}]** {m['content']} *(Importance: {m.get('importance',3)}/5)*")
        with open("RULES.md", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        QMessageBox.information(self, "Exported", "Saved to RULES.md!")

    def on_wipe_vault(self):
        confirm = QMessageBox.question(
            self,
            "Confirm Wipe",
            "Are you sure you want to completely wipe the memory vault?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            save_memories([])
            self.refresh_memories()
            self.memories_updated.emit()
