"""
gui/widgets/sidebar.py - Modern Categorized Dark Theme Sidebar (ModernSidebar)
Conforms strictly to design_system_ui_theme_documentation.md
"""

from typing import Dict, List, Tuple, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSizePolicy, QScrollArea, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QTimer, Property
from PySide6.QtGui import QCursor


class CollapsibleSection(QWidget):
    """Collapsible Dropdown Section styled with design system tokens."""
    def __init__(self, title: str, start_collapsed: bool = False, parent=None):
        super().__init__(parent)
        self.raw_title = str(title).upper()
        self.is_collapsed = start_collapsed

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(2)

        # Header Group Button / Label
        self.header_btn = QPushButton()
        self.header_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.header_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.header_btn.setFixedHeight(28)
        self.header_btn.setProperty("class", "sidebar-group-label")
        self.header_btn.clicked.connect(self.toggle_collapse)
        self.main_layout.addWidget(self.header_btn)

        # Content Container for Child Buttons
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 2)
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


class ModernSidebar(QFrame):
    """
    Modern Dark Theme Navigation Sidebar for Autonomous Multi-Agent OS.
    Implements Design System Token Architecture, nav-button, and group-label patterns.
    """
    page_changed = Signal(str)
    abort_requested = Signal(str)

    EXPANDED_WIDTH = 250
    COLLAPSED_WIDTH = 58

    NAV_SECTIONS = [
        ("OPERATIONS", [
            ("home", "🛰️", "Mission Control"),
            ("launch", "⚡", "Task Dispatcher"),
            ("subagents", "🤖", "Agent Squads"),
            ("history", "📋", "Mission Archive"),
        ]),
        ("ASSISTANT MODES", [
            ("chat", "💬", "Universal Chat"),
            ("chat_files", "📄", "Chat with Files (RAG)"),
            ("research", "🔍", "Deep Research"),
            ("media_studio", "🎨", "Image & Video Studio"),
        ]),
        ("CREATIVE & TOOLS", [
            ("vscode", "💻", "VS Code Studio"),
            ("canvas_dev", "🌌", "Agent Canvas IDE"),
            ("playground", "🎮", "Playground Studio"),
            ("harness", "⚡", "MaxMasAI Harness (Dev)"),
            ("agent_builder", "🧩", "Node Agent Builder"),
            ("painter", "🖌️", "Painter Canvas"),
            ("notepad", "📝", "Smart Notepad"),
            ("scheduler", "⏰", "Task Scheduler"),
        ]),
        ("SYSTEM & MCP", [
            ("tokens", "💎", "Token Manager"),
            ("mcp", "🔌", "MCP Service Hub"),
            ("memory", "🧠", "Neural Memory"),
            ("explorer", "📁", "Folder Explorer"),
        ]),
        ("SETTINGS", [
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
        "tokens": "Ctrl+Shift+T / Alt+T",
    }

    @classmethod
    def get_tooltip(cls, key: str, icon: str, label: str) -> str:
        hk = cls.HOTKEY_MAP.get(key)
        if hk:
            return f"{icon}  {label}  ({hk})"
        return f"{icon}  {label}"

    def __init__(self, on_navigate_callback=None, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarContainer")
        self.active_page = "home"
        self.on_navigate_callback = on_navigate_callback
        if on_navigate_callback:
            self.page_changed.connect(on_navigate_callback)

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
        self.anim.setDuration(200)
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

        # 1. Scrollable Action List (Header Box Removed)
        self.scroll = QScrollArea()
        self.scroll.setObjectName("sidebarScrollArea")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(4, 6, 4, 6)
        self.layout.setSpacing(2)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        # Active Missions Container
        self.active_missions_frame = QFrame()
        self.active_missions_frame.setProperty("class", "card")
        self.active_missions_layout = QVBoxLayout(self.active_missions_frame)
        self.active_missions_layout.setContentsMargins(4, 4, 4, 4)
        self.active_missions_frame.hide()

        # ── Dropdown Accordion Sections ──
        for section_title, items in self.NAV_SECTIONS:
            should_start_collapsed = "SYSTEM" in section_title or "SETTINGS" in section_title
            section_widget = CollapsibleSection(section_title, start_collapsed=should_start_collapsed)
            self.layout.addWidget(section_widget)
            self.sections.append(section_widget)

            for key, icon, label in items:
                btn = QPushButton(f"{icon}  {label}")
                btn.setProperty("class", "nav-button")
                btn.setCheckable(True)
                btn.setCursor(QCursor(Qt.PointingHandCursor))
                btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                btn.setFixedHeight(34)
                btn.setToolTip(self.get_tooltip(key, icon, label))
                btn.clicked.connect(lambda checked=False, k=key: self.on_button_clicked(k))
                
                self.btn_group.addButton(btn)
                self.buttons[key] = (btn, icon, label, section_widget)
                section_widget.add_widget(btn)

            if "OPERATIONS" in section_title:
                self.layout.addWidget(self.active_missions_frame)
                self.layout.addSpacing(4)

        self.layout.addStretch()

        # Footer Status
        self.footer_lbl = QLabel("0 Tasks · 0 Mems")
        self.footer_lbl.setProperty("class", "metric-label")
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
        if hasattr(self, "pin_btn") and self.pin_btn:
            if self.auto_hide:
                self.pin_btn.setText("✨")
                self.pin_btn.setToolTip("Auto-Hide Active (Hover to Expand) (Ctrl+B)")
                self.pin_btn.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #64748B;")
            else:
                self.pin_btn.setText("📌")
                self.pin_btn.setToolTip("Sidebar Pinned Open (Ctrl+B)")
                self.pin_btn.setStyleSheet("background: transparent; border: none; font-size: 11px; color: #38BDF8;")
        if self.auto_hide:
            self._do_collapse()
        else:
            self.collapse_timer.stop()
            self._do_expand()

    def _do_expand(self):
        self.is_expanded = True
        self.anim.stop()
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(self.EXPANDED_WIDTH)
        self.anim.start()

    def _do_collapse(self):
        self.is_expanded = False
        self.anim.stop()
        self.anim.setStartValue(self.width())
        self.anim.setEndValue(self.COLLAPSED_WIDTH)
        self.anim.start()

    def set_collapsed_state(self, collapsed: bool):
        if hasattr(self, "title_lbl") and self.title_lbl:
            self.title_lbl.setVisible(not collapsed)
        if hasattr(self, "status_lbl") and self.status_lbl:
            self.status_lbl.setVisible(not collapsed)
        if hasattr(self, "pin_btn") and self.pin_btn:
            self.pin_btn.setVisible(not collapsed)
        if hasattr(self, "footer_lbl") and self.footer_lbl:
            self.footer_lbl.setVisible(not collapsed)

        for sec in self.sections:
            sec.update_header_text(is_sidebar_compact=collapsed)

        for key, (btn, icon, label, sec) in self.buttons.items():
            if collapsed:
                btn.setText(icon)
                btn.setToolTip(f"{label} ({icon})")
            else:
                btn.setText(f"{icon}  {label}")
                btn.setToolTip(self.get_tooltip(key, icon, label))

    def on_button_clicked(self, key: str):
        self.active_page = key
        self.update_button_states()
        self.page_changed.emit(key)

    def update_button_states(self):
        for key, (btn, icon, label, sec) in self.buttons.items():
            is_active = (key == self.active_page) or (self.active_page.startswith("settings_") and key == self.active_page)
            btn.setChecked(is_active)
            if is_active and sec:
                sec.expand()

    def set_active_page(self, key: str, emit_signal: bool = False):
        self.active_page = key
        self.update_button_states()
        if emit_signal:
            self.page_changed.emit(key)

    def set_active(self, key: str, emit_signal: bool = False):
        self.set_active_page(key, emit_signal=emit_signal)

    def update_footer_stats(self, tasks_done: int, total_memories: int):
        self.footer_lbl.setText(f"{tasks_done} Done · {total_memories} Mems")

    def update_stats(self, tasks_done: int, total_memories: int, skills_count: int = 0):
        if skills_count > 0:
            self.footer_lbl.setText(f"{tasks_done} Done · {total_memories} Mem · {skills_count} Skills")
        else:
            self.footer_lbl.setText(f"{tasks_done} Done · {total_memories} Mems")

    def update_active_missions(self, procs_dict: dict):
        self.update_active_processes(procs_dict)

    def update_active_processes(self, procs_dict: dict):
        current_keys = set(procs_dict.keys())
        if current_keys == self._last_active_procs_keys:
            return
        self._last_active_procs_keys = current_keys

        while self.active_missions_layout.count():
            item = self.active_missions_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not procs_dict:
            self.active_missions_frame.hide()
            return

        self.active_missions_frame.show()
        lbl_head = QLabel("⚡ ACTIVE RUNS")
        lbl_head.setProperty("class", "sidebar-group-label")
        self.active_missions_layout.addWidget(lbl_head)

        for mid, info in procs_dict.items():
            row = QHBoxLayout()
            row.setContentsMargins(2, 2, 2, 2)
            row.setSpacing(4)

            name_lbl = QLabel(f"● {info.get('title', mid)[:14]}")
            name_lbl.setProperty("class", "badge-busy")
            row.addWidget(name_lbl, stretch=1)

            btn_kill = QPushButton("✕")
            btn_kill.setFixedSize(18, 18)
            btn_kill.setProperty("class", "btn-secondary")
            btn_kill.setCursor(QCursor(Qt.PointingHandCursor))
            btn_kill.clicked.connect(lambda _, m=mid: self.abort_requested.emit(m))
            row.addWidget(btn_kill)

            self.active_missions_layout.addLayout(row)


# Alias for backward compatibility
Sidebar = ModernSidebar
