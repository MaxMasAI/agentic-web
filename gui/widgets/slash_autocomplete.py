"""
gui/widgets/slash_autocomplete.py - Sleek Interactive Slash Command Auto-Complete Engine
Provides IDE/Discord-style floating autocomplete popup for '/' commands, multi-agent routing,
and specialized automation instructions with keyboard navigation and instant insertion.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QWidget, QLineEdit, QTextEdit, QGraphicsDropShadowEffect, QApplication
)
from PySide6.QtCore import Qt, QPoint, QObject, QEvent, Signal, QRect
from PySide6.QtGui import QCursor, QFont, QColor, QKeyEvent

from core.agentlist import list_all_active_agents, get_lead_agent

# Standard Slash Commands, Workflows & Internal Tools
DEFAULT_SLASH_WORKFLOWS = [
    {"id": "all", "name": "all", "icon": "👥", "category": "Squad", "desc": "Dispatch task concurrently to all active specialists in roster"},
    {"id": "system", "name": "system", "icon": "⚡", "category": "Tool", "desc": "System OS · Host command line, apps & desktop automation"},
    {"id": "search", "name": "search", "icon": "🌐", "category": "Tool", "desc": "Real-time web search across DuckDuckGo, Google CSE, Bing"},
    {"id": "memory", "name": "memory", "icon": "🧠", "category": "Tool", "desc": "Neural memory search or record knowledge note"},
    {"id": "file", "name": "file", "icon": "📁", "category": "Tool", "desc": "Local filesystem I/O (read, write, list, search files)"},
    {"id": "wiki", "name": "wiki", "icon": "📚", "category": "Tool", "desc": "Instant Wikipedia factual knowledge & article lookup"},
    {"id": "mcp", "name": "mcp", "icon": "🔌", "category": "Tool", "desc": "Execute tool on active Model Context Protocol (MCP) server"},
    {"id": "harness", "name": "harness", "icon": "🧪", "category": "Tool", "desc": "Run MaxMasAI LAYA evaluation harness with plugins & CoT"},
    {"id": "tokens", "name": "tokens", "icon": "💎", "category": "Studio", "desc": "Real-time Token Manager & 1.019B free token metrics"},
    {"id": "canvas", "name": "canvas", "icon": "🌌", "category": "Studio", "desc": "Switch to Infinite Agent Canvas DAG Workflow Studio"},
    {"id": "vscode", "name": "vscode", "icon": "💻", "category": "Studio", "desc": "Switch to Monaco Code Studio & project explorer"},
    {"id": "notepad", "name": "notepad", "icon": "📝", "category": "Studio", "desc": "Switch to Scratchpad & notes workspace"},
    {"id": "painter", "name": "painter", "icon": "🎨", "category": "Studio", "desc": "Switch to AI Visual Sketch & Painter Studio"},
    {"id": "scheduler", "name": "scheduler", "icon": "🕒", "category": "Studio", "desc": "Switch to Automated Recurring Job Scheduler"},
    {"id": "goal", "name": "goal", "icon": "⏱️", "category": "Workflow", "desc": "Run until the specified goal is completely fulfilled"},
    {"id": "schedule", "name": "schedule", "icon": "📅", "category": "Workflow", "desc": "Run an instruction on a recurring schedule or timer"},
    {"id": "grill-me", "name": "grill-me", "icon": "💬", "category": "Workflow", "desc": "Interview me to align on a plan and resolve decisions"},
    {"id": "learn", "name": "learn", "icon": "💡", "category": "Workflow", "desc": "Reflect on recent successes or corrections to persist pattern"},
    {"id": "reset", "name": "reset", "icon": "🔄", "category": "System", "desc": "Reset all agent worker states back to FREE ready status"},
    {"id": "help", "name": "help", "icon": "❓", "category": "System", "desc": "View complete slash command routing guide & cheat sheet"},
]


def get_slash_catalogue():
    """Builds a dynamic catalogue of all active agents + system slash workflows."""
    catalogue = []
    
    # 1. Add "all" squad first
    catalogue.append(DEFAULT_SLASH_WORKFLOWS[0])
    
    # 2. Add all currently active roster agents
    try:
        agents = list_all_active_agents()
        for a in agents:
            aid = a.get("id", "")
            if aid and aid != "all":
                catalogue.append({
                    "id": aid,
                    "name": aid,
                    "icon": a.get("icon", "✦"),
                    "category": "Leader" if a.get("is_leader") else "Agent",
                    "desc": f"{a.get('name', aid)} · {a.get('role', 'Specialist')}"
                })
    except Exception:
        pass
        
    # 3. Add system workflows, tools & utility slash commands
    catalogue.extend(DEFAULT_SLASH_WORKFLOWS[1:])
    return catalogue


class SlashItemWidget(QWidget):
    """Custom rendering card for each autocomplete option in popup list."""
    def __init__(self, item_data: dict, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        # Icon
        self.icon_lbl = QLabel(item_data.get("icon", "✦"))
        self.icon_lbl.setStyleSheet("font-size: 15px; background: transparent;")
        self.icon_lbl.setFixedWidth(24)
        self.icon_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_lbl)

        # Name / Keyword
        self.name_lbl = QLabel(item_data.get("name", ""))
        self.name_lbl.setStyleSheet("font-size: 12.5px; font-weight: 800; color: #f8fafc; font-family: monospace;")
        layout.addWidget(self.name_lbl)

        # Category Badge
        cat = item_data.get("category", "")
        if cat:
            cat_lbl = QLabel(cat.upper())
            cat_color = "#38bdf8" if cat in ("Agent", "Leader") else "#10b981" if cat == "Squad" else "#a855f7" if cat in ("Workflow", "Studio") else "#f59e0b"
            cat_bg = "rgba(56, 189, 248, 0.15)" if cat in ("Agent", "Leader") else "rgba(16, 185, 129, 0.15)" if cat == "Squad" else "rgba(168, 85, 247, 0.15)" if cat in ("Workflow", "Studio") else "rgba(245, 158, 11, 0.15)"
            cat_border = "rgba(56, 189, 248, 0.35)" if cat in ("Agent", "Leader") else "rgba(16, 185, 129, 0.35)" if cat == "Squad" else "rgba(168, 85, 247, 0.35)" if cat in ("Workflow", "Studio") else "rgba(245, 158, 11, 0.35)"
            cat_lbl.setStyleSheet(f"""
                font-size: 9px;
                font-weight: 800;
                color: {cat_color};
                background: {cat_bg};
                border: 1px solid {cat_border};
                border-radius: 4px;
                padding: 1px 5px;
            """)
            layout.addWidget(cat_lbl)

        # Description
        self.desc_lbl = QLabel(item_data.get("desc", ""))
        self.desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent;")
        self.desc_lbl.setWordWrap(False)
        layout.addWidget(self.desc_lbl, stretch=1)


class SlashAutoCompletePopup(QFrame):
    """Floating auto-complete list popup anchored to an input box."""
    command_selected = Signal(str)

    def __init__(self, parent_input: QWidget):
        # Top-level frameless tool popup
        super().__init__(parent_input.window(), Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.parent_input = parent_input
        self.setObjectName("SlashAutoCompletePopup")
        self.setFixedWidth(540)
        self.setMaximumHeight(300)
        
        # Sci-Fi Glassmorphism Styling
        self.setStyleSheet("""
            QFrame#SlashAutoCompletePopup {
                background-color: #0b0f19;
                border: 1.5px solid #38bdf8;
                border-radius: 10px;
            }
            QListWidget {
                background: transparent;
                border: none;
                outline: none;
                padding: 4px;
            }
            QListWidget::item {
                border-radius: 6px;
                margin: 2px 0px;
                padding: 2px;
            }
            QListWidget::item:hover {
                background-color: rgba(56, 189, 248, 0.15);
            }
            QListWidget::item:selected {
                background-color: rgba(56, 189, 248, 0.28);
                border: 1px solid rgba(56, 189, 248, 0.6);
            }
            QScrollBar:vertical {
                background: #0f172a;
                width: 6px;
                border-radius: 3px;
                margin: 4px 2px 4px 0px;
            }
            QScrollBar::handle:vertical {
                background: #38bdf866;
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #38bdf8;
            }
        """)

        # Drop Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 200))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        # Header Hint
        hdr = QLabel("⚡ QUICK SLASH ROUTING, TOOLS & AGENTS (↑/↓ to navigate · Enter to select)")
        hdr.setStyleSheet("font-size: 9.5px; font-weight: 800; color: #38bdf8; padding: 4px 8px; letter-spacing: 0.5px;")
        layout.addWidget(hdr)

        self.list_widget = QListWidget(self)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.list_widget)

        self._current_filter = ""
        self._filtered_items = []

    def populate(self, query: str = ""):
        """Filters and loads items matching the query."""
        self._current_filter = query.lower().strip()
        self.list_widget.clear()
        self._filtered_items = []

        for item in get_slash_catalogue():
            name = item["name"].lower()
            desc = item["desc"].lower()
            cat = item["category"].lower()

            if not self._current_filter or self._current_filter in name or self._current_filter in desc or self._current_filter in cat:
                self._filtered_items.append(item)
                
                list_item = QListWidgetItem(self.list_widget)
                item_widget = SlashItemWidget(item)
                list_item.setSizeHint(item_widget.sizeHint())
                self.list_widget.addItem(list_item)
                self.list_widget.setItemWidget(list_item, item_widget)

        if self._filtered_items:
            self.list_widget.setCurrentRow(0)
            self._update_height()
            self._reposition()
            self.show()
            self.raise_()
        else:
            self.hide()

    def _update_height(self):
        count = self.list_widget.count()
        item_h = 38
        new_h = min(300, max(80, count * item_h + 36))
        self.setFixedHeight(new_h)

    def _reposition(self):
        """Calculates popup position above or below parent input box."""
        if not self.parent_input or not self.parent_input.isVisible():
            self.hide()
            return

        global_pos = self.parent_input.mapToGlobal(QPoint(0, 0))
        input_rect = QRect(global_pos, self.parent_input.size())
        screen = QApplication.screenAt(global_pos) or QApplication.primaryScreen()
        screen_geo = screen.availableGeometry()

        x = input_rect.left()
        if x + self.width() > screen_geo.right():
            x = max(screen_geo.left(), screen_geo.right() - self.width() - 10)

        # Place directly above input box if enough space, else below
        desired_h = self.height()
        space_above = input_rect.top() - screen_geo.top()
        space_below = screen_geo.bottom() - input_rect.bottom()

        if space_above >= desired_h + 8:
            y = input_rect.top() - desired_h - 6
        elif space_below >= desired_h + 8:
            y = input_rect.bottom() + 6
        else:
            y = max(screen_geo.top() + 10, input_rect.top() - desired_h - 4)

        self.move(x, y)

    def select_next(self):
        row = self.list_widget.currentRow()
        if row < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(row + 1)

    def select_prev(self):
        row = self.list_widget.currentRow()
        if row > 0:
            self.list_widget.setCurrentRow(row - 1)

    def confirm_selection(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._filtered_items):
            item = self._filtered_items[row]
            self._insert_completion(item)

    def _on_item_clicked(self, list_item):
        row = self.list_widget.row(list_item)
        if 0 <= row < len(self._filtered_items):
            item = self._filtered_items[row]
            self._insert_completion(item)

    def _insert_completion(self, item: dict):
        cmd_id = item["name"]
        cat = item.get("category", "")
        
        # Formatting rule: Agents / Squads get "/{name} - ", tools/studios get "/{name} "
        if cat in ("Agent", "Squad") and cmd_id not in ("reset", "help"):
            completion_text = f"/{cmd_id} - "
        else:
            completion_text = f"/{cmd_id} "

        if isinstance(self.parent_input, QLineEdit):
            text = self.parent_input.text()
            # Replace prefix slash portion
            if text.startswith("/"):
                # If typing after slash
                self.parent_input.setText(completion_text)
                self.parent_input.setCursorPosition(len(completion_text))
            else:
                self.parent_input.setText(completion_text + text)
                self.parent_input.setCursorPosition(len(completion_text))
        elif isinstance(self.parent_input, QTextEdit):
            self.parent_input.setText(completion_text)
            cursor = self.parent_input.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.parent_input.setTextCursor(cursor)

        self.hide()
        self.parent_input.setFocus()
        self.command_selected.emit(completion_text)


class SlashAutoCompleterFilter(QObject):
    """Event filter attached to QLineEdit or QTextEdit to intercept slash keystrokes."""
    def __init__(self, target_input: QWidget):
        super().__init__(target_input)
        self.target_input = target_input
        self.popup = SlashAutoCompletePopup(target_input)

        if isinstance(target_input, QLineEdit):
            target_input.textEdited.connect(self._on_text_edited)
        elif isinstance(target_input, QTextEdit):
            target_input.textChanged.connect(self._on_text_changed)

    def _get_current_text(self) -> str:
        if isinstance(self.target_input, QLineEdit):
            return self.target_input.text()
        elif isinstance(self.target_input, QTextEdit):
            return self.target_input.toPlainText()
        return ""

    def _on_text_edited(self, text: str):
        self._evaluate_text(text)

    def _on_text_changed(self):
        self._evaluate_text(self._get_current_text())

    def _evaluate_text(self, text: str):
        stripped = text.strip()
        if stripped.startswith("/"):
            # If user already typed " - " or completed the task body, hide popup
            if " - " in stripped or " : " in stripped:
                self.popup.hide()
                return

            query = stripped[1:]  # portion after '/'
            self.popup.populate(query)
        else:
            self.popup.hide()

    def eventFilter(self, obj, event: QEvent) -> bool:
        if obj == self.target_input and event.type() == QEvent.KeyPress:
            key_event: QKeyEvent = event
            key = key_event.key()

            if self.popup.isVisible():
                if key == Qt.Key_Down:
                    self.popup.select_next()
                    return True
                elif key == Qt.Key_Up:
                    self.popup.select_prev()
                    return True
                elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
                    # If selection is confirmed
                    self.popup.confirm_selection()
                    return True
                elif key == Qt.Key_Escape:
                    self.popup.hide()
                    return True

        if obj == self.target_input and event.type() in (QEvent.FocusOut, QEvent.Hide):
            # Defer hide slightly so clicking popup works
            pass

        return super().eventFilter(obj, event)


def attach_slash_autocomplete(input_widget: QWidget) -> SlashAutoCompleterFilter:
    """Convenience helper to attach slash autocomplete to any QLineEdit or QTextEdit."""
    filter_obj = SlashAutoCompleterFilter(input_widget)
    input_widget.installEventFilter(filter_obj)
    return filter_obj
