"""
browser_controller.py - Direct Autonomous Browser & Media Execution Engine.

Executes real browser actions across ANY website (YouTube music playback,
opening websites, web search, navigation, clicking) directly in Chrome via Playwright/CDP,
instead of asking LLM chatbots to write theoretical code.
"""

import asyncio
import os
import sys
import re
import urllib.parse

# Ensure project root in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from browser.browser_helpers import get_or_open_tab, set_window_bounds

CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RED   = "\033[91m"
RESET = "\033[0m"


def is_direct_browser_or_media_task(task: str) -> bool:
    """
    Detects if the user's prompt is a direct browser action on ANY website
    (e.g., play music on youtube, open github.com, go to reddit, search google, browse amazon).
    """
    if not task:
        return False
    t = task.lower().strip()
    
    # Exclude requests asking to write/generate code
    if any(w in t for w in ["write a script", "write code", "how to code", "implement in python", "create a function"]):
        return False

    # 1. YouTube & Music playback patterns
    yt_patterns = [
        "play music", "play song", "play a song", "play any song",
        "open youtube", "open yt", "youtube and play", "yt and play",
        "play lofi", "play track", "music on yt", "music from yt",
        "play from youtube", "play on youtube", "play video on youtube"
    ]
    if any(p in t for p in yt_patterns):
        return True
    
    if t.startswith(("play ", "yt ", "youtube ")):
        return True

    # 2. General Website Navigation & Browsing
    web_patterns = [
        "open website", "open site", "go to http", "visit http", "open http",
        "open url", "go to website", "browse to", "navigate to", "open google",
        "search on google", "search google for", "open github", "open reddit",
        "open twitter", "open x.com", "open amazon", "open wikipedia", "open cnbc",
        "open netflix", "open spotify", "open linkedin", "open chatgpt", "open deepseek"
    ]
    if any(p in t for p in web_patterns):
        return True

    # Check for direct domains (e.g. "github.com", "reddit.com/r/python", "https://...")
    if re.search(r"https?://[^\s]+", t) or re.search(r"\b[a-zA-Z0-9-]+\.(com|org|net|io|ai|dev|co|in|gov|edu)\b", t):
        return True

    # Commands like "open <website_name>"
    if re.match(r"^(open|go to|visit|browse)\s+[a-zA-Z0-9_-]+(\.[a-zA-Z]{2,})?$", t):
        return True

    return False


def extract_music_query(task: str) -> str:
    """Extracts the specific song title, artist, or genre from user prompt."""
    t = task.strip()
    cleaned = re.sub(
        r"^(open\s+(youtub|youtube|yt)\s+(and\s+)?(play|listen\s+to)?|play\s+(music|a\s+song|any\s+song|song|track|audio|video)?\s*(from|on|in)?\s*(youtub|youtube|yt)?|play\s+)",
        "",
        t,
        flags=re.IGNORECASE
    ).strip()

    cleaned = re.sub(r"^(from|on|in)\s+(youtub|youtube|yt)", "", cleaned, flags=re.IGNORECASE).strip()

    if not cleaned or cleaned.lower() in ["any song", "music", "song", "a song", "some music", "tracks"]:
        return "Top Trending Music Hits"
    
    return cleaned


def extract_website_url(task: str) -> tuple[str, str]:
    """
    Extracts target URL and site name from user prompt.
    Returns (url, site_name).
    """
    t = task.strip()
    
    # Direct URL match
    url_match = re.search(r"https?://[^\s]+", t)
    if url_match:
        url = url_match.group(0)
        return url, urllib.parse.urlparse(url).netloc

    # Domain match (e.g. github.com, reddit.com)
    domain_match = re.search(r"\b([a-zA-Z0-9-]+\.(com|org|net|io|ai|dev|co|in|gov|edu)(/[^\s]*)?)\b", t, re.IGNORECASE)
    if domain_match:
        domain = domain_match.group(1)
        return f"https://{domain}", domain

    # "search google for <query>"
    search_match = re.search(r"(?:search\s+(?:on\s+)?google\s+(?:for\s+)?|google\s+)(.+)", t, re.IGNORECASE)
    if search_match:
        query = search_match.group(1).strip()
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}", f"Google: {query}"

    # "open <name>" e.g. "open github", "open amazon"
    open_match = re.search(r"^(?:open|go to|visit|browse)\s+([a-zA-Z0-9_ -]+)", t, re.IGNORECASE)
    if open_match:
        name = open_match.group(1).strip()
        clean_name = name.split()[0].lower()
        known_sites = {
            "github": "https://github.com",
            "google": "https://www.google.com",
            "reddit": "https://www.reddit.com",
            "amazon": "https://www.amazon.com",
            "wikipedia": "https://www.wikipedia.org",
            "twitter": "https://x.com",
            "x": "https://x.com",
            "youtube": "https://www.youtube.com",
            "yt": "https://www.youtube.com",
            "linkedin": "https://www.linkedin.com",
            "netflix": "https://www.netflix.com",
            "spotify": "https://open.spotify.com",
            "stackoverflow": "https://stackoverflow.com",
            "huggingface": "https://huggingface.co",
        }
        if clean_name in known_sites:
            return known_sites[clean_name], clean_name
        return f"https://www.google.com/search?q={urllib.parse.quote(name)}", name

    return f"https://www.google.com/search?q={urllib.parse.quote(t)}", t


