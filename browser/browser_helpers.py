import asyncio
import os
import sys
import urllib.parse

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"

AGENT_DOMAINS = {
    "gemini": ["gemini.google.com"],
    "deepseek": ["chat.deepseek.com", "deepseek.com"],
    "chatgpt": ["chatgpt.com", "openai.com"],
    "dalle": ["chatgpt.com", "openai.com"],
    "claude": ["claude.ai"],
    "meta_ai": ["meta.ai"],
    "perplexity": ["perplexity.ai"],
    "copilot": ["copilot.microsoft.com", "bing.com"],
    "nvidia_ai": ["build.nvidia.com", "nvidia.com"],
    "mistral": ["mistral.ai", "chat.mistral.ai"],
}


def is_matching_agent_page(page_url: str, url_keyword: str, direct_url: str = "") -> bool:
    """Checks whether a page URL matches a given agent ID or target URL."""
    if not page_url:
        return False
    
    p_url = page_url.lower()
    kw = url_keyword.lower().strip()
    
    # Check known domain mappings
    domains = AGENT_DOMAINS.get(kw, [])
    for d in domains:
        if d in p_url:
            return True
            
    # Check extracted netloc from direct_url
    if direct_url:
        try:
            parsed = urllib.parse.urlparse(direct_url)
            netloc = parsed.netloc.lower().replace("www.", "")
            if netloc and netloc in p_url:
                return True
        except Exception:
            pass

    # Normalized keyword check (e.g. meta_ai -> meta.ai or meta)
    clean_kw = kw.replace("_", ".")
    if clean_kw in p_url or kw.replace("_", "") in p_url:
        return True
        
    return False


async def _get_screen_size(context):
    try:
        page = context.pages[0]
        r = await page.evaluate("() => ({w: window.screen.availWidth, h: window.screen.availHeight})")
        return r["w"], r["h"]
    except Exception:
        return 1920, 1080


async def set_window_bounds(page, left, top, width, height):
    """Move and resize a Chrome window precisely via CDP."""
    try:
        client = await page.context.new_cdp_session(page)
        r = await client.send("Browser.getWindowForTarget")
        await client.send("Browser.setWindowBounds", {
            "windowId": r["windowId"],
            "bounds": {"left": int(left), "top": int(top),
                       "width": int(width), "height": int(height),
                       "windowState": "normal"}
        })
        await client.detach()
    except Exception as e:
        print(f"{YELLOW}  [window] setWindowBounds skipped: {e}{RESET}")


async def _get_window_id(context, page):
    """Return the CDP windowId for a given page, or None on failure."""
    try:
        client = await context.new_cdp_session(page)
        r = await client.send("Browser.getWindowForTarget")
        await client.detach()
        return r["windowId"]
    except Exception:
        return None


import json

async def set_page_agent_tab_header(page, agent_id: str):
    """
    Sets the document.title so the browser tab header and Alt-Tab window switcher
    prominently show the Agent's Name (e.g. ● Google Gemini • Agent).
    """
    if not page:
        return
    try:
        from core import agentlist
        agent_meta = agentlist.get_agent_by_id(agent_id)
        agent_name = agent_meta["name"] if agent_meta else agent_id.capitalize()
    except Exception:
        agent_name = agent_id.capitalize()

    js = f"""
    (() => {{
        const agentName = {json.dumps(agent_name)};
        const agentTag = `● ${{agentName}} • Agent`;
        
        function applyTitle() {{
            try {{
                if (!document.title.startsWith(`● ${{agentName}}`)) {{
                    const rawTitle = document.title.replace(/^●\\s*.*?\\s*•\\s*Agent\\s*\\|?\\s*/, '').trim();
                    document.title = rawTitle ? (`${{agentTag}} | ${{rawTitle}}`) : agentTag;
                }}
            }} catch(e) {{}}
        }}

        applyTitle();

        const titleEl = document.querySelector('title');
        if (titleEl && !window.__agent_title_observer_installed) {{
            window.__agent_title_observer_installed = true;
            const observer = new MutationObserver(() => {{
                applyTitle();
            }});
            observer.observe(titleEl, {{ subtree: true, characterData: true, childList: true }});
        }}

        if (!window.__agent_title_interval_installed) {{
            window.__agent_title_interval_installed = true;
            setInterval(applyTitle, 1500);
        }}
    }})();
    """
    try:
        await page.evaluate(js)
    except Exception:
        pass


