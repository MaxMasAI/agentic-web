"""
browser/agent_cursor.py - Antigravity Multi-Agent Visual Cursor Overlay & Telemetry Engine
Renders a live Antigravity-styled collaborative cursor with arrow pointer and
'[Agent Name] • agent' rounded pill badge on top of browser pages and WebViews.
"""

import asyncio
import json
from typing import Optional, Tuple, Dict, Any

# Standard Agent Theme Colors (Default: Antigravity Forest Green #2e6f54)
AGENT_CURSOR_COLORS: Dict[str, str] = {
    "atlas": "#2e6f54",
    "web_agent": "#06b6d4",    # Cyber Cyan / Full Screen Overseer
    "web-agent": "#06b6d4",
    "gemini": "#1e6b52",       # Antigravity Green / Google Gemini
    "deepseek": "#1e40af",     # Deep Blue / Researcher
    "chatgpt": "#047857",      # Emerald / OpenAI
    "claude": "#c2410c",       # Warm Ochre / Anthropic
    "perplexity": "#0891b2",   # Cyan / Perplexity
    "meta_ai": "#4338ca",      # Indigo / Meta
    "copilot": "#0284c7",      # Sky Blue / Microsoft
    "nvidia_ai": "#15803d",    # Bright Green / Nvidia
    "mistral": "#ea580c",      # Amber Flame / Mistral
    "dalle": "#7c3aed",        # Purple / Creative
}

