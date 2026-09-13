"""
services/tab_screenshot_service.py - Multi-Tab High-Resolution Screenshot Engine.

Captures screenshots of all open browser tabs/windows, labels each with its sanitized
tab/agent name, and stores the image files in the project 'images/' directory.
"""

import os
import sys
import re
import time
import asyncio
from typing import List, Dict, Any, Optional

# Default output directory in project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")


def sanitize_tab_filename(raw_name: str) -> str:
    """
    Cleans raw tab titles or agent headers for safe cross-platform file naming.
    Example: '● Google Gemini • Agent | Studio' -> 'Google_Gemini_Agent_Studio'
    """
    if not raw_name:
        return "Browser_Tab"
    
    # Strip bullet dots, agent glyphs, and special characters
    cleaned = raw_name.replace("●", "").replace("•", "").replace("|", "_").replace("-", "_")
    cleaned = re.sub(r"[<>:\"/\\?*~`!@#$%^&()+=;{}[\]]", "", cleaned)
    cleaned = re.sub(r"\s+", "_", cleaned).strip("_")
    cleaned = re.sub(r"_+", "_", cleaned)
    
    if not cleaned:
        return f"Tab_{int(time.time())}"
    return cleaned[:60]


async def capture_all_tabs_screenshots(
    context=None,
    pages: Optional[List[Any]] = None,
    output_dir: str = DEFAULT_IMAGES_DIR,
    include_timestamp: bool = False
) -> List[Dict[str, Any]]:
    """
    Captures screenshots of all active browser tabs/pages, naming each file after
    the tab's agent/page name and saving them into the 'images/' folder.

    Args:
        context: Playwright BrowserContext (optional).
        pages: List of Playwright Page objects (optional).
        output_dir: Destination directory (defaults to 'images/').
        include_timestamp: Whether to append a timestamp to the filename.

    Returns:
        List of dicts with metadata for each saved screenshot:
        [{ 'tab_name': ..., 'title': ..., 'url': ..., 'file_path': ..., 'file_name': ... }, ...]
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    # Connect to running CDP session if no context or pages are provided
    standalone_browser = None
    if not pages:
        if context and context.pages:
            pages = context.pages
        else:
            try:
                from playwright.async_api import async_playwright
                playwright = await async_playwright().start()
                standalone_browser = await playwright.chromium.connect_over_cdp("http://127.0.0.1:9222")
                if standalone_browser.contexts:
                    pages = standalone_browser.contexts[0].pages
            except Exception as e:
                print(f"[!] Could not connect to browser CDP on port 9222: {e}")
                pages = []

    if not pages:
        print("[!] No active browser tabs found to screenshot.")
        return results

    ts = time.strftime("%Y%m%d_%H%M%S")
    print(f"\n[*] Capturing high-resolution screenshots of {len(pages)} open tab(s) to '{output_dir}'...")

    for idx, page in enumerate(pages, 1):
        try:
            # 1. Retrieve Tab Title and URL
            title = await page.title() or f"Tab_{idx}"
            url = page.url or ""
            
            # Derive meaningful name from title or domain
            tab_name = sanitize_tab_filename(title)
            if tab_name.lower() in ["tab", "browser_tab", "new_tab", "chrome"]:
                if url:
                    import urllib.parse
                    domain = urllib.parse.urlparse(url).netloc.replace("www.", "")
                    if domain:
                        tab_name = sanitize_tab_filename(domain)

            # 2. Formulate target filename
            if include_timestamp:
                filename = f"{tab_name}_{ts}.png"
            else:
                filename = f"{tab_name}.png"

            file_path = os.path.join(output_dir, filename)

            # Handle duplicate filenames in same batch
            counter = 1
            base_name = os.path.splitext(filename)[0]
            while os.path.exists(file_path):
                file_path = os.path.join(output_dir, f"{base_name}_{counter}.png")
                filename = os.path.basename(file_path)
                counter += 1

            # 3. Capture screenshot
            await page.bring_to_front()
            await asyncio.sleep(0.1)
            await page.screenshot(path=file_path, full_page=False)

            info = {
                "tab_index": idx,
                "tab_name": tab_name,
                "title": title,
                "url": url,
                "file_path": file_path,
                "file_name": filename,
                "timestamp": ts,
            }
            results.append(info)
            print(f"  [+] Saved Tab #{idx} ['{tab_name}'] -> images/{filename}")
        except Exception as e:
            print(f"  [!] Failed to screenshot Tab #{idx}: {e}")

    if standalone_browser:
        try:
            await standalone_browser.close()
        except Exception:
            pass

    print(f"[OK] Successfully captured {len(results)} tab screenshot(s) in '{output_dir}'.\n")
    return results


def capture_all_tabs_sync(output_dir: str = DEFAULT_IMAGES_DIR, include_timestamp: bool = False) -> List[Dict[str, Any]]:
    """Synchronous entry point for capturing all tab screenshots."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, capture_all_tabs_screenshots(output_dir=output_dir, include_timestamp=include_timestamp)).result()
        else:
            return loop.run_until_complete(capture_all_tabs_screenshots(output_dir=output_dir, include_timestamp=include_timestamp))
    except Exception:
        return asyncio.run(capture_all_tabs_screenshots(output_dir=output_dir, include_timestamp=include_timestamp))


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_IMAGES_DIR
    res = capture_all_tabs_sync(output_dir=out_dir)
    print(f"Captured {len(res)} screenshots.")