async def get_or_open_tab(context, url_keyword, direct_url,
                          col_index=None, total_cols=None):
    """
    Opens or reuses a dedicated browser window for each agent.
    Checks chat_session_manager to always reuse the exact same conversation ID.
    """
    try:
        from utils.chat_session_manager import get_agent_chat_url
        target_url = get_agent_chat_url(url_keyword, direct_url)
    except Exception:
        target_url = direct_url

    if target_url != direct_url:
        print(f"{GREEN}  [Chat Tracker] Opening persisted Chat ID for '{url_keyword}' -> {target_url}{RESET}")

    # ── Tile geometry ──────────────────────────────────────────────────────
    screen_w, screen_h = await _get_screen_size(context)
    if col_index is not None and total_cols is not None and total_cols > 0:
        col_w = screen_w // total_cols
        win_left, win_top     = col_w * col_index, 0
        win_width, win_height = col_w, screen_h
    else:
        win_left, win_top     = 0, 0
        win_width, win_height = screen_w, screen_h

    # ── Look for an existing window for this agent ─────────────────────────
    for page in context.pages:
        if not is_matching_agent_page(page.url, url_keyword, direct_url):
            continue

        print(f"{GREEN}  [window] Found existing tab for '{url_keyword}' ({page.url[:45]}...){RESET}")
        try:
            await page.bring_to_front()
            await set_window_bounds(page, win_left, win_top, win_width, win_height)
            await set_page_agent_tab_header(page, url_keyword)
            await dismiss_sidebar_and_overlays(page, url_keyword)
            return page
        except Exception as e:
            print(f"{YELLOW}  [window] Could not activate existing tab for '{url_keyword}': {e}{RESET}")

    # ── Check if there is an unused blank initial tab to repurpose ────────
    for page in context.pages:
        if page.url in ["about:blank", "chrome://newtab/", "edge://newtab/"]:
            print(f"{CYAN}  [window] Repurposing blank tab for '{url_keyword}'...{RESET}")
            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=20000)
                await page.bring_to_front()
                await set_window_bounds(page, win_left, win_top, win_width, win_height)
                await set_page_agent_tab_header(page, url_keyword)
                await dismiss_sidebar_and_overlays(page, url_keyword)
                return page
            except Exception:
                pass

    # ── Open a brand-new dedicated window via CDP ──────────────────────────
    print(f"{CYAN}  [window] Opening new window for '{url_keyword}' at col {col_index}/{total_cols}...{RESET}")

    # Snapshot existing pages BEFORE we open anything
    pages_before = set(id(p) for p in context.pages)

    base_page = context.pages[0] if context.pages else None
    if base_page:
        try:
            cdp = await context.new_cdp_session(base_page)
            await cdp.send("Target.createTarget", {
                "url":       target_url,
                "newWindow": True,
                "width":     win_width,
                "height":    win_height,
            })
            await cdp.detach()
        except Exception as e:
            print(f"{YELLOW}  [window] Target.createTarget notice: {e}, falling back to new_page(){RESET}")
            new_p = await context.new_page()
            await new_p.goto(target_url, wait_until="domcontentloaded", timeout=20000)
            await set_window_bounds(new_p, win_left, win_top, win_width, win_height)
            await set_page_agent_tab_header(new_p, url_keyword)
            await dismiss_sidebar_and_overlays(new_p, url_keyword)
            return new_p

    # Poll until a genuinely new page appears in the context
    new_page = None
    for attempt in range(20):  # up to 10 seconds
        await asyncio.sleep(0.5)
        for p in context.pages:
            if id(p) not in pages_before:
                new_page = p
                break
        if new_page:
            break

    if new_page is None:
        # Last resort: find by matching domain/keyword
        for p in context.pages:
            if is_matching_agent_page(p.url, url_keyword, direct_url):
                new_page = p
                break

    if new_page is None:
        # Fallback to direct new page in context
        new_page = await context.new_page()
        await new_page.goto(target_url, wait_until="domcontentloaded", timeout=20000)

    try:
        await new_page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception:
        pass

    # Fine-tune position and bounds
    await set_window_bounds(new_page, win_left, win_top, win_width, win_height)
    await set_page_agent_tab_header(new_page, url_keyword)
    await dismiss_sidebar_and_overlays(new_page, url_keyword)
    
    # Inject Antigravity-styled agent cursor overlay
    try:
        from browser.agent_cursor import inject_agent_cursor
        await inject_agent_cursor(new_page, agent_name=url_keyword)
    except Exception:
        pass

    print(f"{GREEN}  [window] '{url_keyword}' window ready with Antigravity Agent Cursor at x={win_left} w={win_width}{RESET}")
    return new_page