# CSS & JavaScript payload for Antigravity styled agent cursor
ANTIGRAVITY_CURSOR_JS = """
(function() {
    if (window.__agentic_cursor_installed) return;
    window.__agentic_cursor_installed = true;

    // Inject CSS styles for the Antigravity Agent Cursor & Screen Management HUD
    const style = document.createElement('style');
    style.id = 'agentic-antigravity-cursor-style';
    style.textContent = `
        #agentic-cursor-wrapper {
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

        .agentic-cursor-pointer {
            position: absolute;
            top: -2px;
            left: -2px;
            width: 24px;
            height: 24px;
            filter: drop-shadow(0 2px 5px rgba(0, 0, 0, 0.45));
            transform-origin: 0 0;
            transition: transform 0.1s ease;
        }

        .agentic-cursor-badge {
            position: absolute;
            left: 14px;
            top: 14px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #2e6f54;
            color: #ffffff;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.3px;
            padding: 4px 10px;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.2);
            white-space: nowrap;
            line-height: 1.2;
            animation: agentic-badge-fade-in 0.2s ease-out;
            border: 1px solid rgba(255, 255, 255, 0.15);
        }

        .agentic-cursor-dot {
            width: 6px;
            height: 6px;
            background-color: #4ade80;
            border-radius: 50%;
            box-shadow: 0 0 6px #4ade80;
            animation: agentic-pulse 1.5s infinite;
        }

        .agentic-action-chip {
            background: rgba(0, 0, 0, 0.35);
            font-size: 10.5px;
            font-weight: 600;
            padding: 2px 7px;
            border-radius: 4px;
            color: #86efac;
            margin-left: 4px;
            display: none;
            letter-spacing: 0.2px;
            box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.4);
        }

        .agentic-cursor-ripple {
            position: absolute;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            border: 2px solid #06b6d4;
            transform: translate(-50%, -50%) scale(0.2);
            opacity: 1;
            pointer-events: none;
            animation: agentic-ripple-wave 0.5s cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
        }

        #agentic-screen-highlight {
            position: fixed;
            border: 2px solid #06b6d4;
            background: rgba(6, 182, 212, 0.12);
            border-radius: 6px;
            z-index: 2147483640;
            pointer-events: none;
            display: none;
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.45), inset 0 0 10px rgba(6, 182, 212, 0.2);
            transition: all 0.2s ease;
        }

        .agentic-screen-sweep-line {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 3px;
            background: linear-gradient(90deg, transparent, #06b6d4, #38bdf8, transparent);
            box-shadow: 0 0 16px #38bdf8;
            z-index: 2147483645;
            pointer-events: none;
            animation: agentic-sweep-anim 1.2s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }

        @keyframes agentic-sweep-anim {
            0% { top: 0%; opacity: 0; }
            20% { opacity: 1; }
            80% { opacity: 1; }
            100% { top: 100%; opacity: 0; }
        }

        @keyframes agentic-pulse {
            0% { transform: scale(0.9); opacity: 0.8; }
            50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 10px #4ade80; }
            100% { transform: scale(0.9); opacity: 0.8; }
        }

        @keyframes agentic-ripple-wave {
            0% { transform: translate(-50%, -50%) scale(0.2); opacity: 1; }
            100% { transform: translate(-50%, -50%) scale(2.2); opacity: 0; }
        }

        @keyframes agentic-badge-fade-in {
            from { opacity: 0; transform: translateY(4px) scale(0.95); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
    `;
    document.head.appendChild(style);

    // Create Main Cursor Container
    const wrapper = document.createElement('div');
    wrapper.id = 'agentic-cursor-wrapper';
    wrapper.innerHTML = `
        <svg class="agentic-cursor-pointer" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M5.65376 12.3673H5.46026L5.31717 12.4976L0.500002 16.8829L0.500002 1.19841L11.7841 12.3673H5.65376Z" 
                  fill="#ffffff" stroke="#164e37" stroke-width="1.2"/>
        </svg>
        <div class="agentic-cursor-badge" id="agentic-cursor-badge">
            <div class="agentic-cursor-dot"></div>
            <span id="agentic-cursor-name">Atlas • agent</span>
            <span class="agentic-action-chip" id="agentic-cursor-action"></span>
        </div>
    `;
    document.body.appendChild(wrapper);

    // Global Cursor Controller
    window.__agentic_cursor = {
        x: 100,
        y: 100,
        setPosition: function(x, y) {
            this.x = x;
            this.y = y;
            wrapper.style.transform = `translate(${x}px, ${y}px)`;
        },
        setAgent: function(name, color = '#2e6f54', role = 'agent') {
            const badge = document.getElementById('agentic-cursor-badge');
            const nameEl = document.getElementById('agentic-cursor-name');
            if (badge) badge.style.backgroundColor = color;
            if (nameEl) nameEl.textContent = `${name} • ${role}`;
        },
        setAction: function(actionText) {
            const actionEl = document.getElementById('agentic-cursor-action');
            if (actionEl) {
                if (actionText) {
                    actionEl.textContent = actionText;
                    actionEl.style.display = 'inline-block';
                } else {
                    actionEl.style.display = 'none';
                }
            }
        },
        pulseClick: function(x = null, y = null) {
            const posX = x !== null ? x : this.x;
            const posY = y !== null ? y : this.y;
            
            const ripple = document.createElement('div');
            ripple.className = 'agentic-cursor-ripple';
            ripple.style.left = `${posX}px`;
            ripple.style.top = `${posY}px`;
            document.body.appendChild(ripple);
            
            const pointer = wrapper.querySelector('.agentic-cursor-pointer');
            if (pointer) {
                pointer.style.transform = 'scale(0.85)';
                setTimeout(() => { pointer.style.transform = 'scale(1)'; }, 150);
            }

            setTimeout(() => {
                if (ripple.parentNode) ripple.parentNode.removeChild(ripple);
            }, 600);
        },
        show: function() {
            wrapper.style.display = 'block';
        },
        hide: function() {
            wrapper.style.display = 'none';
        },
        highlightRegion: function(x, y, width, height, label = '') {
            let box = document.getElementById('agentic-screen-highlight');
            if (!box) {
                box = document.createElement('div');
                box.id = 'agentic-screen-highlight';
                document.body.appendChild(box);
            }
            box.style.left = `${x}px`;
            box.style.top = `${y}px`;
            box.style.width = `${width}px`;
            box.style.height = `${height}px`;
            box.style.display = 'block';
        },
        clearHighlight: function() {
            const box = document.getElementById('agentic-screen-highlight');
            if (box) box.style.display = 'none';
        },
        screenSweep: function() {
            const sweep = document.createElement('div');
            sweep.className = 'agentic-screen-sweep-line';
            document.body.appendChild(sweep);
            setTimeout(() => { if (sweep.parentNode) sweep.parentNode.removeChild(sweep); }, 1200);
        }
    };

    // Follow native mouse move if in interactive testing mode
    document.addEventListener('mousemove', function(e) {
        window.__agentic_cursor.setPosition(e.clientX, e.clientY);
    });

    console.log('[AgenticWeb] Antigravity Agent Cursor initialized.');
})();
"""


