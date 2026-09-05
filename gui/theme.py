"""
gui/theme.py - Dark Sci-Fi Glassmorphism Theme & Design System for PySide6
"""

COLORS = {
    "bg_dark": "#080b11",
    "bg_sidebar": "#0b0f19",
    "bg_card": "#0f172a",
    "bg_card_hover": "#131d31",
    "bg_input": "#090d16",
    "bg_terminal": "#030712",
    "border": "rgba(56, 189, 248, 0.18)",
    "border_solid": "#1e293b",
    "border_focus": "#38bdf8",
    "text_main": "#f8fafc",
    "text_secondary": "#cbd5e1",
    "text_muted": "#64748b",
    "accent_cyan": "#38bdf8",
    "accent_indigo": "#818cf8",
    "accent_emerald": "#10b981",
    "accent_amber": "#f59e0b",
    "accent_rose": "#ef4444",
    "accent_purple": "#c084fc",
}

MODEL_THEMES = {
    "gemini":     {"name": "Google Gemini",    "role": "Master Leader",          "icon": "👑", "color": "#38bdf8", "vendor": "Google DeepMind"},
    "deepseek":   {"name": "DeepSeek",         "role": "Creative & Coder",       "icon": "⚡", "color": "#06b6d4", "vendor": "DeepSeek AI"},
    "chatgpt":    {"name": "ChatGPT (GPT-4o)", "role": "Copy & Synthesis",       "icon": "🟢", "color": "#10b981", "vendor": "OpenAI"},
    "claude":     {"name": "Claude",           "role": "Critique & Review",      "icon": "🟠", "color": "#f97316", "vendor": "Anthropic"},
    "perplexity": {"name": "Perplexity AI",   "role": "Live Web Search",        "icon": "🔍", "color": "#3b82f6", "vendor": "Perplexity"},
    "nvidia_ai":  {"name": "Nvidia NIM",       "role": "High-Performance GPU",   "icon": "🏎️", "color": "#22c55e", "vendor": "Nvidia NIM"},
    "dalle":      {"name": "DALL-E 3",        "role": "Visual Designer",        "icon": "🎨", "color": "#c084fc", "vendor": "OpenAI DALL-E"},
    "meta_ai":    {"name": "Meta AI",         "role": "Social & Engagement",    "icon": "📈", "color": "#0ea5e9", "vendor": "Meta AI"},
    "copilot":    {"name": "Microsoft Copilot","role": "Workflow Specialist",   "icon": "📊", "color": "#38bdf8", "vendor": "Microsoft"},
    "mistral":    {"name": "Mistral Le Chat", "role": "Multilingual Logic",     "icon": "🌐", "color": "#f59e0b", "vendor": "Mistral AI"}
}

