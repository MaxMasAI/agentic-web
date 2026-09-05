"""
services/bitbucket_service.py - Bitbucket Cloud API Plugin & Service Integration
Manages repositories, file source trees, issues, and pull requests via Bitbucket Cloud API v2.0.
"""

import os
import requests
import json
from typing import Dict, List, Any, Optional, Union

BITBUCKET_API_BASE = "https://api.bitbucket.org/2.0"
CREDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "bitbucket_creds.json")


class BitbucketService:
    """
    Bitbucket Cloud API Client.
    Supports App Passwords (username + token), Personal Access Tokens, and OAuth Bearer Tokens.
    """
    def __init__(
        self,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
        bearer_token: Optional[str] = None
    ):
        self.username = username or os.environ.get("BITBUCKET_USERNAME", "")
        self.app_password = app_password or os.environ.get("BITBUCKET_APP_PASSWORD", "")
        self.bearer_token = bearer_token or os.environ.get("BITBUCKET_BEARER_TOKEN", "")
        
        # Load from credentials file if available
        if not (self.username or self.bearer_token) and os.path.exists(CREDS_FILE):
            try:
                with open(CREDS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.username = data.get("username", "")
                    self.app_password = data.get("app_password", "")
                    self.bearer_token = data.get("bearer_token", "")
            except Exception:
                pass

        self.session = requests.Session()
        self._setup_auth()

    def _setup_auth(self):
        if self.bearer_token:
            self.session.headers.update({"Authorization": f"Bearer {self.bearer_token}"})
        elif self.username and self.app_password:
            self.session.auth = (self.username, self.app_password)
        self.session.headers.update({"Accept": "application/json"})

    def save_credentials(self, username: str = "", app_password: str = "", bearer_token: str = ""):
        self.username = username
        self.app_password = app_password
        self.bearer_token = bearer_token
        self._setup_auth()
        
        os.makedirs(os.path.dirname(CREDS_FILE), exist_ok=True)
        try:
            with open(CREDS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "username": self.username,
                    "app_password": self.app_password,
                    "bearer_token": self.bearer_token
                }, f, indent=2)
        except Exception:
            pass

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{BITBUCKET_API_BASE}/{endpoint.lstrip('/')}"
        try:
            resp = self.session.request(method, url, timeout=15, **kwargs)
            if resp.status_code in (200, 201):
                try:
                    return {"success": True, "status_code": resp.status_code, "data": resp.json()}
                except Exception:
                    return {"success": True, "status_code": resp.status_code, "data": resp.text}
            elif resp.status_code == 204:
                return {"success": True, "status_code": 204, "message": "Action completed successfully (No Content)."}
            else:
                try:
                    err_data = resp.json()
                    err_msg = err_data.get("error", {}).get("message", resp.text)
                except Exception:
                    err_msg = resp.text
                return {"success": False, "status_code": resp.status_code, "error": err_msg}
        except Exception as e:
            return {"success": False, "error": f"HTTP Request failed: {str(e)}"}

    # 1. Authenticated User Details
    def get_authenticated_user(self) -> Dict[str, Any]:
        return self._request("GET", "/user")

    # 2. Specific User Info
    def get_user(self, user_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/users/{user_id}")

    # 3. List Workspaces
    def list_workspaces(self) -> Dict[str, Any]:
        return self._request("GET", "/workspaces")

    # 4. List Repositories in a Workspace
    def list_repositories(self, workspace: str) -> Dict[str, Any]:
        return self._request("GET", f"/repositories/{workspace}")

    # 5. Specific Repository Details
    def get_repository(self, workspace: str, repo_slug: str) -> Dict[str, Any]:
        return self._request("GET", f"/repositories/{workspace}/{repo_slug}")

    # 6. Create New Repository
    def create_repository(
        self,
        workspace: str,
        repo_slug: str,
        is_private: bool = True,
        description: str = "",
        project_key: Optional[str] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "scm": "git",
            "is_private": is_private,
            "description": description
        }
        if project_key:
            payload["project"] = {"key": project_key}
        return self._request("POST", f"/repositories/{workspace}/{repo_slug}", json=payload)

    # 7. Delete Repository
    def delete_repository(self, workspace: str, repo_slug: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/repositories/{workspace}/{repo_slug}")

    # 8. Retrieve File Contents
    def get_file_content(self, workspace: str, repo_slug: str, file_path: str, commit: str = "main") -> Dict[str, Any]:
        url = f"{BITBUCKET_API_BASE}/repositories/{workspace}/{repo_slug}/src/{commit}/{file_path.lstrip('/')}"
        try:
            resp = self.session.get(url, timeout=15)
            if resp.status_code == 200:
                return {"success": True, "content": resp.text, "status_code": 200}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 9. Upload File to Repository
    def upload_file(
        self,
        workspace: str,
        repo_slug: str,
        file_path: str,
        content: str,
        commit_message: str = "Update file via Bitbucket API"
    ) -> Dict[str, Any]:
        data = {
            "message": commit_message,
            file_path.lstrip('/'): content
        }
        return self._request("POST", f"/repositories/{workspace}/{repo_slug}/src", data=data)

    # 10. Delete File from Repository
    def delete_file(
        self,
        workspace: str,
        repo_slug: str,
        file_path: str,
        commit_message: str = "Delete file via Bitbucket API"
    ) -> Dict[str, Any]:
        data = {
            "message": commit_message,
            "files": file_path.lstrip('/')
        }
        return self._request("POST", f"/repositories/{workspace}/{repo_slug}/src", data=data)

    # 11. List Issues
    def list_issues(self, workspace: str, repo_slug: str, state: str = "OPEN") -> Dict[str, Any]:
        params = {"q": f'state="{state}"'} if state else {}
        return self._request("GET", f"/repositories/{workspace}/{repo_slug}/issues", params=params)

    # 12. Create Issue
    def create_issue(
        self,
        workspace: str,
        repo_slug: str,
        title: str,
        description: str = "",
        priority: str = "major",
        kind: str = "bug"
    ) -> Dict[str, Any]:
        payload = {
            "title": title,
            "content": {"raw": description},
            "priority": priority,
            "kind": kind
        }
        return self._request("POST", f"/repositories/{workspace}/{repo_slug}/issues", json=payload)

    # 13. Comment on Issue
    def comment_issue(self, workspace: str, repo_slug: str, issue_id: Union[int, str], comment_text: str) -> Dict[str, Any]:
        payload = {"content": {"raw": comment_text}}
        return self._request("POST", f"/repositories/{workspace}/{repo_slug}/issues/{issue_id}/comments", json=payload)

    # 14. Update Issue Details
    def update_issue(self, workspace: str, repo_slug: str, issue_id: Union[int, str], updates: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/repositories/{workspace}/{repo_slug}/issues/{issue_id}", json=updates)

    # 15. List Pull Requests
    def list_pull_requests(self, workspace: str, repo_slug: str, state: str = "OPEN") -> Dict[str, Any]:
        params = {"state": state} if state else {}
        return self._request("GET", f"/repositories/{workspace}/{repo_slug}/pullrequests", params=params)

    # 16. Create Pull Request
    def create_pull_request(
        self,
        workspace: str,
        repo_slug: str,
        title: str,
        source_branch: str,
        destination_branch: str = "main",
        description: str = ""
    ) -> Dict[str, Any]:
        payload = {
            "title": title,
            "description": description,
            "source": {"branch": {"name": source_branch}},
            "destination": {"branch": {"name": destination_branch}}
        }
        return self._request("POST", f"/repositories/{workspace}/{repo_slug}/pullrequests", json=payload)

    # 17. Merge Pull Request
    def merge_pull_request(
        self,
        workspace: str,
        repo_slug: str,
        pr_id: Union[int, str],
        message: str = "Merged via Bitbucket API",
        close_source_branch: bool = True
    ) -> Dict[str, Any]:
        payload = {
            "message": message,
            "close_source_branch": close_source_branch,
            "merge_strategy": "merge_commit"
        }
        return self._request("POST", f"/repositories/{workspace}/{repo_slug}/pullrequests/{pr_id}/merge", json=payload)

    # 18. Search Repositories
    def search_repositories(self, workspace: Optional[str] = None, query: str = "") -> Dict[str, Any]:
        endpoint = f"/repositories/{workspace}" if workspace else "/repositories"
        params = {}
        if query:
            params["q"] = f'name ~ "{query}"'
        return self._request("GET", endpoint, params=params)


# Singleton Helper
_bb_service: Optional[BitbucketService] = None

def get_bitbucket_service() -> BitbucketService:
    global _bb_service
    if _bb_service is None:
        _bb_service = BitbucketService()
    return _bb_service
