"""
test_live_browser_e2e.py - Live Browser End-to-End Integration Test.
Connects to the running Chrome on port 9222, opens real AI windows,
tiles them across your screen, and verifies DOM elements live.
"""

import sys
import os
import asyncio
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from playwright.async_api import async_playwright
from core import agentlist
from browser.browser_helpers import get_or_open_tab

class TestLiveBrowserE2E(unittest.IsolatedAsyncioTestCase):

    async def test_live_chrome_multi_agent_tiling(self):
        """Connects to live Chrome on port 9222 and opens 3 agents side-by-side."""
        print("\n\n[*] Connecting to live Chrome browser on port 9222...")
        
        async with async_playwright() as p:
            try:
                browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            except Exception as e:
                raise unittest.SkipTest(f"Chrome remote debugging port 9222 is not currently running. Error: {e}")
                
            context = browser.contexts[0]
            self.assertGreater(len(context.pages), 0, "Chrome should have at least 1 open tab.")

            # Test agents: Gemini (Leader), DeepSeek (Worker 1), ChatGPT (Worker 2)
            test_agents = [
                agentlist.get_leader(),
                agentlist.get_agent_by_id("deepseek"),
                agentlist.get_agent_by_id("chatgpt")
            ]
            total_cols = len(test_agents)

            print(f"[*] Opening and tiling {total_cols} AI agent windows across screen...")
            tabs = {}
            for col_idx, agent in enumerate(test_agents):
                print(f"  -> Launching [{agent['name']}] at column {col_idx+1}/{total_cols}...")
                tab = await get_or_open_tab(
                    context,
                    agent["id"],
                    agent["official_url"],
                    col_index=col_idx,
                    total_cols=total_cols
                )
                tabs[agent["id"]] = tab
                self.assertIsNotNone(tab, f"Failed to get or open tab for {agent['name']}")
                self.assertIn(agent["id"], tab.url.lower(), f"Tab URL '{tab.url}' does not match expected agent '{agent['id']}'")
                await tab.bring_to_front()

            print("[✓] All 3 live agent browser windows opened and verified side-by-side!")

if __name__ == "__main__":
    unittest.main()
