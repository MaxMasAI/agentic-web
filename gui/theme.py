"""
gui/theme.py - Dark Modern Design System for PySide6
Conforms strictly to design_system_ui_theme_documentation.md
"""

import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THEME_QSS_FILE = os.path.join(PROJECT_ROOT, "theme.qss")

# Design Tokens conforming to design_system_ui_theme_documentation.md
COLORS = {
    "canvas_bg": "#0B0D11",
    "sidebar_surface": "#0E1117",
    "card_surface": "#14171F",
    "elevated_surface": "#1B202A",
    "subtle_border": "#232834",
    "active_border": "#3B82F6",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "primary_accent": "#2563EB",
    "accent_cyan": "#38BDF8",
    "status_idle": "#10B981",
    "status_busy": "#F59E0B",
    "status_error": "#EF4444",
    
    # Legacy alias compatibility
    "bg_dark": "#0B0D11",
    "bg_sidebar": "#0E1117",
    "bg_card": "#14171F",
    "bg_card_hover": "#1B202A",
    "bg_input": "#0F1218",
    "bg_terminal": "#0B0D11",
    "border": "#232834",
    "border_solid": "#232834",
    "border_focus": "#3B82F6",
    "text_main": "#F8FAFC",
    "accent_primary": "#2563EB",
    "accent_indigo": "#818cf8",
    "accent_emerald": "#10B981",
    "accent_amber": "#F59E0B",
    "accent_rose": "#EF4444",
    "accent_purple": "#c084fc",
}

MODEL_THEMES = {
    "gemini":     {"name": "Google Gemini",    "role": "Master Leader",          "icon": "✨", "color": "#38BDF8", "vendor": "Google DeepMind"},
    "deepseek":   {"name": "DeepSeek",         "role": "Creative & Coder",       "icon": "🐋", "color": "#38BDF8", "vendor": "DeepSeek AI"},
    "chatgpt":    {"name": "ChatGPT (GPT-4o)", "role": "Copy & Synthesis",       "icon": "✳️", "color": "#10B981", "vendor": "OpenAI"},
    "claude":     {"name": "Claude 3.5 Sonnet", "role": "Critique & Review",      "icon": "✴️", "color": "#F59E0B", "vendor": "Anthropic"},
    "perplexity": {"name": "Perplexity AI",   "role": "Live Web Search",        "icon": "🔍", "color": "#3B82F6", "vendor": "Perplexity"},
    "nvidia_ai":  {"name": "Nvidia NIM",       "role": "High-Performance GPU",   "icon": "🟩", "color": "#10B981", "vendor": "Nvidia NIM"},
    "dalle":      {"name": "DALL-E 3",        "role": "Visual Designer",        "icon": "🎨", "color": "#D946EF", "vendor": "OpenAI DALL-E"},
    "meta_ai":    {"name": "Meta AI",         "role": "Social & Engagement",    "icon": "♾️", "color": "#38BDF8", "vendor": "Meta AI"},
    "copilot":    {"name": "Microsoft Copilot","role": "Workflow Specialist",   "icon": "🪟", "color": "#3B82F6", "vendor": "Microsoft"},
    "mistral":    {"name": "Mistral Le Chat", "role": "Multilingual Logic",     "icon": "🌪️", "color": "#F59E0B", "vendor": "Mistral AI"},
    "web_agent":  {"name": "Web-Agent",       "role": "Autonomous Browser",     "icon": "🖥️", "color": "#38BDF8", "vendor": "Agentic Web"},
    "qwen":       {"name": "Qwen 2.5 Coder",   "role": "Senior Engineer",        "icon": "💻", "color": "#C084FC", "vendor": "Alibaba Cloud"},
    "qwen_coder": {"name": "Qwen 2.5 Coder",   "role": "Senior Engineer",        "icon": "💻", "color": "#C084FC", "vendor": "Alibaba Cloud"},
    "system":     {"name": "System",          "role": "OS & Host Operator",     "icon": "⚡", "color": "#38BDF8", "vendor": "Host System"}
}


def load_theme_qss() -> str:
    """Loads the centralized theme.qss stylesheet."""
    if os.path.exists(THEME_QSS_FILE):
        try:
            with open(THEME_QSS_FILE, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"[Theme] Error reading theme.qss: {e}")
    return ""


APP_QSS = load_theme_qss()