async def inject_agent_cursor(page, agent_name: str = "Gemini", agent_color: Optional[str] = None, agent_role: str = "agent"):
    """
    Injects the Antigravity cursor script and sets up the active agent's name badge & theme color.
    """
    if not page:
        return
    
    clean_id = agent_name.lower().replace(" ", "_")
    color = agent_color or AGENT_CURSOR_COLORS.get(clean_id, "#2e6f54")
    
    try:
        # 1. Inject script if not already present
        await page.evaluate(ANTIGRAVITY_CURSOR_JS)
        
        # 2. Configure Agent metadata
        escaped_name = json.dumps(agent_name.capitalize())
        escaped_color = json.dumps(color)
        escaped_role = json.dumps(agent_role)
        
        await page.evaluate(f"""
            if (window.__agentic_cursor) {{
                window.__agentic_cursor.setAgent({escaped_name}, {escaped_color}, {escaped_role});
                window.__agentic_cursor.show();
            }}
        """)
    except Exception as e:
        # Non-fatal if page navigation occurs simultaneously
        pass


async def set_cursor_action(page, action_text: str = ""):
    """Updates the action chip badge next to the agent cursor (e.g., 'Typing...', 'Clicking...')."""
    if not page:
        return
    try:
        escaped_action = json.dumps(action_text)
        await page.evaluate(f"""
            if (window.__agentic_cursor) {{
                window.__agentic_cursor.setAction({escaped_action});
            }}
        """)
    except Exception:
        pass


async def animate_agent_cursor_move(page, target_x: float, target_y: float, steps: int = 12):
    """
    Glides the Antigravity agent cursor smoothly across the browser viewport towards target coordinates.
    """
    if not page:
        return
    try:
        current_pos = await page.evaluate("""
            () => window.__agentic_cursor ? {x: window.__agentic_cursor.x, y: window.__agentic_cursor.y} : {x: 100, y: 100}
        """)
        start_x = current_pos.get("x", 100)
        start_y = current_pos.get("y", 100)

        for i in range(1, steps + 1):
            t = i / steps
            # Smooth ease-out cubic interpolation
            ease = 1 - (1 - t) ** 3
            cx = start_x + (target_x - start_x) * ease
            cy = start_y + (target_y - start_y) * ease
            await page.evaluate(f"""
                if (window.__agentic_cursor) {{
                    window.__agentic_cursor.setPosition({cx}, {cy});
                }}
            """)
            await asyncio.sleep(0.015)
    except Exception:
        pass


async def simulate_agent_click(page, selector: Optional[str] = None, x: Optional[float] = None, y: Optional[float] = None, agent_name: str = "Gemini"):
    """
    Visually moves the Antigravity agent cursor to the element or coordinates,
    pulses the radar wave click ripple, and triggers the action.
    """
    if not page:
        return

    await inject_agent_cursor(page, agent_name)
    await set_cursor_action(page, "⚡ Clicking...")

    target_x = x
    target_y = y

    if selector and (target_x is None or target_y is None):
        try:
            loc = page.locator(selector).first
            box = await loc.bounding_box()
            if box:
                target_x = box["x"] + box["width"] / 2
                target_y = box["y"] + box["height"] / 2
        except Exception:
            pass

    if target_x is not None and target_y is not None:
        await animate_agent_cursor_move(page, target_x, target_y)
        await page.evaluate(f"""
            if (window.__agentic_cursor) {{
                window.__agentic_cursor.pulseClick({target_x}, {target_y});
            }}
        """)
        await asyncio.sleep(0.15)

    await set_cursor_action(page, "")


