"""
services/wikipedia_service.py - Wikipedia Plugin Engine
Provides multilingual Wikipedia search, summaries, detailed page contents, random article discovery,
geographic search, and browser opening.
"""

import os
import requests
import json
import webbrowser
import urllib.parse
from typing import Dict, List, Any, Optional

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "wikipedia_config.json")

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish (Español)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "pl": "Polish (Polski)",
    "it": "Italian (Italiano)",
    "pt": "Portuguese (Português)",
    "ja": "Japanese (日本語)",
    "zh": "Chinese (中文)",
    "ru": "Russian (Русский)",
    "ar": "Arabic (العربية)",
    "hi": "Hindi (हिन्दी)"
}


class WikipediaService:
    """
    Wikipedia API Client.
    Manages language preferences, article querying, page extraction, and coordinates discovery.
    """
    def __init__(self, language: str = "en", config_path: str = SETTINGS_FILE):
        self.config_path = config_path
        self.language = language
        self.load_config()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "AgenticWeb-Desktop/1.0 (WikipediaPlugin)"})

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.language = data.get("language", "en")
                    return
            except Exception:
                pass
        self.save_config()

    def save_config(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({"language": self.language}, f, indent=2)
        except Exception:
            pass

    def _api_url(self) -> str:
        return f"https://{self.language}.wikipedia.org/w/api.php"

    # 1. Set preferred language
    def set_language(self, lang_code: str) -> Dict[str, Any]:
        lang_code = lang_code.lower().strip()
        if lang_code in SUPPORTED_LANGUAGES:
            self.language = lang_code
            self.save_config()
            return {"success": True, "language": self.language, "name": SUPPORTED_LANGUAGES[self.language]}
        return {"success": False, "error": f"Unsupported language '{lang_code}'. Use list_supported_languages()."}

    # 2. Retrieve current language setting
    def get_language(self) -> Dict[str, Any]:
        return {"success": True, "language": self.language, "name": SUPPORTED_LANGUAGES.get(self.language, "Custom")}

    # 3. Explore list of supported languages
    def list_supported_languages(self) -> Dict[str, Any]:
        return {"success": True, "languages": SUPPORTED_LANGUAGES}

    # 4. Search for articles using keywords
    def search_articles(self, query: str, limit: int = 10) -> Dict[str, Any]:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json"
        }
        try:
            resp = self.session.get(self._api_url(), params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                for item in data.get("query", {}).get("search", []):
                    title = item.get("title", "")
                    clean_snippet = item.get("snippet", "").replace('<span class="searchmatch">', "").replace("</span>", "")
                    results.append({
                        "title": title,
                        "snippet": clean_snippet,
                        "pageid": item.get("pageid"),
                        "url": f"https://{self.language}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    })
                return {"success": True, "query": query, "total_hits": len(results), "results": results}
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 5. Obtain summaries and detailed page content
    def get_article_summary(self, title: str, sentences: int = 4) -> Dict[str, Any]:
        url = f"https://{self.language}.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title.replace(' ', '_'))}"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "title": data.get("title"),
                    "extract": data.get("extract", ""),
                    "description": data.get("description", ""),
                    "thumbnail": data.get("thumbnail", {}).get("source", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                }
            return {"success": False, "error": f"Article '{title}' not found (HTTP {resp.status_code})"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_article_content(self, title: str) -> Dict[str, Any]:
        params = {
            "action": "query",
            "prop": "extracts",
            "explaintext": True,
            "titles": title,
            "format": "json"
        }
        try:
            resp = self.session.get(self._api_url(), params=params, timeout=12)
            if resp.status_code == 200:
                pages = resp.json().get("query", {}).get("pages", {})
                for pid, pdata in pages.items():
                    if pid != "-1":
                        return {
                            "success": True,
                            "title": pdata.get("title"),
                            "pageid": pid,
                            "content": pdata.get("extract", ""),
                            "url": f"https://{self.language}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                        }
            return {"success": False, "error": f"Content for '{title}' not found."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 6. Discover random article
    def get_random_article(self) -> Dict[str, Any]:
        url = f"https://{self.language}.wikipedia.org/api/rest_v1/page/random/summary"
        try:
            resp = self.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "success": True,
                    "title": data.get("title"),
                    "extract": data.get("extract", ""),
                    "description": data.get("description", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                }
            return {"success": False, "error": f"Random article failed (HTTP {resp.status_code})"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 7. Discover articles by geographic location
    def get_nearby_articles(self, lat: float, lng: float, radius: int = 10000, limit: int = 10) -> Dict[str, Any]:
        params = {
            "action": "query",
            "list": "geosearch",
            "gscoord": f"{lat}|{lng}",
            "gsradius": radius,
            "gslimit": limit,
            "format": "json"
        }
        try:
            resp = self.session.get(self._api_url(), params=params, timeout=10)
            if resp.status_code == 200:
                places = resp.json().get("query", {}).get("geosearch", [])
                results = []
                for p in places:
                    title = p.get("title", "")
                    results.append({
                        "title": title,
                        "dist_meters": p.get("dist", 0),
                        "lat": p.get("lat"),
                        "lng": p.get("lon"),
                        "url": f"https://{self.language}.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
                    })
                return {"success": True, "coordinates": (lat, lng), "results": results}
            return {"success": False, "error": f"Geo search failed (HTTP {resp.status_code})"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 8. Open articles directly in web browser
    def open_in_browser(self, title_or_url: str) -> Dict[str, Any]:
        if title_or_url.startswith("http://") or title_or_url.startswith("https://"):
            target_url = title_or_url
        else:
            target_url = f"https://{self.language}.wikipedia.org/wiki/{urllib.parse.quote(title_or_url.replace(' ', '_'))}"
        try:
            webbrowser.open(target_url)
            return {"success": True, "url": target_url, "opened": True}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global Singleton Helper
_wiki_service: Optional[WikipediaService] = None

def get_wikipedia_service() -> WikipediaService:
    global _wiki_service
    if _wiki_service is None:
        _wiki_service = WikipediaService()
    return _wiki_service
