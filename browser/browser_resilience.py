"""
browser/browser_resilience.py - Self-Healing & Decoupled Browser Automation Engine.

Provides automated fallback to headless Playwright worker contexts if the localized
Chrome CDP instance on port 9222 is closed, disconnected, or crashes.
"""

import sys
import asyncio
from typing import Optional, Tuple, Any

CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RESET = "\033[0m"


class ResilientBrowserManager:
    """
    Manages browser connections with automatic reconnection and headless fallback.
    """
    def __init__(self, cdp_port: int = 9222):
        self.cdp_port = cdp_port
        self._browser = None
        self._context = None
        self._is_fallback_headless = False

    async def get_or_create_context(self, playwright_instance, force_headless: bool = False):
        """
        Attempts to connect to live Chrome CDP on port 9222.
        If unavailable or disconnected, seamlessly launches an isolated headless Chromium worker.
        """
        if not force_headless:
            try:
                self._browser = await playwright_instance.chromium.connect_over_cdp(
                    f"http://127.0.0.1:{self.cdp_port}",
                    timeout=4000
                )
                self._context = self._browser.contexts[0] if self._browser.contexts else await self._browser.new_context()
                self._is_fallback_headless = False
                return self._context, "cdp_attached"
            except Exception as e:
                print(f"{YELLOW}[BrowserResilience] CDP port {self.cdp_port} unavailable ({e}) -> Activating Headless Worker Fallback...{RESET}")

        # Headless Multi-Tenant Fallback
        self._browser = await playwright_instance.chromium.launch(
            headless=True,
            args=[
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-gpu",
                "--disable-background-networking"
            ]
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
        )
        self._is_fallback_headless = True
        print(f"{GREEN}[BrowserResilience] Isolated Headless Chromium worker active.{RESET}")
        return self._context, "headless_fallback"

    async def close(self):
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass


# Global Singleton Helper
_global_browser_resilience: Optional[ResilientBrowserManager] = None

def get_browser_resilience_manager(cdp_port: int = 9222) -> ResilientBrowserManager:
    global _global_browser_resilience
    if _global_browser_resilience is None:
        _global_browser_resilience = ResilientBrowserManager(cdp_port=cdp_port)
    return _global_browser_resilience