async def simulate_agent_type(page, selector: str, text: str, agent_name: str = "Gemini"):
    """
    Moves Antigravity cursor to the target input element, shows the typing indicator badge,
    and fills the text.
    """
    if not page:
        return

    await inject_agent_cursor(page, agent_name)
    await set_cursor_action(page, "✍️ Typing...")

    try:
        loc = page.locator(selector).first
        box = await loc.bounding_box()
        if box:
            tx = box["x"] + 20
            ty = box["y"] + box["height"] / 2
            await animate_agent_cursor_move(page, tx, ty)
            await page.evaluate(f"""
                if (window.__agentic_cursor) {{
                    window.__agentic_cursor.pulseClick({tx}, {ty});
                }}
            """)
    except Exception:
        pass

    await asyncio.sleep(0.1)
    await set_cursor_action(page, "🤖 Processing...")


async def simulate_agent_dismiss_sidebar(page, agent_name: str = "Gemini"):
    """
    Empowers the Antigravity agent cursor to visually detect the pop-up drawer / sidebar close '✕' button,
    glide over to it, pulse a click ripple, and close the sidebar smoothly.
    """
    if not page:
        return
    
    try:
        await inject_agent_cursor(page, agent_name)
        
        # Detect if any drawer/sidebar close button or backdrop is active
        btn_info = await page.evaluate("""
        (() => {
            const selectors = [
                "button[aria-label*='Collapse' i]",
                "button[aria-label*='Close' i]",
                "button[aria-label*='close' i]",
                "button[data-test-id*='close' i]",
                ".mat-drawer-close-button",
                "button[aria-label='Main menu'][aria-expanded='true']"
            ];
            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.offsetParent !== null) {
                    const rect = el.getBoundingClientRect();
                    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, found: true };
                }
            }
            
            // Check drawer buttons with '✕' or close icon
            const drawerButtons = Array.from(document.querySelectorAll("mat-drawer button, [class*='drawer' i] button, [class*='sidebar' i] button, nav button, header button"));
            for (const btn of drawerButtons) {
                const txt = (btn.innerText || '').trim();
                const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                if (txt === '✕' || txt === '×' || txt.toLowerCase() === 'close' || aria.includes('close') || aria.includes('collapse')) {
                    if (btn.offsetParent !== null) {
                        const rect = btn.getBoundingClientRect();
                        return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, found: true };
                    }
                }
            }
            return { found: false };
        })();
        """)

        if btn_info and btn_info.get("found"):
            tx = btn_info["x"]
            ty = btn_info["y"]
            await set_cursor_action(page, "🎯 Closing Sidebar...")
            await animate_agent_cursor_move(page, tx, ty, steps=10)
            await page.evaluate(f"""
                if (window.__agentic_cursor) {{
                    window.__agentic_cursor.pulseClick({tx}, {ty});
                }}
            """)
            await asyncio.sleep(0.12)
            await set_cursor_action(page, "")
    except Exception:
        pass


async def simulate_agent_scroll_chat(page, direction: str = "bottom", agent_name: str = "Gemini"):
    """
    Empowers the Antigravity agent cursor to visually scroll the chat up or down.
    """
    if not page:
        return
    try:
        await inject_agent_cursor(page, agent_name)
        action_label = "📜 Scrolling down..." if direction in ["bottom", "down"] else "📜 Scrolling up..."
        await set_cursor_action(page, action_label)
        
        # Smoothly scroll the page/container
        await page.evaluate(f"""
        (() => {{
            const dir = {json.dumps(direction)};
            const scrollContainers = [
                document.querySelector("div[class*='conversation' i]"),
                document.querySelector("div[class*='chat-history' i]"),
                document.querySelector("div[class*='messages' i]"),
                document.querySelector("div[class*='chat' i][class*='scroll' i]"),
                document.querySelector("main"),
                document.querySelector("infinite-scroller"),
                document.querySelector(".chat-container"),
                document.scrollingElement || document.documentElement || document.body
            ].filter(Boolean);

            for (const el of scrollContainers) {{
                try {{
                    if (dir === 'bottom') {{
                        el.scrollTo({{ top: el.scrollHeight, behavior: 'smooth' }});
                    }} else if (dir === 'top') {{
                        el.scrollTo({{ top: 0, behavior: 'smooth' }});
                    }} else if (dir === 'down') {{
                        el.scrollBy({{ top: 400, behavior: 'smooth' }});
                    }} else if (dir === 'up') {{
                        el.scrollBy({{ top: -400, behavior: 'smooth' }});
                    }}
                }} catch(e) {{}}
            }}
            if (dir === 'bottom') {{
                window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }});
            }} else if (dir === 'top') {{
                window.scrollTo({{ top: 0, behavior: 'smooth' }});
            }}
        }})();
        """)
        await asyncio.sleep(0.15)
        await set_cursor_action(page, "")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# 🌐 WEB-AGENT: FULL-SCREEN AUTONOMOUS OVERSEER & SCREEN CONTROLLER
