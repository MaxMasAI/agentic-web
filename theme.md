# 🎨 Agentic Web Design System & Theme Specification

This document defines the official design system tokens, typography rules, component styling guidelines, and master PySide6/PyQt QSS stylesheets for **Agentic Web**.

---

## 1. Design Tokens & Color Palette

### Core Theme Tokens
```ini
base                     = "dark"
primaryColor             = "#ff4b4b"       /* Crimson Coral Accent */
backgroundColor          = "#0e1117"       /* Deep Obsidian Canvas */
secondaryBackgroundColor = "#262730"       /* Charcoal Surface & Cards */
textColor                = "#fafafa"       /* Pure High-Contrast White */
font                     = "sans serif"    /* Inter / Segoe UI / System Sans */
```

### Full Color Palette Map

| Token Name | Hex / RGBA Code | Usage Description |
|---|---|---|
| `bg_canvas` | `#0e1117` | Main window background, central widget canvas |
| `bg_surface` | `#262730` | Cards, sidebars, panels, container boxes |
| `bg_surface_hover` | `#31333f` | Hover state for interactive cards and list items |
| `bg_input` | `#161920` | Inputs, text areas, code blocks |
| `primary_accent` | `#ff4b4b` | Primary buttons, active tabs, highlights, focus rings |
| `primary_gradient` | `qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e03131, stop:1 #ff4b4b)` | Primary CTA buttons and key indicator badges |
| `primary_hover` | `#ff6b6b` | Primary button hover state |
| `primary_dim` | `rgba(255, 75, 75, 0.15)` | User message bubble background, subtle selections |
| `border_subtle` | `rgba(255, 255, 255, 0.08)` | Default card and separator borders |
| `border_focus` | `#ff4b4b` | Focused inputs and active card rings |
| `text_primary` | `#fafafa` | Primary text, titles, user input |
| `text_secondary` | `#d0d2d6` | Subtitles, descriptions, secondary copy |
| `text_muted` | `#808495` | Placeholders, timestamps, disabled indicators |
| `success` | `#00c04b` | Success alerts, online agent statuses |
| `warning` | `#ffa421` | Warning alerts, busy worker status |
| `error` | `#ff2b2b` | Error badges, failed tests, destructive actions |

---

## 2. Multi-Agent Specialist Palette

| Agent ID | Specialist Name | Theme Accent | Icon | Description |
|---|---|---|---|---|
| `gemini` | Google Gemini 2.0 Flash | `#ff4b4b` | ✨ | Master Orchestrator |
| `deepseek` | DeepSeek Coder / Reasoner | `#00d4ff` | 🐋 | Algorithmic Code & TDD |
| `chatgpt` | OpenAI GPT-4o | `#00c04b` | ✳️ | Copy, Docs & Synthesis |
| `claude` | Anthropic Claude 3.5 Sonnet | `#ff8b3d` | ✴️ | Security & Architecture Audit |
| `perplexity` | Perplexity AI | `#3b82f6` | 🔍 | Live Web Search & Citations |
| `nvidia_ai` | Nvidia NIM AI | `#76b900` | 🟩 | High-Performance GPU Profiling |
| `dalle` | OpenAI DALL-E 3 | `#d946ef` | 🎨 | Visual Prompt Engineering |
| `meta_ai` | Meta AI | `#0ea5e9` | ♾️ | Viral Trends & Social Strategy |
| `copilot` | Microsoft Copilot | `#38bdf8` | 🪟 | Enterprise Coordination |
| `mistral` | Mistral Le Chat | `#f59e0b` | 🌪️ | Multilingual Logic & Compliance |
| `system` | OS & Host Operator | `#ff2b2b` | ⚡ | Local OS & Tool Execution |

---

## 3. Master PySide6 / PyQt QSS Stylesheet

