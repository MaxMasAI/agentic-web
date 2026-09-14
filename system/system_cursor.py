"""
system/system_cursor.py - Dynamic Multi-Agent Visual Cursor Overlay & Telemetry Engine.

Provides an Antigravity-styled collaborative cursor system that dynamically transforms
based on which worker is currently executing. Features agent-specific visual templates
(custom colors, gradients, glowing dots, badges, action chips, click ripples, and desktop PySide6 overlay).
"""

import os
import sys
import json
import asyncio
from typing import Optional, Tuple, Dict, Any

# ─────────────────────────────────────────────────────────────────────────────
# 1. Agent Cursor Visual Templates Registry
# ─────────────────────────────────────────────────────────────────────────────
AGENT_CURSOR_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "gemini": {
        "id": "gemini",
        "name": "Google Gemini",
        "icon": "👑",
        "color": "#7c3aed",                 # Royal Violet
        "gradient": "linear-gradient(135deg, #4285f4, #9333ea)",
        "dot_color": "#a78bfa",
        "accent": "#38bdf8",
        "role_title": "Master Orchestrator",
        "default_action": "Orchestrating Plan..."
    },
    "deepseek": {
        "id": "deepseek",
        "name": "DeepSeek",
        "icon": "🔬",
        "color": "#2563eb",                 # Deep Blue
        "gradient": "linear-gradient(135deg, #3b82f6, #1d4ed8)",
        "dot_color": "#60a5fa",
        "accent": "#93c5fd",
        "role_title": "Research & Reasoning",
        "default_action": "Deep Thinking & Coding..."
    },
    "chatgpt": {
        "id": "chatgpt",
        "name": "OpenAI ChatGPT",
        "icon": "✍️",
        "color": "#059669",                 # OpenAI Emerald
        "gradient": "linear-gradient(135deg, #10b981, #047857)",
        "dot_color": "#34d399",
        "accent": "#a7f3d0",
        "role_title": "Campaign & Copywriting",
        "default_action": "Synthesizing Deliverables..."
    },
    "claude": {
        "id": "claude",
        "name": "Anthropic Claude",
        "icon": "🎭",
        "color": "#d97706",                 # Warm Amber / Terracotta
        "gradient": "linear-gradient(135deg, #f59e0b, #b45309)",
        "dot_color": "#fcd34d",
        "accent": "#fef08a",
        "role_title": "Editorial & Security",
        "default_action": "Reviewing Nuances..."
    },
    "meta_ai": {
        "id": "meta_ai",
        "name": "Meta AI",
        "icon": "🌐",
        "color": "#0284c7",                 # Meta Sky Blue
        "gradient": "linear-gradient(135deg, #0ea5e9, #0369a1)",
        "dot_color": "#38bdf8",
        "accent": "#bae6fd",
        "role_title": "Social & Viral Trends",
        "default_action": "Optimizing Engagement..."
    },
    "dalle": {
        "id": "dalle",
        "name": "DALL-E 3",
        "icon": "🎨",
        "color": "#ec4899",                 # Magenta / Pink
        "gradient": "linear-gradient(135deg, #f43f5e, #be185d)",
        "dot_color": "#fb7185",
        "accent": "#fecdd3",
        "role_title": "Visual Prompt Studio",
        "default_action": "Designing Graphic Assets..."
    },
    "perplexity": {
        "id": "perplexity",
        "name": "Perplexity AI",
        "icon": "🔍",
        "color": "#0d9488",                 # Teal Search
        "gradient": "linear-gradient(135deg, #14b8a6, #0f766e)",
        "dot_color": "#2dd4bf",
        "accent": "#99f6e4",
        "role_title": "Fact-Checking & Citations",
        "default_action": "Verifying Live Sources..."
    },
    "copilot": {
        "id": "copilot",
        "name": "Microsoft Copilot",
        "icon": "📎",
        "color": "#0078d4",                 # Windows / Microsoft Blue
        "gradient": "linear-gradient(135deg, #0284c7, #005a9e)",
        "dot_color": "#38bdf8",
        "accent": "#bae6fd",
        "role_title": "Enterprise Integration",
        "default_action": "Formatting Office Assets..."
    },
    "nvidia_ai": {
        "id": "nvidia_ai",
        "name": "Nvidia NIM AI",
        "icon": "⚡",
        "color": "#65a30d",                 # Nvidia Lime Green
        "gradient": "linear-gradient(135deg, #76b900, #4d7c0f)",
        "dot_color": "#a3e635",
        "accent": "#d9f99d",
        "role_title": "GPU Compute Advisor",
        "default_action": "Optimizing Compute Scaling..."
    },
    "mistral": {
        "id": "mistral",
        "name": "Mistral Le Chat",
        "icon": "🌪️",
        "color": "#ea580c",                 # Mistral Orange
        "gradient": "linear-gradient(135deg, #f97316, #c2410c)",
        "dot_color": "#fb923c",
        "accent": "#ffedd5",
        "role_title": "Multilingual Specialist",
        "default_action": "Translating & Logic Verification..."
    },
    "web_agent": {
        "id": "web_agent",
        "name": "Web-Agent",
        "icon": "🖥️",
        "color": "#06b6d4",                 # Cyan Overseer
        "gradient": "linear-gradient(135deg, #06b6d4, #0891b2)",
        "dot_color": "#22d3ee",
        "accent": "#cffafe",
        "role_title": "OS Browser Overseer",
        "default_action": "Full-Screen Navigation..."
    }
}


