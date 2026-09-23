"""
gui/theme.py - Dark Sci-Fi Glassmorphism Theme & Design System for PySide6
"""

COLORS = {
    "bg_dark": "#0e1117",
    "bg_sidebar": "#0e1117",
    "bg_card": "#262730",
    "bg_card_hover": "#31333f",
    "bg_input": "#161920",
    "bg_terminal": "#0e1117",
    "border": "rgba(255, 255, 255, 0.08)",
    "border_solid": "rgba(255, 255, 255, 0.12)",
    "border_focus": "#ff4b4b",
    "text_main": "#fafafa",
    "text_secondary": "#d0d2d6",
    "text_muted": "#808495",
    "accent_primary": "#ff4b4b",
    "accent_cyan": "#00d4ff",
    "accent_indigo": "#818cf8",
    "accent_emerald": "#00c04b",
    "accent_amber": "#ffa421",
    "accent_rose": "#ff2b2b",
    "accent_purple": "#c084fc",
}

MODEL_THEMES = {
    "gemini":     {"name": "Google Gemini",    "role": "Master Leader",          "icon": "✨", "color": "#ff4b4b", "vendor": "Google DeepMind"},
    "deepseek":   {"name": "DeepSeek",         "role": "Creative & Coder",       "icon": "🐋", "color": "#00d4ff", "vendor": "DeepSeek AI"},
    "chatgpt":    {"name": "ChatGPT (GPT-4o)", "role": "Copy & Synthesis",       "icon": "✳️", "color": "#00c04b", "vendor": "OpenAI"},
    "claude":     {"name": "Claude 3.5 Sonnet", "role": "Critique & Review",      "icon": "✴️", "color": "#ff8b3d", "vendor": "Anthropic"},
    "perplexity": {"name": "Perplexity AI",   "role": "Live Web Search",        "icon": "🔍", "color": "#3b82f6", "vendor": "Perplexity"},
    "nvidia_ai":  {"name": "Nvidia NIM",       "role": "High-Performance GPU",   "icon": "🟩", "color": "#76b900", "vendor": "Nvidia NIM"},
    "dalle":      {"name": "DALL-E 3",        "role": "Visual Designer",        "icon": "🎨", "color": "#d946ef", "vendor": "OpenAI DALL-E"},
    "meta_ai":    {"name": "Meta AI",         "role": "Social & Engagement",    "icon": "♾️", "color": "#0ea5e9", "vendor": "Meta AI"},
    "copilot":    {"name": "Microsoft Copilot","role": "Workflow Specialist",   "icon": "🪟", "color": "#ff4b4b", "vendor": "Microsoft"},
    "mistral":    {"name": "Mistral Le Chat", "role": "Multilingual Logic",     "icon": "🌪️", "color": "#ffa421", "vendor": "Mistral AI"},
    "web_agent":  {"name": "Web-Agent",       "role": "Autonomous Browser",     "icon": "🖥️", "color": "#00d4ff", "vendor": "Agentic Web"},
    "qwen":       {"name": "Qwen 2.5 Coder",   "role": "Senior Engineer",        "icon": "💻", "color": "#c084fc", "vendor": "Alibaba Cloud"},
    "qwen_coder": {"name": "Qwen 2.5 Coder",   "role": "Senior Engineer",        "icon": "💻", "color": "#c084fc", "vendor": "Alibaba Cloud"},
    "system":     {"name": "System",          "role": "OS & Host Operator",     "icon": "⚡", "color": "#ff2b2b", "vendor": "Host System"}
}

