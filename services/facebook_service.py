"""
services/facebook_service.py - Facebook Graph API Plugin & Service Integration
Manages Facebook OAuth2, pages, posts, and media uploads via Facebook Graph API v19.0+.
"""

import os
import requests
import json
from typing import Dict, List, Any, Optional, Union

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
CREDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "facebook_creds.json")


class FacebookService:
    """
    Facebook Graph API Client.
    Supports User Access Tokens, Page Access Tokens, and OAuth2 token exchange.
    """
    def __init__(
        self,
        user_access_token: Optional[str] = None,
        default_page_id: Optional[str] = None
    ):
        self.user_access_token = user_access_token or os.environ.get("FACEBOOK_USER_TOKEN", "")
        self.default_page_id = default_page_id or os.environ.get("FACEBOOK_DEFAULT_PAGE_ID", "")
        self.page_tokens: Dict[str, str] = {}
        
        self.load_credentials()

    def load_credentials(self):
        if os.path.exists(CREDS_FILE):
            try:
                with open(CREDS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if not self.user_access_token:
                        self.user_access_token = data.get("user_access_token", "")
                    if not self.default_page_id:
                        self.default_page_id = data.get("default_page_id", "")
                    self.page_tokens = data.get("page_tokens", {})
            except Exception:
                pass

    def save_credentials(
        self,
        user_access_token: Optional[str] = None,
        default_page_id: Optional[str] = None,
        page_tokens: Optional[Dict[str, str]] = None
    ):
        if user_access_token is not None:
            self.user_access_token = user_access_token
        if default_page_id is not None:
            self.default_page_id = default_page_id
        if page_tokens is not None:
            self.page_tokens = page_tokens

        os.makedirs(os.path.dirname(CREDS_FILE), exist_ok=True)
        try:
            with open(CREDS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "user_access_token": self.user_access_token,
                    "default_page_id": self.default_page_id,
                    "page_tokens": self.page_tokens
                }, f, indent=2)
        except Exception:
            pass

    def _get_page_token(self, page_id: str) -> Optional[str]:
        if page_id in self.page_tokens:
            return self.page_tokens[page_id]
        
        # Query accounts to fetch page token dynamically
        pages_res = self.list_pages()
        if pages_res.get("success"):
            for p in pages_res.get("data", {}).get("data", []):
                pid = p.get("id")
                token = p.get("access_token")
                if pid and token:
                    self.page_tokens[pid] = token
            self.save_credentials()
            return self.page_tokens.get(page_id)
        return self.user_access_token

    # 1. Retrieve basic information about the authenticated user
    def get_user_info(self) -> Dict[str, Any]:
        if not self.user_access_token:
            return {"success": False, "error": "No user access token configured"}
        url = f"{GRAPH_API_BASE}/me"
        params = {
            "fields": "id,name,email,picture",
            "access_token": self.user_access_token
        }
        try:
            resp = requests.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json()}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 2. List all Facebook pages the user has access to
    def list_pages(self) -> Dict[str, Any]:
        if not self.user_access_token:
            return {"success": False, "error": "No user access token configured"}
        url = f"{GRAPH_API_BASE}/me/accounts"
        params = {"access_token": self.user_access_token}
        try:
            resp = requests.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                for p in data.get("data", []):
                    pid = p.get("id")
                    token = p.get("access_token")
                    if pid and token:
                        self.page_tokens[pid] = token
                self.save_credentials()
                return {"success": True, "data": data}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 3. Set a specified Facebook page as the default
    def set_default_page(self, page_id: str) -> Dict[str, Any]:
        self.default_page_id = page_id
        self.save_credentials(default_page_id=page_id)
        return {"success": True, "message": f"Default page set to '{page_id}'", "default_page_id": page_id}

    # 4. Retrieve a list of posts from a Facebook page
    def get_page_posts(self, page_id: Optional[str] = None, limit: int = 25) -> Dict[str, Any]:
        pid = page_id or self.default_page_id
        if not pid:
            return {"success": False, "error": "No page ID provided and no default page configured"}
        token = self._get_page_token(pid)
        url = f"{GRAPH_API_BASE}/{pid}/feed"
        params = {
            "fields": "id,message,created_time,full_picture,shares,likes.summary(true),comments.summary(true)",
            "limit": limit,
            "access_token": token
        }
        try:
            resp = requests.get(url, params=params, timeout=12)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json()}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 5. Create a new post on a Facebook page
    def create_page_post(
        self,
        message: str,
        page_id: Optional[str] = None,
        link: Optional[str] = None
    ) -> Dict[str, Any]:
        pid = page_id or self.default_page_id
        if not pid:
            return {"success": False, "error": "No page ID provided and no default page configured"}
        token = self._get_page_token(pid)
        url = f"{GRAPH_API_BASE}/{pid}/feed"
        payload = {
            "message": message,
            "access_token": token
        }
        if link:
            payload["link"] = link
        try:
            resp = requests.post(url, data=payload, timeout=15)
            if resp.status_code in (200, 201):
                return {"success": True, "data": resp.json()}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 6. Delete a post from a Facebook page
    def delete_page_post(self, post_id: str, page_id: Optional[str] = None) -> Dict[str, Any]:
        pid = page_id or self.default_page_id
        token = self._get_page_token(pid) if pid else self.user_access_token
        url = f"{GRAPH_API_BASE}/{post_id}"
        params = {"access_token": token}
        try:
            resp = requests.delete(url, params=params, timeout=12)
            if resp.status_code == 200:
                return {"success": True, "message": f"Post '{post_id}' deleted successfully.", "data": resp.json()}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 7. Upload a photo to a Facebook page
    def upload_photo(
        self,
        image_path_or_url: str,
        caption: str = "",
        page_id: Optional[str] = None
    ) -> Dict[str, Any]:
        pid = page_id or self.default_page_id
        if not pid:
            return {"success": False, "error": "No page ID provided and no default page configured"}
        token = self._get_page_token(pid)
        url = f"{GRAPH_API_BASE}/{pid}/photos"

        # Case A: URL upload
        if image_path_or_url.startswith("http://") or image_path_or_url.startswith("https://"):
            payload = {
                "url": image_path_or_url,
                "caption": caption,
                "access_token": token
            }
            try:
                resp = requests.post(url, data=payload, timeout=20)
                if resp.status_code in (200, 201):
                    return {"success": True, "data": resp.json()}
                return {"success": False, "status_code": resp.status_code, "error": resp.text}
            except Exception as e:
                return {"success": False, "error": str(e)}

        # Case B: Local file upload
        if not os.path.exists(image_path_or_url):
            return {"success": False, "error": f"Local image file '{image_path_or_url}' not found."}

        try:
            with open(image_path_or_url, "rb") as img_f:
                files = {"source": img_f}
                data = {"caption": caption, "access_token": token}
                resp = requests.post(url, data=data, files=files, timeout=30)
                if resp.status_code in (200, 201):
                    return {"success": True, "data": resp.json()}
                return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global Singleton Helper
_fb_service: Optional[FacebookService] = None

def get_facebook_service() -> FacebookService:
    global _fb_service
    if _fb_service is None:
        _fb_service = FacebookService()
    return _fb_service