# ═══════════════════════════════════════════════════════════════════════════════

async def inject_web_agent_cursor(page, action_text: str = "🌐 Managing Screen..."):
    """
    Injects and activates the master 'Web-Agent' cursor with cyber-cyan theme
    and screen management powers over the entire browser viewport.
    """
    if not page:
        return
    try:
        await inject_agent_cursor(page, agent_name="Web-Agent", agent_color="#06b6d4", agent_role="Screen Overseer")
        if action_text:
            await set_cursor_action(page, action_text)
    except Exception:
        pass


async def web_agent_screen_sweep(page, sweep_text: str = "📡 Full-Screen Telemetry Scan..."):
    """
    Performs a high-tech full screen radar sweep across the entire display.
    """
    if not page:
        return
    try:
        await inject_web_agent_cursor(page, action_text=sweep_text)
        await page.evaluate("""
            if (window.__agentic_cursor) {
                window.__agentic_cursor.screenSweep();
            }
        """)
        # Glide cursor across screen diagonal to simulate full visual oversight
        await animate_agent_cursor_move(page, 150, 150, steps=6)
        await animate_agent_cursor_move(page, 800, 500, steps=8)
        await asyncio.sleep(0.2)
        await set_cursor_action(page, "✓ Screen Audited")
    except Exception:
        pass


async def web_agent_manage_screen(page, target_selector: Optional[str] = None, x: Optional[float] = None, y: Optional[float] = None, action_label: str = "🎯 Screen Action..."):
    """
    Empowers Web-Agent to locate any element across the screen, highlight it with a neon bounding box,
    glide to it, and execute a screen interaction with full visual feedback.
    """
    if not page:
        return
    
    try:
        await inject_web_agent_cursor(page, action_text=action_label)
        
        target_x, target_y = x, y
        if target_selector and (target_x is None or target_y is None):
            loc = page.locator(target_selector).first
            box = await loc.bounding_box()
            if box:
                target_x = box["x"] + box["width"] / 2
                target_y = box["y"] + box["height"] / 2
                
                # Draw neon bounding box highlight over the element
                await page.evaluate(f"""
                    if (window.__agentic_cursor) {{
                        window.__agentic_cursor.highlightRegion({box['x']}, {box['y']}, {box['width']}, {box['height']}, {json.dumps(action_label)});
                    }}
                """)

        if target_x is not None and target_y is not None:
            await animate_agent_cursor_move(page, target_x, target_y, steps=10)
            await page.evaluate(f"""
                if (window.__agentic_cursor) {{
                    window.__agentic_cursor.pulseClick({target_x}, {target_y});
                }}
            """)
            await asyncio.sleep(0.15)
            # Clear highlight after interaction
            await page.evaluate("""
                if (window.__agentic_cursor) {
                    window.__agentic_cursor.clearHighlight();
                }
            """)
    except Exception:
        pass


async def web_agent_scroll_screen(page, direction: str = "down", amount: int = 500):
    """
    Empowers Web-Agent to smoothly scroll the entire web page viewport up or down.
    """
    if not page:
        return
    try:
        await inject_web_agent_cursor(page, action_text=f"📜 Scrolling Screen {direction.upper()}...")
        await page.evaluate(f"""
            (() => {{
                const dir = {json.dumps(direction)};
                const amt = {amount};
                if (dir === 'down' || dir === 'bottom') {{
                    window.scrollBy({{ top: amt, behavior: 'smooth' }});
                }} else {{
                    window.scrollBy({{ top: -amt, behavior: 'smooth' }});
                }}
            }})();
        """)
        await asyncio.sleep(0.2)
        await set_cursor_action(page, "")
    except Exception:
        pass