APP_QSS = """
/* Global Reset & Window */
QMainWindow, QWidget#CentralWidget {
    background-color: #0e1117;
    color: #fafafa;
    font-family: 'Segoe UI', 'Inter', -apple-system, sans-serif;
    font-size: 13px;
}

QScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Scrollbars */
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
}

/* Sidebar */
QWidget#SidebarWidget {
    background-color: #0e1117;
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

/* Buttons */
QPushButton {
    background-color: #262730;
    color: #fafafa;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 7px 16px;
    font-weight: 600;
    font-size: 12.5px;
}
QPushButton:hover {
    background-color: #31333f;
    border-color: rgba(255, 255, 255, 0.2);
}
QPushButton:pressed {
    background-color: #1e2029;
    color: #ffffff;
}
QPushButton:disabled {
    background-color: rgba(38, 39, 48, 0.4);
    color: #808495;
    border-color: rgba(255, 255, 255, 0.04);
}

QPushButton.primary-btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e03131, stop:1 #ff4b4b);
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 6px;
    font-size: 13px;
    font-weight: 700;
}
QPushButton.primary-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #c92a2a, stop:1 #e03131);
    border-color: #ff4b4b;
}

QPushButton.danger-btn {
    background-color: rgba(255, 43, 43, 0.12);
    color: #ff4b4b;
    border: 1px solid rgba(255, 43, 43, 0.35);
}
QPushButton.danger-btn:hover {
    background-color: rgba(255, 43, 43, 0.28);
    color: #ffffff;
    border-color: #ff2b2b;
}

QPushButton.success-btn {
    background-color: rgba(0, 192, 75, 0.12);
    color: #00c04b;
    border: 1px solid rgba(0, 192, 75, 0.35);
}
QPushButton.success-btn:hover {
    background-color: rgba(0, 192, 75, 0.28);
    color: #ffffff;
    border-color: #00c04b;
}

/* Nav Item Buttons */
QPushButton.nav-btn {
    background-color: transparent;
    color: #d0d2d6;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 8px 14px;
    text-align: left;
    font-weight: 600;
    font-size: 12.5px;
}
QPushButton.nav-btn:hover {
    background-color: #262730;
    color: #fafafa;
}
QPushButton.nav-btn:checked, QPushButton.nav-btn.active, QPushButton.nav-btn[active="true"] {
    background-color: rgba(255, 75, 75, 0.12);
    color: #ff4b4b;
    border-left: 3px solid #ff4b4b;
    font-weight: 700;
}

/* Input Fields & Text Edits */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #161920;
    color: #fafafa;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 8px 12px;
    font-family: 'Segoe UI', sans-serif;
    selection-background-color: #ff4b4b;
    selection-color: #ffffff;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1.5px solid #ff4b4b;
    background-color: #1a1d26;
}

QPlainTextEdit.code-editor, QTextEdit.code-editor {
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12.5px;
    line-height: 1.5;
    background-color: #0e1117;
    color: #00d4ff;
    border: 1px solid rgba(255, 255, 255, 0.12);
}

/* ComboBox */
QComboBox {
    background-color: #262730;
    color: #fafafa;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 12px;
    font-weight: 500;
    min-height: 24px;
}
QComboBox:focus, QComboBox:hover {
    border-color: #ff4b4b;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid rgba(255, 255, 255, 0.08);
}
QComboBox QAbstractItemView {
    background-color: #262730;
    color: #fafafa;
    border: 1px solid rgba(255, 255, 255, 0.15);
    selection-background-color: #ff4b4b;
    selection-color: #ffffff;
    border-radius: 6px;
    padding: 4px;
}

/* Checkbox & Radio Buttons */
QCheckBox, QRadioButton {
    color: #fafafa;
    spacing: 8px;
    font-weight: 500;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 4px;
    background: #161920;
}
QRadioButton::indicator {
    border-radius: 9px;
}
QCheckBox::indicator:checked {
    background: #ff4b4b;
    border-color: #ff4b4b;
}
QRadioButton::indicator:checked {
    background: #ff4b4b;
    border-color: #ff4b4b;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #262730;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #ff4b4b;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #ff4b4b;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #ff4b4b;
}

/* SpinBox */
QSpinBox, QDoubleSpinBox {
    background-color: #161920;
    color: #fafafa;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 10px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: #262730;
    border-radius: 8px;
    padding: 12px;
}
QTabBar::tab {
    background-color: #0e1117;
    color: #808495;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 18px;
    font-weight: 600;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background-color: #262730;
    color: #ff4b4b;
    border-top: 2px solid #ff4b4b;
    border-color: rgba(255, 255, 255, 0.1) rgba(255, 255, 255, 0.1) transparent rgba(255, 255, 255, 0.1);
}
QTabBar::tab:hover:!selected {
    color: #fafafa;
    background-color: #1a1d26;
}

/* GroupBox & Frames */
QGroupBox {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: 700;
    color: #ff4b4b;
    background-color: rgba(38, 39, 48, 0.6);
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #0e1117;
}

/* ToolTips */
QToolTip {
    background-color: #262730;
    color: #fafafa;
    border: 1px solid #ff4b4b;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Dialogs & MessageBoxes */
QDialog, QMessageBox {
    background-color: #0e1117;
    color: #fafafa;
    border: 1px solid rgba(255, 75, 75, 0.4);
    border-radius: 12px;
}

QMessageBox QLabel {
    color: #fafafa;
    font-size: 13px;
    line-height: 1.5;
}

QMessageBox QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e03131, stop:1 #ff4b4b);
    color: #ffffff;
    border: 1px solid #ff4b4b;
    border-radius: 6px;
    font-weight: 700;
    font-size: 13px;
    min-width: 90px;
    min-height: 32px;
    padding: 4px 16px;
}

QMessageBox QPushButton:hover {
    background: #ff4b4b;
}
"""