```css
/* ========================================================================= */
/* GLOBAL RESET & MAIN APPLICATION WINDOW                                    */
/* ========================================================================= */
QMainWindow, QWidget#CentralWidget {
    background-color: #0e1117;
    color: #fafafa;
    font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* ========================================================================= */
/* MODERN SLIM SCROLLBARS                                                    */
/* ========================================================================= */
QScrollBar:vertical {
    background: #0e1117;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #262730;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #ff4b4b;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
}

QScrollBar:horizontal {
    background: #0e1117;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #262730;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #ff4b4b;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
    background: none;
}

/* ========================================================================= */
/* SIDEBAR & NAVIGATION DRAWER                                               */
/* ========================================================================= */
QWidget#SidebarWidget {
    background-color: #0e1117;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

QPushButton.nav-btn {
    background-color: transparent;
    color: #d0d2d6;
    font-size: 12.5px;
    font-weight: 600;
    text-align: left;
    padding: 8px 14px;
    border-radius: 6px;
    border: none;
}

QPushButton.nav-btn:hover {
    background-color: #262730;
    color: #fafafa;
}

QPushButton.nav-btn:checked, QPushButton.nav-btn[active="true"] {
    background-color: rgba(255, 75, 75, 0.12);
    color: #ff4b4b;
    font-weight: 700;
    border-left: 3px solid #ff4b4b;
}

/* ========================================================================= */
/* BUTTONS & CONTROLS                                                        */
/* ========================================================================= */
QPushButton {
    background: #262730;
    color: #fafafa;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 12.5px;
    font-weight: 600;
}

QPushButton:hover {
    background: #31333f;
    border-color: rgba(255, 255, 255, 0.2);
}

QPushButton:pressed {
    background: #1e2029;
}

QPushButton.primary-btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e03131, stop:1 #ff4b4b);
    color: #ffffff;
    font-weight: 700;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    padding: 8px 18px;
}

QPushButton.primary-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c92a2a, stop:1 #e03131);
    border-color: #ff4b4b;
}

QPushButton:disabled {
    background: rgba(38, 39, 48, 0.4);
    color: #808495;
    border-color: rgba(255, 255, 255, 0.04);
}

/* ========================================================================= */
/* INPUTS & TEXT EDITS                                                       */
/* ========================================================================= */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #161920;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    color: #fafafa;
    padding: 8px 10px;
    font-size: 13px;
    selection-background-color: #ff4b4b;
    selection-color: #ffffff;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid #ff4b4b;
    background-color: #1a1d26;
}

/* ========================================================================= */
/* COMBO BOXES                                                               */
/* ========================================================================= */
QComboBox {
    background-color: #262730;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    color: #fafafa;
    padding: 6px 12px;
    font-size: 12.5px;
    font-weight: 600;
}

QComboBox:hover {
    border-color: rgba(255, 255, 255, 0.2);
}

QComboBox:focus {
    border: 1.5px solid #ff4b4b;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #262730;
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #fafafa;
    selection-background-color: #ff4b4b;
    selection-color: #ffffff;
    border-radius: 6px;
    padding: 4px;
}

/* ========================================================================= */
/* CARDS & CONTAINERS                                                        */
/* ========================================================================= */
QFrame.card-panel {
    background-color: #262730;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 14px;
}

QFrame.card-panel:hover {
    border-color: rgba(255, 75, 75, 0.3);
}

/* ========================================================================= */
/* CHAT MESSAGE BUBBLES                                                      */
/* ========================================================================= */
QFrame.chat-bubble-user {
    background-color: rgba(255, 75, 75, 0.14);
    border: 1px solid #ff4b4b;
    border-radius: 12px;
    padding: 10px 14px;
}

QFrame.chat-bubble-assistant {
    background-color: #262730;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 10px 14px;
}

/* ========================================================================= */
/* SPLITTERS                                                                 */
/* ========================================================================= */
QSplitter::handle {
    background: rgba(255, 255, 255, 0.06);
}

QSplitter::handle:hover {
    background: #ff4b4b;
}

/* ========================================================================= */
/* TABS                                                                      */
/* ========================================================================= */
QTabBar::tab {
    background: #0e1117;
    color: #808495;
    padding: 8px 16px;
    font-weight: 600;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:hover {
    color: #fafafa;
}

QTabBar::tab:selected {
    color: #ff4b4b;
    border-bottom: 2px solid #ff4b4b;
}

QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: #262730;
    border-radius: 8px;
}
```

---

## 4. Component Implementation Guide

### 1. Chat Bubble Factory Pattern
```python
def create_chat_bubble(role: str, text: str, model_tag: str = "") -> QFrame:
    bubble = QFrame()
    is_user = (role == "user")
    
    if is_user:
        bubble.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 75, 75, 0.14);
                border: 1px solid #ff4b4b;
                border-radius: 12px;
                padding: 10px 14px;
            }
        """)
    else:
        bubble.setStyleSheet("""
            QFrame {
                background-color: #262730;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 10px 14px;
            }
        """)
    return bubble
```

### 2. Primary CTA Button Pattern
```python
btn = QPushButton("🚀 Send Mission")
btn.setStyleSheet("""
    QPushButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e03131, stop:1 #ff4b4b);
        color: #ffffff;
        font-size: 13px;
        font-weight: 800;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 8px;
        padding: 8px 18px;
    }
    QPushButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c92a2a, stop:1 #e03131);
        border: 1px solid #ff4b4b;
    }
    QPushButton:disabled {
        background: rgba(38, 39, 48, 0.5);
        color: #808495;
    }
""")
```

---

*© 2026 MaxMasAI. Design System Specification for Agentic Web.*