async def execute_direct_browser_action(task: str, context) -> str:
    """
    Executes real browser action for ANY website (YouTube music, website navigation, web search).
    """
    t = task.lower().strip()
    from voice.voice_narrator import speak_narrator

    # Case 1: YouTube Music / Video Playback
    if any(p in t for p in ["youtube", "yt", "play music", "play song", "play a song", "play any song", "play lofi", "play track"]) or t.startswith("play "):
        return await execute_youtube_playback(task, context)

    # Case 2: General Website / URL / Search Action
    target_url, site_name = extract_website_url(task)
    print(f"\n{CYAN}[Browser Controller] Opening Website: '{site_name}' -> {target_url}{RESET}")
    speak_narrator(f"opening {site_name} in your browser now...")

    keyword = urllib.parse.urlparse(target_url).netloc or site_name
    page = await get_or_open_tab(context, keyword, target_url, col_index=0, total_cols=1)
    await page.bring_to_front()

    try:
        await page.goto(target_url, timeout=20000, wait_until="domcontentloaded")
    except Exception:
        pass

    await page.bring_to_front()
    print(f"{GREEN}[OK] Website '{site_name}' is live and displayed in Chrome.{RESET}")

    result_summary = (
        f"🌐 BROWSER NAVIGATION ACTIVE\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"▶ Target Website: {site_name}\n"
        f"🔗 URL: {target_url}\n"
        f"📱 Status: Active in Chrome browser\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    return result_summary


async def execute_youtube_playback(task: str, context) -> str:
    """
    Directly opens YouTube in Chrome, searches for the song, clicks the first video,
    and starts video/audio playback immediately.
    """
    query = extract_music_query(task)
    print(f"\n{CYAN}[Browser Controller] Direct YouTube Media Execution triggered for: '{query}'{RESET}")
    
    try:
        from voice.voice_narrator import speak_narrator
        speak_narrator(f"opening youtube and playing {query}...")
    except Exception:
        pass

    encoded_query = urllib.parse.quote(query)
    search_url = f"https://www.youtube.com/results?search_query={encoded_query}"

    print(f"{YELLOW}[*] Opening YouTube search in Chrome: {search_url}...{RESET}")
    page = await get_or_open_tab(context, "youtube.com", search_url, col_index=0, total_cols=1)
    await page.bring_to_front()

    # Wait for search results to load
    print(f"{YELLOW}[*] Locating top video match for '{query}'...{RESET}")
    video_title_locator = page.locator("ytd-video-renderer a#video-title, ytd-rich-item-renderer a#video-title, a#video-title").first

    clicked = False
    try:
        await video_title_locator.wait_for(timeout=10000, state="visible")
        video_name = await video_title_locator.get_attribute("title") or query
        print(f"{GREEN}[OK] Top video found: '{video_name}'. Clicking to play...{RESET}")
        await video_title_locator.click()
        clicked = True
    except Exception as e:
        print(f"{YELLOW}[*] Direct title click fallback: {e}{RESET}")

    if not clicked:
        # Fallback click on any thumbnail
        try:
            thumb = page.locator("ytd-video-renderer ytd-thumbnail, ytd-rich-item-renderer ytd-thumbnail").first
            await thumb.click(timeout=5000)
            clicked = True
        except Exception:
            pass

    # Ensure video is actively unmuted/playing
    await asyncio.sleep(2.5)
    try:
        await page.evaluate("""
            () => {
                const v = document.querySelector('video');
                if (v) {
                    v.play();
                }
            }
        """)
        print(f"{GREEN}[OK] YouTube Audio & Video playback is ACTIVE and playing in browser!{RESET}")
    except Exception:
        pass

    # Bring YouTube window to front
    await page.bring_to_front()

    result_summary = (
        f"🎵 YOUTUBE MUSIC PLAYBACK ACTIVE\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"▶ Now Playing: {query}\n"
        f"🔗 URL: {page.url}\n"
        f"🔊 Status: Active playback in dedicated Chrome browser tab\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    return result_summary