def get_agent_cursor_template(agent_id: str, action_text: str = "") -> Dict[str, Any]:
    """
    Returns the visual template for an agent.
    If the agent is a custom model not in predefined templates, dynamically computes
    a unique harmonious visual palette.
    """
    clean_id = (agent_id or "gemini").strip().lower()
    
    if clean_id in AGENT_CURSOR_TEMPLATES:
        tmpl = dict(AGENT_CURSOR_TEMPLATES[clean_id])
        if action_text:
            tmpl["default_action"] = action_text
        return tmpl
        
    # Check core agentlist for custom agent metadata
    try:
        from core import agentlist
        custom_agent = agentlist.get_agent_by_id(clean_id)
        if custom_agent:
            name = custom_agent.get("name", clean_id.title())
            role = custom_agent.get("role", "Custom Model Agent")
            is_leader = custom_agent.get("is_leader", False)
            return {
                "id": clean_id,
                "name": name,
                "icon": "👑" if is_leader else "⭐",
                "color": "#8b5cf6" if is_leader else "#0284c7",
                "gradient": "linear-gradient(135deg, #9333ea, #6366f1)" if is_leader else "linear-gradient(135deg, #0284c7, #38bdf8)",
                "dot_color": "#c084fc" if is_leader else "#7dd3fc",
                "accent": "#fde047" if is_leader else "#a5f3fc",
                "role_title": role,
                "default_action": action_text or "Executing Task..."
            }
    except Exception:
        pass
        
    # Generic Fallback Template
    return {
        "id": clean_id,
        "name": clean_id.title(),
        "icon": "🤖",
        "color": "#7c3aed",
        "gradient": "linear-gradient(135deg, #6d28d9, #4c1d95)",
        "dot_color": "#a78bfa",
        "accent": "#38bdf8",
        "role_title": "Specialist Agent",
        "default_action": action_text or "Executing Active Task..."
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. JavaScript DOM Injection for In-Browser Agent Cursors
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_CURSOR_JS = """
(function() {
    if (window.__system_cursor_installed) return;
    window.__system_cursor_installed = true;

    const style = document.createElement('style');
    style.id = 'agentic-system-cursor-style';
    style.textContent = `
        #system-cursor-wrapper {
            position: fixed;
            top: 0;
            left: 0;
            width: 0;
            height: 0;
            z-index: 2147483647;
            pointer-events: none;
            user-select: none;
            transition: transform 0.12s cubic-bezier(0.2, 0.9, 0.3, 1);
            will-change: transform;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", monospace, sans-serif;
        }

        .system-cursor-pointer {
            position: absolute;
            top: -2px;
            left: -2px;
            width: 24px;
            height: 24px;
            filter: drop-shadow(0 2px 6px rgba(0, 0, 0, 0.55));
            transform-origin: 0 0;
            transition: transform 0.1s ease;
        }

        .system-cursor-badge {
            position: absolute;
            left: 14px;
            top: 14px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, #6d28d9, #4c1d95);
            color: #ffffff;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.3px;
            padding: 4px 10px;
            border-radius: 6px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45), inset 0 1px 0 rgba(255, 255, 255, 0.25);
            white-space: nowrap;
            line-height: 1.2;
            animation: system-badge-fade-in 0.2s ease-out;
            border: 1px solid rgba(167, 139, 250, 0.4);
            transition: background 0.3s ease, border-color 0.3s ease;
        }

        .system-cursor-dot {
            width: 6px;
            height: 6px;
            background-color: #a78bfa;
            border-radius: 50%;
            box-shadow: 0 0 8px #c4b5fd;
            animation: system-pulse 1.5s infinite;
        }

        .system-action-chip {
            background: rgba(0, 0, 0, 0.45);
            font-size: 10.5px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
            color: #38bdf8;
            margin-left: 4px;
            display: none;
            letter-spacing: 0.2px;
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(56, 189, 248, 0.3);
            transition: color 0.3s ease, border-color 0.3s ease;
        }

        .system-cursor-ripple {
            position: absolute;
            width: 34px;
            height: 34px;
            border-radius: 50%;
            border: 2px solid #a78bfa;
            transform: translate(-50%, -50%) scale(0.2);
            opacity: 1;
            pointer-events: none;
            animation: system-ripple-wave 0.5s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
        }

        #system-screen-highlight {
            position: fixed;
            border: 2px solid #a78bfa;
            background: rgba(124, 58, 237, 0.12);
            border-radius: 6px;
            z-index: 2147483640;
            pointer-events: none;
            display: none;
            box-shadow: 0 0 16px rgba(124, 58, 237, 0.45), inset 0 0 10px rgba(124, 58, 237, 0.2);
            transition: all 0.2s ease;
        }

        @keyframes system-pulse {
            0% { transform: scale(0.95); opacity: 0.8; }
            50% { transform: scale(1.3); opacity: 1; }
            100% { transform: scale(0.95); opacity: 0.8; }
        }

        @keyframes system-badge-fade-in {
            from { opacity: 0; transform: translateY(-4px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        @keyframes system-ripple-wave {
            0% { transform: translate(-50%, -50%) scale(0.2); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(2.4); opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    const wrapper = document.createElement('div');
    wrapper.id = 'system-cursor-wrapper';
    wrapper.innerHTML = `
        <svg class="system-cursor-pointer" id="system-cursor-svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path id="system-cursor-path" d="M4 2L20 10.5L12.5 13L9 21L4 2Z" fill="#7c3aed" stroke="#ffffff" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>
        <div class="system-cursor-badge" id="system-badge-container">
            <span class="system-cursor-dot" id="system-cursor-dot"></span>
            <span id="system-cursor-name">👑 Google Gemini</span>
            <span class="system-action-chip" id="system-action-chip">⚡ Master Orchestrator</span>
        </div>
    `;
    document.body.appendChild(wrapper);

    const highlight = document.createElement('div');
    highlight.id = 'system-screen-highlight';
    document.body.appendChild(highlight);

    window.__system_cursor_x = window.innerWidth / 2;
    window.__system_cursor_y = window.innerHeight / 2;
    wrapper.style.transform = `translate(${window.__system_cursor_x}px, ${window.__system_cursor_y}px)`;
})();
"""


async def inject_system_cursor(
    page,
    agent_id: str = "gemini",
    action_text: str = ""
):
    """
    Injects or dynamically updates the in-browser cursor matching the working agent's template.
    """
    if not page:
        return
    template = get_agent_cursor_template(agent_id, action_text)
    try:
        await page.evaluate(SYSTEM_CURSOR_JS)
        update_js = f"""
        (() => {{
            const wrapper = document.getElementById('system-cursor-wrapper');
            const svgPath = document.getElementById('system-cursor-path');
            const badge = document.getElementById('system-badge-container');
            const dot = document.getElementById('system-cursor-dot');
            const nameEl = document.getElementById('system-cursor-name');
            const actionEl = document.getElementById('system-action-chip');

            if (wrapper) wrapper.style.display = 'block';
            if (svgPath) svgPath.setAttribute('fill', {json.dumps(template['color'])});
            if (badge) {{
                badge.style.background = {json.dumps(template['gradient'])};
                badge.style.borderColor = {json.dumps(template['dot_color'])};
            }}
            if (dot) {{
                dot.style.backgroundColor = {json.dumps(template['dot_color'])};
                dot.style.boxShadow = `0 0 8px ${{ {json.dumps(template['dot_color'])} }}`;
            }}
            if (nameEl) nameEl.textContent = `${{ {json.dumps(template['icon'])} }} ${{ {json.dumps(template['name'])} }}`;
            if (actionEl) {{
                const act = {json.dumps(template['default_action'])};
                if (act) {{
                    actionEl.textContent = act;
                    actionEl.style.color = {json.dumps(template['accent'])};
                    actionEl.style.borderColor = {json.dumps(template['accent'])};
                    actionEl.style.display = 'inline-block';
                }} else {{
                    actionEl.style.display = 'none';
                }}
            }}
        }})();
        """
        await page.evaluate(update_js)
    except Exception:
        pass


async def animate_system_cursor_move(page, target_x: float, target_y: float, steps: int = 12):
    """Smoothly animates the agent cursor pointer to (target_x, target_y)."""
    if not page:
        return
    js = f"""
    (async () => {{
        const wrapper = document.getElementById('system-cursor-wrapper');
        if (!wrapper) return;
        const startX = window.__system_cursor_x || 0;
        const startY = window.__system_cursor_y || 0;
        const destX = {target_x};
        const destY = {target_y};
        const totalSteps = {steps};

        for (let i = 1; i <= totalSteps; i++) {{
            const t = i / totalSteps;
            const ease = t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t;
            const cx = startX + (destX - startX) * ease;
            const cy = startY + (destY - startY) * ease;
            wrapper.style.transform = `translate(${{cx}}px, ${{cy}}px)`;
            window.__system_cursor_x = cx;
            window.__system_cursor_y = cy;
            await new Promise(r => setTimeout(r, 16));
        }}
    }})();
    """
    try:
        await page.evaluate(js)
    except Exception:
        pass


async def simulate_system_cursor_click(page, target_x: float, target_y: float, agent_id: str = "gemini", action_label: str = "🖱️ Click"):
    """Moves active agent cursor to coordinate, emits colored ripple wave, and clicks."""
    if not page:
        return
    template = get_agent_cursor_template(agent_id, action_label)
    await inject_system_cursor(page, agent_id=agent_id, action_text=action_label)
    await animate_system_cursor_move(page, target_x, target_y, steps=10)
    ripple_js = f"""
    (() => {{
        const rip = document.createElement('div');
        rip.className = 'system-cursor-ripple';
        rip.style.left = '{target_x}px';
        rip.style.top = '{target_y}px';
        rip.style.borderColor = '{template["dot_color"]}';
        document.body.appendChild(rip);
        setTimeout(() => rip.remove(), 600);
    }})();
    """
    try:
        await page.evaluate(ripple_js)
        await page.mouse.click(target_x, target_y)
    except Exception:
        pass


# ─────────────────────────────────────────────────────────────────────────────
# 3. PySide6 Desktop-Level Dynamic Agent Cursor Overlay (Cross-Monitor Transparent)
# ─────────────────────────────────────────────────────────────────────────────
try:
    from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout
    from PySide6.QtCore import Qt, QPoint, QRect
    from PySide6.QtGui import QPainter, QColor, QPolygon, QFont, QPen, QBrush

    class DesktopSystemCursorOverlay(QWidget):
        """
        A native transparent, click-through overlay window rendering the dynamic
        agent cursor across the Windows desktop styled with the active worker's template.
        """
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowFlags(
                Qt.WindowStaysOnTopHint |
                Qt.FramelessWindowHint |
                Qt.SubWindow |
                Qt.WindowTransparentForInput
            )
            self.setAttribute(Qt.WA_TranslucentBackground, True)
            self.setAttribute(Qt.WA_ShowWithoutActivating, True)
            self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

            self.cursor_pos = QPoint(400, 300)
            self.current_agent_id = "gemini"
            self.template = get_agent_cursor_template("gemini")
            self.action_text = self.template.get("default_action", "Master Orchestrator")
            self.resize(360, 90)

        def set_active_worker(self, agent_id: str, action_text: str = ""):
            """Dynamically updates the overlay to match the active worker agent's template."""
            self.current_agent_id = agent_id
            self.template = get_agent_cursor_template(agent_id, action_text)
            if action_text:
                self.action_text = action_text
            else:
                self.action_text = self.template.get("default_action", "")
            self.update()

        def set_cursor_location(self, x: int, y: int, action_text: str = ""):
            """Moves the overlay cursor to desktop (x, y) coordinates."""
            self.cursor_pos = QPoint(x, y)
            if action_text:
                self.action_text = action_text
            self.move(x - 4, y - 4)
            self.update()

        def paintEvent(self, event):
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing, True)

            tmpl = self.template

            # 1. Draw Pointer Arrow with Agent's Color
            pointer = QPolygon([
                QPoint(4, 4),
                QPoint(22, 12),
                QPoint(14, 15),
                QPoint(11, 23)
            ])
            ptr_color = QColor(tmpl.get("color", "#7c3aed"))
            painter.setBrush(QBrush(ptr_color))
            painter.setPen(QPen(QColor("#ffffff"), 1.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawPolygon(pointer)

            # 2. Draw Badge Pill
            badge_rect = QRect(24, 16, 290, 28)
            badge_bg = QColor(tmpl.get("color", "#7c3aed"))
            badge_bg.setAlpha(225)
            painter.setBrush(QBrush(badge_bg))
            painter.setPen(QPen(QColor(tmpl.get("dot_color", "#a78bfa")), 1))
            painter.drawRoundedRect(badge_rect, 6, 6)

            # 3. Draw Glowing Dot
            painter.setBrush(QBrush(QColor(tmpl.get("dot_color", "#a78bfa"))))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPoint(34, 30), 3, 3)

            # 4. Draw Agent Icon & Name
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.setPen(QColor("#ffffff"))
            display_title = f"{tmpl.get('icon', '🤖')} {tmpl.get('name', 'Agent')}"
            painter.drawText(44, 34, display_title)

            # 5. Draw Action Chip
            if self.action_text:
                painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                painter.setPen(QColor(tmpl.get("accent", "#38bdf8")))
                painter.drawText(180, 34, f"• {self.action_text[:18]}")

except Exception:
    DesktopSystemCursorOverlay = None
