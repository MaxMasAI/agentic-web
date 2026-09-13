import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from browser.browser_helpers import is_matching_agent_page
from core.main import find_browser_executable
from core import agentlist

class TestBrowserAndExeFixes(unittest.TestCase):

    def test_agent_domain_matching(self):
        # Test all active agents to ensure their URLs match properly
        all_agents = agentlist.list_all_active_agents()
        for agent in all_agents:
            aid = agent["id"]
            url = agent["official_url"]
            self.assertTrue(
                is_matching_agent_page(url, aid, url),
                f"Agent '{aid}' with URL '{url}' should match itself"
            )

        # Test specific edge cases that previously failed
        self.assertTrue(is_matching_agent_page("https://www.meta.ai/chat/123", "meta_ai", "https://www.meta.ai"))
        self.assertTrue(is_matching_agent_page("https://chatgpt.com/c/abc", "dalle", "https://chatgpt.com/?model=dall-e-3"))
        self.assertTrue(is_matching_agent_page("https://build.nvidia.com/meta/llama-3", "nvidia_ai", "https://build.nvidia.com"))
        self.assertTrue(is_matching_agent_page("https://copilot.microsoft.com/chats/1", "copilot", "https://copilot.microsoft.com"))
        self.assertTrue(is_matching_agent_page("https://chat.deepseek.com", "deepseek", "https://chat.deepseek.com"))
        self.assertTrue(is_matching_agent_page("https://gemini.google.com/app", "gemini", "https://gemini.google.com/app"))

        # Test negative cases
        self.assertFalse(is_matching_agent_page("https://www.google.com", "deepseek", "https://chat.deepseek.com"))
        self.assertFalse(is_matching_agent_page("https://www.youtube.com", "meta_ai", "https://www.meta.ai"))

    def test_find_browser_executable(self):
        exe = find_browser_executable()
        self.assertIsNotNone(exe)
        self.assertTrue(len(exe) > 0)
        print(f"\n[Test] Detected browser executable: {exe}")

if __name__ == "__main__":
    unittest.main()