async def dismiss_sidebar_and_overlays(page, agent_id: str = ""):
    """
    Automatically detects and closes pop-up drawers, sidebars, and overlay modals
    (such as the Gemini left navigation drawer with '✕' button, ChatGPT sidebar, Claude drawer)
    so they never obstruct the conversation or input box.
    """
    if not page:
        return
    try:
        from browser.agent_cursor import simulate_agent_dismiss_sidebar
        await simulate_agent_dismiss_sidebar(page, agent_id or "Gemini")
    except Exception:
        pass

    try:
        await page.evaluate("""
        (() => {
            // 1. Target specific close / collapse buttons
            const closeSelectors = [
                "button[aria-label*='Collapse' i]",
                "button[aria-label*='Close' i]",
                "button[aria-label*='close' i]",
                "button[aria-label*='Hide side' i]",
                "button[aria-label*='Dismiss' i]",
                "button[data-test-id*='close' i]",
                "button[data-test-id*='collapse' i]",
                ".mat-drawer-close-button",
                "button.close-button",
                "button[aria-label='Main menu'][aria-expanded='true']"
            ];
            
            for (const sel of closeSelectors) {
                const elements = document.querySelectorAll(sel);
                for (const el of elements) {
                    if (el && el.offsetParent !== null) {
                        try { el.click(); } catch(e) {}
                    }
                }
            }

            // 2. Scan buttons with close icon or text inside navigation drawers/sidebars
            const drawerButtons = Array.from(document.querySelectorAll("mat-drawer button, [class*='drawer' i] button, [class*='sidebar' i] button, nav button, header button"));
            for (const btn of drawerButtons) {
                const txt = (btn.innerText || '').trim();
                const aria = (btn.getAttribute('aria-label') || '').toLowerCase();
                if (txt === '✕' || txt === '×' || txt.toLowerCase() === 'close' || aria.includes('close') || aria.includes('collapse') || aria.includes('main menu')) {
                    if (btn.offsetParent !== null) {
                        try { btn.click(); } catch(e) {}
                    }
                }
            }

            // 3. Click backdrop overlay if active and covering the viewport
            const backdrops = document.querySelectorAll("mat-drawer-backdrop.mat-drawer-shown, .mat-drawer-backdrop, div[class*='backdrop'][class*='show'], div[class*='drawer-mask'], div[data-testid='dialog-overlay']");
            for (const bd of backdrops) {
                if (bd.offsetParent !== null) {
                    try { bd.click(); } catch(e) {}
                }
            }
        })();
        """)
    except Exception:
        pass

    try:
        await page.keyboard.press("Escape")
    except Exception:
        pass


async def scroll_chat(page, direction: str = "bottom", amount: int = None):
    """
    Scrolls the active chat conversation container or page smoothly.
    Supports 'bottom', 'top', 'down', 'up'.
    """
    if not page:
        return
    try:
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
    except Exception:
        pass


async def wait_until_text_settles(locator, page=None, check_interval=None, max_cycles=None):
    """Polls a locator until the AI stops streaming text, with live auto-scrolling."""
    try:
        from utils.latency_manager import load_latency_config
        cfg = load_latency_config()
        if check_interval is None:
            check_interval = cfg.get("check_interval_sec", 1.5)
        if max_cycles is None:
            total_sec = cfg.get("max_timeout_sec", 120)
            max_cycles = max(10, int(total_sec / check_interval))
    except Exception:
        if check_interval is None:
            check_interval = 1.5
        if max_cycles is None:
            max_cycles = 80

    target_page = page or getattr(locator, "page", None)
    last_text = ""
    for _ in range(max_cycles):
        await asyncio.sleep(check_interval)
        if target_page:
            try:
                await scroll_chat(target_page, "bottom")
            except Exception:
                pass
        try:
            current_text = await locator.inner_text()
            if current_text and current_text == last_text:
                if target_page:
                    await scroll_chat(target_page, "bottom")
                return current_text.strip()
            last_text = current_text
        except Exception:
            continue
    if target_page:
        try:
            await scroll_chat(target_page, "bottom")
        except Exception:
            pass
    return last_text.strip()


