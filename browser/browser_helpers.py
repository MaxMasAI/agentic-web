import asyncio

CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"

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
            "bounds": {"left": left, "top": top,
                       "width": width, "height": height,
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


async def get_or_open_tab(context, url_keyword, direct_url,
                          col_index=None, total_cols=None):
    """
    Opens a dedicated browser window for each agent.
    Checks chat_session_manager to always reuse the exact same single conversation ID
    under "Collaborative AI review framework assignment".
    """
    try:
        from chat_session_manager import get_agent_chat_url
        target_url = get_agent_chat_url(url_keyword, direct_url)
    except Exception:
        target_url = direct_url

    if target_url != direct_url:
        print(f"{GREEN}  [Chat Tracker] Opening persisted Chat ID for '{url_keyword}' -> {target_url}{RESET}")

    # ── Tile geometry ──────────────────────────────────────────────────────
    screen_w, screen_h = await _get_screen_size(context)
    if col_index is not None and total_cols is not None:
        col_w = screen_w // total_cols
        win_left, win_top     = col_w * col_index, 0
        win_width, win_height = col_w, screen_h
    else:
        win_left, win_top     = 0, 0
        win_width, win_height = screen_w, screen_h

    # ── Look for an existing STANDALONE window for this agent ──────────────
    for page in context.pages:
        if url_keyword not in page.url:
            continue

        my_win = await _get_window_id(context, page)
        if my_win is None:
            continue

        # Count tabs that share the same window
        siblings = 0
        for other in context.pages:
            if other is page:
                continue
            other_win = await _get_window_id(context, other)
            if other_win == my_win:
                siblings += 1

        if siblings == 0:
            # Already a standalone window — reuse & reposition
            print(f"{GREEN}  [window] Reusing standalone window for '{url_keyword}'{RESET}")
            await page.bring_to_front()
            await set_window_bounds(page, win_left, win_top, win_width, win_height)
            return page

        # Page exists but shares a window with other tabs — open a fresh window
        print(f"{YELLOW}  [window] '{url_keyword}' is a shared tab "
              f"({siblings} siblings) — opening new dedicated window{RESET}")
        break

    # ── Open a brand-new dedicated window via CDP ──────────────────────────
    print(f"{CYAN}  [window] Opening new window for '{url_keyword}' "
          f"at col {col_index}/{total_cols}...{RESET}")

    # Snapshot existing pages BEFORE we open anything
    pages_before = set(id(p) for p in context.pages)

    base_page = context.pages[0]
    cdp = await context.new_cdp_session(base_page)
    try:
        await cdp.send("Target.createTarget", {
            "url":       target_url,
            "newWindow": True,
            "width":     win_width,
            "height":    win_height,
        })
    except Exception as e:
        print(f"{RED}  [window] Target.createTarget failed: {e}{RESET}")
        raise
    finally:
        await cdp.detach()

    # Poll until a genuinely new page appears in the context
    new_page = None
    for attempt in range(20):          # up to 10 seconds
        await asyncio.sleep(0.5)
        for p in context.pages:
            if id(p) not in pages_before:
                new_page = p
                break
        if new_page:
            break

    if new_page is None:
        # Last resort: find by URL keyword (may have loaded by now)
        for p in context.pages:
            if url_keyword in p.url:
                new_page = p
                break

    if new_page is None:
        raise RuntimeError(
            f"[window] Failed to open a new window for '{url_keyword}'. "
            f"Chrome may have blocked the new-window request."
        )

    try:
        await new_page.wait_for_load_state("domcontentloaded", timeout=15000)
    except Exception:
        pass  # Page may still be loading — continue anyway

    # Fine-tune position (createTarget sets size but not always left offset)
    await set_window_bounds(new_page, win_left, win_top, win_width, win_height)
    print(f"{GREEN}  [window] '{url_keyword}' window ready at "
          f"x={win_left} w={win_width}{RESET}")
    return new_page


async def wait_until_text_settles(locator, check_interval=None, max_cycles=None):
    """Polls a locator until the AI stops streaming text using dynamic latency manager."""
    try:
        from latency_manager import load_latency_config
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

    last_text = ""
    for _ in range(max_cycles):
        await asyncio.sleep(check_interval)
        try:
            current_text = await locator.inner_text()
            if current_text and current_text == last_text:
                return current_text.strip()
            last_text = current_text
        except Exception:
            continue
    return last_text.strip()