APP_QSS = """
/* Global Reset & Window */
QMainWindow, QWidget#CentralWidget {
    background-color: #080b11;
    color: #cbd5e1;
    font-family: 'Segoe UI', 'Outfit', -apple-system, sans-serif;
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
    background: #080b11;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:vertical {
    background: #1e293b;
    min-height: 24px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #38bdf8;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar:horizontal {
    background: #080b11;
    height: 8px;
    margin: 0px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal {
    background: #1e293b;
    min-width: 24px;
    border-radius: 4px;
}
QScrollBar::handle:horizontal:hover {
    background: #38bdf8;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Sidebar */
QWidget#SidebarWidget {
    background-color: #0b0f19;
    border-right: 1px solid rgba(56, 189, 248, 0.14);
}

/* Buttons */
QPushButton {
    background-color: rgba(15, 23, 42, 0.85);
    color: #cbd5e1;
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}
QPushButton:hover {
    background-color: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border-color: #38bdf8;
}
QPushButton:pressed {
    background-color: rgba(56, 189, 248, 0.25);
    color: #ffffff;
}
QPushButton:disabled {
    background-color: rgba(15, 23, 42, 0.4);
    color: #475569;
    border-color: rgba(255, 255, 255, 0.05);
}

QPushButton.primary-btn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0284c7, stop:1 #6366f1);
    color: #ffffff;
    border: none;
    font-size: 14px;
    font-weight: 700;
}
QPushButton.primary-btn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38bdf8, stop:1 #818cf8);
}

QPushButton.danger-btn {
    background-color: rgba(239, 68, 68, 0.12);
    color: #f87171;
    border: 1px solid rgba(239, 68, 68, 0.35);
}
QPushButton.danger-btn:hover {
    background-color: rgba(239, 68, 68, 0.28);
    color: #ffffff;
    border-color: #ef4444;
}

QPushButton.success-btn {
    background-color: rgba(16, 185, 129, 0.12);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.35);
}
QPushButton.success-btn:hover {
    background-color: rgba(16, 185, 129, 0.28);
    color: #ffffff;
    border-color: #10b981;
}

/* Nav Item Buttons */
QPushButton.nav-btn {
    background-color: transparent;
    color: #94a3b8;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    font-size: 13px;
}
QPushButton.nav-btn:hover {
    background-color: rgba(56, 189, 248, 0.08);
    color: #38bdf8;
    border-color: rgba(56, 189, 248, 0.2);
}
QPushButton.nav-btn:checked, QPushButton.nav-btn.active {
    background-color: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    border-color: rgba(56, 189, 248, 0.45);
    font-weight: 700;
}

/* Input Fields & Text Edits */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #090d16;
    color: #f8fafc;
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 8px;
    padding: 8px 12px;
    font-family: 'Segoe UI', sans-serif;
    selection-background-color: #38bdf8;
    selection-color: #080b11;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #38bdf8;
    background-color: #0d1322;
}

QPlainTextEdit.code-editor, QTextEdit.code-editor {
    font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12.5px;
    line-height: 1.5;
    background-color: #030712;
    color: #4ade80;
    border: 1px solid rgba(56, 189, 248, 0.25);
}

/* ComboBox */
QComboBox {
    background-color: #090d16;
    color: #f8fafc;
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 8px;
    padding: 6px 12px;
    font-weight: 500;
    min-height: 24px;
}
QComboBox:focus, QComboBox:hover {
    border-color: #38bdf8;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 28px;
    border-left: 1px solid rgba(56, 189, 248, 0.15);
}
QComboBox QAbstractItemView {
    background-color: #0b0f19;
    color: #cbd5e1;
    border: 1px solid #38bdf8;
    selection-background-color: rgba(56, 189, 248, 0.2);
    selection-color: #38bdf8;
    padding: 4px;
}

/* Checkbox & Radio Buttons */
QCheckBox, QRadioButton {
    color: #cbd5e1;
    spacing: 8px;
    font-weight: 500;
}
QCheckBox::indicator, QRadioButton::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 4px;
    background: #090d16;
}
QRadioButton::indicator {
    border-radius: 9px;
}
QCheckBox::indicator:checked {
    background: #38bdf8;
    border-color: #38bdf8;
}
QRadioButton::indicator:checked {
    background: #38bdf8;
    border-color: #38bdf8;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 6px;
    background: #1e293b;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #38bdf8;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #38bdf8;
    width: 16px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 8px;
}
QSlider::handle:horizontal:hover {
    background: #38bdf8;
}

/* SpinBox */
QSpinBox, QDoubleSpinBox {
    background-color: #090d16;
    color: #f8fafc;
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 8px;
    padding: 6px 10px;
}

/* Tabs */
QTabWidget::pane {
    border: 1px solid rgba(255, 255, 255, 0.08);
    background-color: #0b0f19;
    border-radius: 8px;
    padding: 12px;
}
QTabBar::tab {
    background-color: #090d16;
    color: #94a3b8;
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    margin-right: 3px;
}
QTabBar::tab:selected {
    background-color: #0b0f19;
    color: #38bdf8;
    border-top: 2px solid #38bdf8;
    border-color: rgba(56, 189, 248, 0.3) rgba(56, 189, 248, 0.3) transparent rgba(56, 189, 248, 0.3);
}
QTabBar::tab:hover:!selected {
    color: #f8fafc;
    background-color: #131d31;
}

/* GroupBox & Frames */
QGroupBox {
    border: 1px solid rgba(56, 189, 248, 0.15);
    border-radius: 10px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: 700;
    color: #38bdf8;
    background-color: rgba(15, 23, 42, 0.5);
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    background-color: #080b11;
}

/* ToolTips */
QToolTip {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #38bdf8;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* Dialogs & MessageBoxes */
QDialog, QMessageBox {
    background-color: #0b0f19;
    color: #f8fafc;
    border: 1px solid rgba(56, 189, 248, 0.4);
    border-radius: 12px;
}

QMessageBox QLabel {
    color: #f1f5f9;
    font-size: 13px;
    line-height: 1.5;
}

QMessageBox QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38bdf8, stop:1 #2563eb);
    color: #ffffff;
    border: 1px solid #38bdf8;
    border-radius: 8px;
    font-weight: 700;
    font-size: 13px;
    min-width: 90px;
    min-height: 32px;
    padding: 4px 16px;
}

QMessageBox QPushButton:hover {
    background: #38bdf8;
}
"""
