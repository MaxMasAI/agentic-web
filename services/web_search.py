"""
services/web_search.py - Multi-Engine Real-Time Web Search Plugin
Integrates Google Custom Search Engine (CSE), Microsoft Bing API, and DuckDuckGo for live grounded search.
"""

import os
import urllib.parse
import requests
import json
import re
from typing import Dict, List, Any, Optional

from services.llm_provider import load_api_keys

SEARCH_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "web_search_config.json")


class SearchProvider:
    DUCKDUCKGO = "duckduckgo"
    GOOGLE = "google"
    BING = "bing"


class WebSearchService:
    """
    Real-Time Web Search Engine.
    Supports Google Custom Search, Microsoft Bing API, and DuckDuckGo.
    """
    def __init__(self, default_provider: str = SearchProvider.DUCKDUCKGO):
        self.default_provider = default_provider
        self.google_cse_id = os.environ.get("GOOGLE_CSE_ID", "")
        self.bing_api_key = os.environ.get("BING_API_KEY") or os.environ.get("AZURE_BING_KEY", "")
        self.load_config()

    def load_config(self):
        if os.path.exists(SEARCH_CONFIG_FILE):
            try:
                with open(SEARCH_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.default_provider = data.get("default_provider", SearchProvider.DUCKDUCKGO)
                    if not self.google_cse_id:
                        self.google_cse_id = data.get("google_cse_id", "")
                    if not self.bing_api_key:
                        self.bing_api_key = data.get("bing_api_key", "")
            except Exception:
                pass

    def save_config(self, default_provider: Optional[str] = None, google_cse_id: Optional[str] = None, bing_api_key: Optional[str] = None):
        if default_provider:
            self.default_provider = default_provider
        if google_cse_id:
            self.google_cse_id = google_cse_id
        if bing_api_key:
            self.bing_api_key = bing_api_key

        os.makedirs(os.path.dirname(SEARCH_CONFIG_FILE), exist_ok=True)
        try:
            with open(SEARCH_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "default_provider": self.default_provider,
                    "google_cse_id": self.google_cse_id,
                    "bing_api_key": self.bing_api_key
                }, f, indent=2)
        except Exception:
            pass

    def search(self, query: str, max_results: int = 5, provider: Optional[str] = None) -> List[Dict[str, str]]:
        chosen = (provider or self.default_provider).lower()

        if chosen == SearchProvider.GOOGLE and self.google_cse_id:
            return self._search_google_cse(query, max_results)
        elif chosen == SearchProvider.BING and self.bing_api_key:
            return self._search_bing(query, max_results)
        
        return self._search_duckduckgo(query, max_results)

    def _search_google_cse(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        api_key = load_api_keys().get("gemini") or os.environ.get("GOOGLE_API_KEY", "")
        if not (api_key and self.google_cse_id):
            return self._search_duckduckgo(query, max_results)

        url = "https://www.googleapis.com/customsearch/v1"
        params = {"key": api_key, "cx": self.google_cse_id, "q": query, "num": max_results}
        try:
            resp = requests.get(url, params=params, timeout=8)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                return [{"title": i.get("title", ""), "url": i.get("link", ""), "snippet": i.get("snippet", "")} for i in items]
        except Exception:
            pass
        return self._search_duckduckgo(query, max_results)

    def _search_bing(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        if not self.bing_api_key:
            return self._search_duckduckgo(query, max_results)

        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {"Ocp-Apim-Subscription-Key": self.bing_api_key}
        params = {"q": query, "count": max_results}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=8)
            if resp.status_code == 200:
                values = resp.json().get("webPages", {}).get("value", [])
                return [{"title": v.get("name", ""), "url": v.get("url", ""), "snippet": v.get("snippet", "")} for v in values]
        except Exception:
            pass
        return self._search_duckduckgo(query, max_results)

    def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        if not query.strip():
            return []

        results = []
        try:
            # DuckDuckGo Instant Answer API
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
            resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            if resp.status_code == 200:
                data = resp.json()
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading", query),
                        "url": data.get("AbstractURL", "https://duckduckgo.com"),
                        "snippet": data.get("AbstractText", "")
                    })
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("FirstURL", "").split("/")[-1].replace("_", " "),
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", "")
                        })
        except Exception:
            pass

        # HTML Lite Search Fallback
        if len(results) < 2:
            try:
                lite_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
                resp = requests.get(lite_url, timeout=5, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                if resp.status_code == 200:
                    snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', resp.text, re.DOTALL)
                    titles = re.findall(r'<a class="result__url[^>]*href="([^"]*)"[^>]*>(.*?)</a>', resp.text, re.DOTALL)
                    for i in range(min(len(snippets), max_results)):
                        s_clean = re.sub(r"<[^>]+>", "", snippets[i]).strip()
                        url_val = titles[i][0] if i < len(titles) else "#"
                        title_val = re.sub(r"<[^>]+>", "", titles[i][1]).strip() if i < len(titles) else f"Result #{i+1}"
                        if s_clean:
                            results.append({
                                "title": title_val,
                                "url": url_val,
                                "snippet": s_clean
                            })
            except Exception:
                pass

        return results[:max_results]


# Standalone function export for backward compatibility
def search_duckduckgo(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    return get_web_search_service().search(query, max_results=max_results, provider=SearchProvider.DUCKDUCKGO)


# Global Singleton Helper
_search_service: Optional[WebSearchService] = None

def get_web_search_service() -> WebSearchService:
    global _search_service
    if _search_service is None:
        _search_service = WebSearchService()
    return _search_service
