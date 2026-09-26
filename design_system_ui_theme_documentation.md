# Autonomous Multi-Agent OS — Modern Dark Theme Specification

This specification transforms the high-saturation, multi-color UI into a cohesive, high-performance, dark-mode design system tailored for PySide6 desktop applications.

---

## 1. Design Token Architecture

### 1.1 Color Palette

| Token Role | Hex Code | Purpose & Usage |
| :--- | :--- | :--- |
| **Canvas Background** | `#0B0D11` | Primary window surface, main background |
| **Sidebar Surface** | `#0E1117` | Navigation panel and drawer background |
| **Card Surface** | `#14171F` | Metric widgets, model roster tiles, inner containers |
| **Elevated Surface** | `#1B202A` | Popups, dropdown menus, button standard states |
| **Subtle Border** | `#232834` | Inactive cards, section dividers, metric tile borders |
| **Active / Focus Border** | `#3B82F6` | Active input outlines, focus indicators, highlight cards |
| **Text Primary** | `#F8FAFC` | Main headings, metric figures, primary labels |
| **Text Secondary** | `#94A3B8` | Body text, sidebar items, meta information |
| **Text Muted** | `#64748B` | Category section headers, inactive indicators, place markers |
| **Primary Accent** | `#2563EB` | Primary buttons, active state indicators |
| **Accent Glow / Cyan** | `#38BDF8` | Active sidebar selections, focused highlights |
| **Status: Idle / Ready** | `#10B981` | Green status badges and live indicators |
| **Status: Busy / Running**| `#F59E0B` | Amber status indicators for models in execution |
| **Status: Error / Stopped**| `#EF4444` | Red badges for terminated runs or failed tasks |

---

## 2. Global Stylesheet (`theme.qss`)

Save this stylesheet and load it at application start to automatically style your existing PySide6 widgets:

```css
/* ==========================================================================
   GLOBAL BASE STYLING
   ========================================================================== */

QWidget {
    background-color: transparent;
    color: #F8FAFC;
    font-family: "Segoe UI", "Inter", -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #2563EB;
    selection-color: #FFFFFF;
}

QMainWindow, QDialog {
    background-color: #0B0D11;
}

/* ==========================================================================
   SIDEBAR & NAVIGATION
   ========================================================================== */

QFrame#sidebarContainer {
    background-color: #0E1117;
    border-right: 1px solid #1E232F;
    min-width: 240px;
    max-width: 260px;
}

QScrollArea#sidebarScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea#sidebarScrollArea QWidget {
    background-color: transparent;
}

/* Sidebar Top Workspace Card */
QFrame#sidebarHeader {
    background-color: #141822;
    border: 1px solid #232938;
    border-radius: 8px;
    margin: 12px 10px 8px 10px;
    padding: 10px;
}

QLabel#headerTitle {
    font-size: 12px;
    font-weight: 700;
    color: #F8FAFC;
    letter-spacing: 0.5px;
}

QLabel#headerStatus {
    font-size: 11px;
    font-weight: 600;
    color: #10B981;
}

/* Section Header Labels */
QLabel[class="sidebar-group-label"] {
    color: #64748B;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    padding: 14px 14px 4px 14px;
}

/* Navigation Items */
QPushButton[class="nav-button"] {
    background-color: transparent;
    border: none;
    border-radius: 6px;
    color: #94A3B8;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    padding: 8px 12px;
    margin: 2px 8px;
}

QPushButton[class="nav-button"]:hover {
    background-color: #181D27;
    color: #F1F5F9;
}

QPushButton[class="nav-button"]:checked {
    background-color: #1A2333;
    color: #38BDF8;
    font-weight: 600;
    border-left: 3px solid #38BDF8;
}

/* ==========================================================================
   CARDS & DASHBOARD TILES
   ========================================================================== */

/* Standard Card (Metrics, Worker Roster) */
QFrame[class="card"] {
    background-color: #14171F;
    border: 1px solid #232834;
    border-radius: 8px;
    padding: 12px;
}

QFrame[class="card"]:hover {
    border: 1px solid #2F3646;
}

/* Featured / Master Leader Card */
QFrame[class="card-featured"] {
    background-color: #141926;
    border: 1px solid #2563EB;
    border-radius: 8px;
    padding: 14px;
}

/* Metric Numerals & Titles */
QLabel[class="metric-value"] {
    font-size: 22px;
    font-weight: 700;
    color: #F8FAFC;
}

QLabel[class="metric-label"] {
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* ==========================================================================
   FORM INPUTS & COMMAND LINE
   ========================================================================== */

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0F1218;
    border: 1px solid #232834;
    border-radius: 6px;
    color: #F8FAFC;
    padding: 8px 12px;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #3B82F6;
    background-color: #131720;
}

/* ==========================================================================
   BUTTONS
   ========================================================================== */

/* Primary Action */
QPushButton[class="btn-primary"] {
    background-color: #2563EB;
    color: #FFFFFF;
    font-weight: 600;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
}

QPushButton[class="btn-primary"]:hover {
    background-color: #1D4ED8;
}

QPushButton[class="btn-primary"]:pressed {
    background-color: #1E40AF;
}

/* Secondary Action */
QPushButton[class="btn-secondary"] {
    background-color: #1B202A;
    border: 1px solid #2D3444;
    color: #CBD5E1;
    font-weight: 500;
    border-radius: 6px;
    padding: 7px 14px;
}

QPushButton[class="btn-secondary"]:hover {
    background-color: #242A38;
    color: #F8FAFC;
    border-color: #3B82F6;
}

/* ==========================================================================
   BADGES & STATUS PILLS
   ========================================================================== */

QLabel[class="badge-idle"] {
    background-color: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.25);
    color: #34D399;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

QLabel[class="badge-busy"] {
    background-color: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.25);
    color: #FBBF24;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
}

/* ==========================================================================
   MINIMAL SCROLLBAR
   ========================================================================== */

QScrollBar:vertical {
    border: none;
    background-color: transparent;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #232834;
    border-radius: 3px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3B82F6;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
```

