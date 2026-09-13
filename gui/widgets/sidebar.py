"""
gui/widgets/sidebar.py - Modern Categorized Sci-Fi Sidebar with Dropdown Settings & Accordion Sections
Supports full collapsible dropdown settings menu, fluid auto-hide, and keyboard shortcuts.
"""

from typing import Dict, List, Tuple, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, Property
from PySide6.QtGui import QCursor


class CollapsibleSection(QWidget):
    """Collapsible Dropdown Accordion Section with animated toggle."""
    def __init__(self, title: str, start_collapsed: bool = False, parent=None):
        super().__init__(parent)
        self.raw_title = title
        self.is_collapsed = start_collapsed

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        # Dropdown Header Button
        self.header_btn = QPushButton()
        self.header_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.header_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.header_btn.setFixedHeight(28)
        self.header_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #7dd3fc;
                border: none;
                text-align: left;
                padding-left: 6px;
                padding-right: 6px;
                font-size: 10.5px;
                font-weight: 800;
                letter-spacing: 0.8px;
            }
            QPushButton:hover {
                color: #38bdf8;
                background-color: rgba(56, 189, 248, 0.08);
                border-radius: 4px;
            }
        """)
        self.header_btn.clicked.connect(self.toggle_collapse)
        self.main_layout.addWidget(self.header_btn)

        # Content Container for Child Buttons
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 4)
        self.content_layout.setSpacing(2)
        self.main_layout.addWidget(self.content_widget)

        if start_collapsed:
            self.content_widget.hide()

        self.update_header_text()

    def add_widget(self, widget: QWidget):
        self.content_layout.addWidget(widget)

    def update_header_text(self, is_sidebar_compact: bool = False):
        if is_sidebar_compact:
            icon = self.raw_title.split()[0] if self.raw_title else "📁"
            self.header_btn.setText(icon)
        else:
            arrow = "▸" if self.is_collapsed else "▾"
            self.header_btn.setText(f"{self.raw_title}  {arrow}")

    def toggle_collapse(self):
        self.set_collapsed(not self.is_collapsed)

    def set_collapsed(self, collapsed: bool):
        self.is_collapsed = collapsed
        self.content_widget.setVisible(not collapsed)
        self.update_header_text()

    def expand(self):
        if self.is_collapsed:
            self.set_collapsed(False)


class Sidebar(QWidget):
    page_changed = Signal(str)
    abort_requested = Signal(str)

    EXPANDED_WIDTH = 240
    COLLAPSED_WIDTH = 58

    NAV_SECTIONS = [
        ("🚀 OPERATIONS", [
            ("home", "🛰️", "Mission Control"),
            ("launch", "🚀", "Task Dispatch"),
            ("subagents", "🤖", "Agent Squads"),
            ("history", "📋", "Mission Archive"),
        ]),
        ("💬 ASSISTANT MODES", [
            ("chat", "💬", "Universal Chat"),
            ("chat_files", "📄", "Chat with Files (RAG)"),
            ("research", "🔍", "Deep Research"),
            ("media_studio", "🎨", "Image & Video Studio"),
        ]),
        ("🛠️ CREATIVE & TOOLS", [
            ("vscode", "💻", "VS Code Studio"),
            ("canvas_dev", "🌌", "Agent Canvas IDE"),
            ("playground", "🎮", "Playground Studio"),
            ("agent_builder", "🧩", "Node Agent Builder"),
            ("painter", "🖌️", "Painter Canvas"),
            ("notepad", "📝", "Smart Notepad"),
            ("scheduler", "⏰", "Task Scheduler"),
        ]),
        ("🔌 SYSTEM", [
            ("mcp", "🔌", "MCP Service Hub"),
            ("memory", "🧠", "Neural Memory"),
            ("explorer", "📁", "Folder Explorer"),
        ]),
        ("⚙️ SETTINGS", [
            ("settings_general", "🌐", "General"),
            ("settings_api_keys", "🔑", "API Keys"),
            ("settings_layout", "🎨", "Layout"),
            ("settings_files", "📁", "Files & attachments"),
            ("settings_context", "🧠", "Context"),
            ("settings_remote_tools", "🛠️", "Remote tools"),
            ("settings_models", "🤖", "Models"),
            ("settings_prompts", "📝", "Prompts"),
            ("settings_images_video", "🖼️", "Images & video"),
            ("settings_vision_camera", "👁️", "Vision & camera"),
            ("settings_audio", "🔊", "Audio"),
            ("settings_indexes", "📚", "Indexes / LlamaIndex"),
            ("settings_agents", "👥", "Agents & experts"),
            ("settings_accessibility", "♿", "Accessibility"),
            ("settings_security", "🔒", "Security"),
            ("settings_personalize", "✨", "Personalize"),
            ("settings_updates", "🔄", "Updates"),
            ("settings_debug", "🐞", "Debug"),
            ("settings_about", "ℹ️", "About"),
        ])
    ]

    HOTKEY_MAP = {
        "home": "Alt+H",
        "launch": "Alt+D",
        "canvas_dev": "Ctrl+K / Alt+C",
        "playground": "Alt+P",
        "chat": "Alt+U",
        "explorer": "Ctrl+E / Alt+E",
        "subagents": "Alt+S",
        "research": "Alt+R",
        "media_studio": "Alt+M",
        "settings_general": "Ctrl+,",
        "chat_files": "Ctrl+Shift+F",
        "mcp": "Ctrl+Shift+M",
        "memory": "Ctrl+Shift+N",
    }

    @classmethod
    def get_tooltip(cls, key: str, icon: str, label: str) -> str:
        hk = cls.HOTKEY_MAP.get(key)
        if hk:
            return f"{icon}  {label}  ({hk})"
        return f"{icon}  {label}"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")
        self.active_page = "home"
        self.buttons: Dict[str, Tuple[QPushButton, str, str, Optional[CollapsibleSection]]] = {}
        self.sections: List[CollapsibleSection] = []
        self._last_active_procs_keys = None

        # Auto-Hide and Visual State
        self.auto_hide = True
        self.is_expanded = False
        self._is_visually_collapsed = True

        # Initial collapsed width
        self.setFixedWidth(self.COLLAPSED_WIDTH)

        # Collapse Timer to prevent jittery leave triggers
        self.collapse_timer = QTimer(self)
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.setInterval(200)
        self.collapse_timer.timeout.connect(self._do_collapse)

        # Fluid Sliding Property Animation
        self.anim = QPropertyAnimation(self, b"sidebar_width")
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.init_ui()
        self.set_collapsed_state(True)

    # ── Animated Property for Smooth Width Interpolation ──
    def get_sidebar_width(self) -> int:
        return self.width()

    def set_sidebar_width(self, w: int):
        self.setFixedWidth(w)
        if w < 130 and not self._is_visually_collapsed:
            self._is_visually_collapsed = True
            self.set_collapsed_state(True)
        elif w >= 130 and self._is_visually_collapsed:
            self._is_visually_collapsed = False
            self.set_collapsed_state(False)

    sidebar_width = Property(int, get_sidebar_width, set_sidebar_width)

    def init_ui(self):
        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("border: none; background: transparent;")

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(6, 10, 6, 10)
        self.layout.setSpacing(4)

        # Brand Box Header
        self.brand_frame = QFrame()
        self.brand_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        brand_vbox = QVBoxLayout(self.brand_frame)
        brand_vbox.setContentsMargins(4, 4, 4, 4)
        brand_vbox.setSpacing(2)

        top_brand = QHBoxLayout()
        top_brand.setContentsMargins(0, 0, 0, 0)
        top_brand.setSpacing(6)

        self.logo_btn = QPushButton("⚡")
        self.logo_btn.setFixedSize(36, 32)
        self.logo_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.logo_btn.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.15);
                border: 1px solid rgba(56, 189, 248, 0.3);
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.3);
            }
        """)
        self.logo_btn.setToolTip("Toggle Pin / Auto-Hide Sidebar (Ctrl+B)")
        self.logo_btn.clicked.connect(self.toggle_pin)
        top_brand.addWidget(self.logo_btn)

        self.title_lbl = QLabel("AGENT CONSOLE")
        self.title_lbl.setStyleSheet("font-weight: 800; font-size: 12.5px; color: #38bdf8; letter-spacing: 0.8px;")
        top_brand.addWidget(self.title_lbl)

        self.pin_btn = QPushButton("✨")
        self.pin_btn.setFixedSize(24, 24)
        self.pin_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.pin_btn.setToolTip("Auto-Hide Active (Click to Pin Open) (Ctrl+B)")
        self.pin_btn.setStyleSheet("background: transparent; border: none; font-size: 12px; color: #38bdf8;")
        self.pin_btn.clicked.connect(self.toggle_pin)
        top_brand.addWidget(self.pin_btn)

        brand_vbox.addLayout(top_brand)

        self.status_lbl = QLabel("● SYSTEM ONLINE")
        self.status_lbl.setStyleSheet("font-size: 9px; font-weight: 700; color: #10b981; margin-left: 6px; letter-spacing: 0.5px;")
        brand_vbox.addWidget(self.status_lbl)

        self.layout.addWidget(self.brand_frame)
        self.layout.addSpacing(4)

        # Active Missions Container
        self.active_missions_frame = QFrame()
        self.active_missions_frame.setStyleSheet("""
            QFrame {
                background: rgba(245, 158, 11, 0.08);
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        self.active_missions_layout = QVBoxLayout(self.active_missions_frame)
        self.active_missions_layout.setContentsMargins(4, 4, 4, 4)
        self.active_missions_frame.hide()

        # ── Dropdown Accordion Sections ──
        for section_title, items in self.NAV_SECTIONS:
            # Default close/collapse bottom two sections (SYSTEM and SETTINGS)
            should_start_collapsed = "SYSTEM" in section_title or "SETTINGS" in section_title
            section_widget = CollapsibleSection(section_title, start_collapsed=should_start_collapsed)
            self.layout.addWidget(section_widget)
            self.sections.append(section_widget)

            for key, icon, label in items:
                btn = QPushButton(f"  {icon}  {label}")
                btn.setProperty("class", "nav-btn")
                btn.setCheckable(True)
                btn.setCursor(QCursor(Qt.PointingHandCursor))
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.setFixedHeight(32)
                btn.setToolTip(self.get_tooltip(key, icon, label))
                btn.clicked.connect(lambda checked=False, k=key: self.on_button_clicked(k))
                self.buttons[key] = (btn, icon, label, section_widget)
                section_widget.add_widget(btn)

            if "OPERATIONS" in section_title:
                self.layout.addWidget(self.active_missions_frame)
                self.layout.addSpacing(6)

        self.layout.addStretch()

        # Footer Stats Frame
        self.footer_lbl = QLabel("0 Tasks · 0 Mems")
        self.footer_lbl.setStyleSheet("font-size: 9.5px; color: #64748b; padding-top: 4px; border-top: 1px solid rgba(255, 255, 255, 0.08);")
        self.footer_lbl.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.footer_lbl)

        self.scroll.setWidget(self.container)
        main_vbox.addWidget(self.scroll)

        self.update_button_states()

    def enterEvent(self, event):
        """Mouse hovered onto sidebar -> smoothly slide open if auto_hide is active."""
        if self.auto_hide and not self.is_expanded:
            self.collapse_timer.stop()
            self._do_expand()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse left sidebar -> smoothly slide collapse."""
        if self.auto_hide and self.is_expanded:
            self.collapse_timer.start()
        super().leaveEvent(event)

    def toggle_pin(self):
        """Toggles between Auto-Hide mode and Pinned Open mode."""
        self.auto_hide = not self.auto_hide
        if self.auto_hide:
            self.pin_btn.setText("✨")
            self.pin_btn.setToolTip("Auto-Hide Active (Hover to Expand) (Ctrl+B)")
            self.pin_btn.setStyleSheet("background: transparent; border: none; font-size: 12px; color: #38bdf8;")
            self._do_collapse()
        else:
            self.pin_btn.setText("📌")
            self.pin_btn.setToolTip("Sidebar Pinned Open (Click to Auto-Hide) (Ctrl+B)")
            self.pin_btn.setStyleSheet("background: transparent; border: none; font-size: 12px; color: #10b981; font-weight: bold;")
            self._do_expand()

    def _do_expand(self):
        self.is_expanded = True
        self.anim.stop()
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(self.EXPANDED_WIDTH)
        self.anim.start()

    def _do_collapse(self):
        if not self.auto_hide:
            return
        self.is_expanded = False
        self.anim.stop()
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(self.COLLAPSED_WIDTH)
        self.anim.start()

    def set_collapsed_state(self, collapsed: bool):
        """Updates text visibility and button labels for compact or expanded state."""
        self.title_lbl.setVisible(not collapsed)
        self.pin_btn.setVisible(not collapsed)
        self.status_lbl.setVisible(not collapsed)
        self.footer_lbl.setVisible(not collapsed)

        for sec in self.sections:
            sec.update_header_text(is_sidebar_compact=collapsed)
            if collapsed:
                sec.content_widget.setVisible(True)
            else:
                sec.content_widget.setVisible(not sec.is_collapsed)

        for key, (btn, icon, label, sec) in self.buttons.items():
            tip = self.get_tooltip(key, icon, label)
            if collapsed:
                btn.setText(icon)
                btn.setToolTip(tip)
            else:
                btn.setText(f"  {icon}  {label}")
                btn.setToolTip(tip)

    def on_button_clicked(self, page_key: str):
        if page_key in self.buttons:
            btn, icon, label, sec = self.buttons[page_key]
            if sec:
                sec.expand()
            if page_key != self.active_page:
                self.active_page = page_key
                self.update_button_states()
                self.page_changed.emit(page_key)
                if self.auto_hide:
                    self.collapse_timer.start(100)

    def set_active_page(self, page_key: str, emit_signal: bool = False):
        if page_key in self.buttons:
            btn, icon, label, sec = self.buttons[page_key]
            if sec:
                sec.expand()
            if self.active_page != page_key:
                self.active_page = page_key
                self.update_button_states()
                if emit_signal:
                    self.page_changed.emit(page_key)

    def update_button_states(self):
        for key, (btn, icon, label, sec) in self.buttons.items():
            is_active = (key == self.active_page)
            btn.setChecked(is_active)
            if is_active:
                btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(56, 189, 248, 0.25), stop:1 rgba(14, 165, 233, 0.1));
                        color: #38bdf8;
                        border: 1px solid rgba(56, 189, 248, 0.6);
                        font-weight: 700;
                        border-radius: 7px;
                        text-align: left;
                        font-size: 12px;
                        padding-left: 8px;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #94a3b8;
                        border: 1px solid transparent;
                        border-radius: 7px;
                        text-align: left;
                        font-size: 12px;
                        padding-left: 8px;
                    }
                    QPushButton:hover {
                        background-color: rgba(56, 189, 248, 0.08);
                        color: #f1f5f9;
                        border-color: rgba(56, 189, 248, 0.2);
                    }
                """)

    def update_stats(self, tasks_count: int, memory_count: int, skills_count: int):
        new_text = f"<b>{tasks_count}</b> Tasks · <b>{memory_count}</b> Mems"
        if self.footer_lbl.text() != new_text:
            self.footer_lbl.setText(new_text)

    def update_active_missions(self, running_procs: dict):
        active = {k: v for k, v in running_procs.items() if v.get("status") == "running"}
        active_keys = tuple(sorted(active.keys()))
        
        if self._last_active_procs_keys == active_keys:
            return
        self._last_active_procs_keys = active_keys

        while self.active_missions_layout.count():
            item = self.active_missions_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
            l = item.layout()
            if l:
                while l.count():
                    sub = l.takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        if active:
            self.active_missions_frame.show()
            title = QLabel(f"⚡ LIVE ({len(active)})")
            title.setStyleSheet("font-size: 10px; font-weight: 800; color: #fbbf24; margin-bottom: 2px;")
            self.active_missions_layout.addWidget(title)

            for label, info in active.items():
                lbl_row = QHBoxLayout()
                m_lbl = QLabel(f"● {label[:10]}")
                m_lbl.setStyleSheet("font-size: 10px; color: #fde68a;")
                
                abort_btn = QPushButton("⏹")
                abort_btn.setProperty("class", "danger-btn")
                abort_btn.setFixedSize(20, 20)
                abort_btn.setToolTip(f"Abort {label}")
                abort_btn.setStyleSheet("font-size: 9px; padding: 0px; border-radius: 4px; background: #dc2626; color: white;")
                abort_btn.clicked.connect(lambda _, l=label: self.abort_requested.emit(l))
                
                lbl_row.addWidget(m_lbl)
                lbl_row.addWidget(abort_btn)
                self.active_missions_layout.addLayout(lbl_row)
        else:
            self.active_missions_frame.hide()