---

## 3. PySide6 Implementation Guide

### 3.1 App Bootstrap & Stylesheet Loader

```python
import sys
from PySide6.QtWidgets import QApplication
from main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Load central QSS theme
    with open("theme.qss", "r", encoding="utf-8") as file:
        app.setStyleSheet(file.read())
        
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### 3.2 Sidebar Implementation (`sidebar.py`)

```python
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, 
    QScrollArea, QWidget, QButtonGroup
)
from PySide6.QtCore import Qt

class ModernSidebar(QFrame):
    def __init__(self, on_navigate_callback=None, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebarContainer")
        self.on_navigate = on_navigate_callback

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1. Header Banner
        header = QFrame()
        header.setObjectName("sidebarHeader")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(8, 8, 8, 8)
        h_layout.setSpacing(2)

        title = QLabel("AGENT CONSOLE")
        title.setObjectName("headerTitle")
        status = QLabel("● SYSTEM ONLINE")
        status.setObjectName("headerStatus")

        h_layout.addWidget(title)
        h_layout.addWidget(status)
        layout.addWidget(header)

        # 2. Scrollable Action List
        scroll = QScrollArea()
        scroll.setObjectName("sidebarScrollArea")
        scroll.setWidgetResizable(True)

        content = QWidget()
        self.nav_layout = QVBoxLayout(content)
        self.nav_layout.setContentsMargins(0, 4, 0, 4)
        self.nav_layout.setSpacing(2)

        self.btn_group = QButtonGroup(self)
        self.btn_group.setExclusive(True)

        # Sections
        self._add_group("OPERATIONS", [
            ("Mission Control", True),
            ("Task Dispatcher", False),
            ("Agent Squads", False),
            ("Mission Archive", False),
        ])

        self._add_group("ASSISTANT MODES", [
            ("Universal Chat", False),
            ("Chat with Files (RAG)", False),
            ("Deep Research", False),
            ("Image / Video Studio", False),
        ])

        self._add_group("CREATIVE TOOLS", [
            ("VS Code Studio", False),
            ("Agent Canvas IDE", False),
            ("Playground Studio", False),
            ("MaxMasAI Harness (Dev)", False),
            ("Node Agent Builder", False),
            ("Painter Canvas", False),
            ("Smart Notepad", False),
            ("Task Scheduler", False),
        ])

        self._add_group("SYSTEM", [
            ("Settings", False),
        ])

        self.nav_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _add_group(self, title: str, items: list[tuple[str, bool]]):
        lbl = QLabel(title)
        lbl.setProperty("class", "sidebar-group-label")
        self.nav_layout.addWidget(lbl)

        for name, active in items:
            btn = QPushButton(name)
            btn.setProperty("class", "nav-button")
            btn.setCheckable(True)
            btn.setChecked(active)
            btn.setCursor(Qt.PointingHandCursor)
            
            if self.on_navigate:
                btn.clicked.connect(lambda chk=False, target=name: self.on_navigate(target))

            self.btn_group.addButton(btn)
            self.nav_layout.addWidget(btn)
```

---

## 4. Anti-Patterns to Avoid

1. **Avoid Hardcoded Color Stylesheets in Code:**
   * ❌ `label.setStyleSheet("color: magenta;")`
   * ✅ `label.setProperty("class", "metric-value")`
2. **Avoid Multi-Color Card Outlines:**
   * Do not mix pink, green, cyan, and yellow borders in adjacent tiles. Use `#232834` universally, reserving `#2563EB` solely for focused or active leader cards.
3. **Avoid Emoji Clutter:**
   * Replace emoji bullet points (👑, ⚡, 🚀, 🤖) with standard SVG line icons or uniform spacing.