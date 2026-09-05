"""
services/github_service.py - GitHub REST API Plugin & Service Integration
Manages GitHub repositories, file source trees, issues, pull requests, and search queries via GitHub API v3.
"""

import os
import requests
import json
import base64
from typing import Dict, List, Any, Optional, Union

GITHUB_API_BASE = "https://api.github.com"
CREDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "github_creds.json")


class GitHubService:
    """
    GitHub REST API Client.
    Supports Personal Access Tokens (PAT), OAuth Bearer Tokens, and Device Flow tokens.
    """
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PAT", "")
        self.load_credentials()
        self.session = requests.Session()
        self._setup_headers()

    def _setup_headers(self):
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgenticWeb-Desktop/1.0"
        })
        if self.token:
            self.session.headers.update({"Authorization": f"token {self.token}"})

    def load_credentials(self):
        if not self.token and os.path.exists(CREDS_FILE):
            try:
                with open(CREDS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.token = data.get("token", "")
            except Exception:
                pass

    def save_credentials(self, token: str):
        self.token = token
        self._setup_headers()
        os.makedirs(os.path.dirname(CREDS_FILE), exist_ok=True)
        try:
            with open(CREDS_FILE, "w", encoding="utf-8") as f:
                json.dump({"token": self.token}, f, indent=2)
        except Exception:
            pass

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{GITHUB_API_BASE}/{endpoint.lstrip('/')}"
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
                    err_json = resp.json()
                    err_msg = err_json.get("message", resp.text)
                except Exception:
                    err_msg = resp.text
                return {"success": False, "status_code": resp.status_code, "error": err_msg}
        except Exception as e:
            return {"success": False, "error": f"HTTP Request failed: {str(e)}"}

    # 1. Retrieve details about your GitHub profile
    def get_authenticated_user(self) -> Dict[str, Any]:
        return self._request("GET", "/user")

    # 2. Get information about a specific GitHub user
    def get_user(self, username: str) -> Dict[str, Any]:
        return self._request("GET", f"/users/{username}")

    # 3. List repositories for a user or organization
    def list_repositories(self, user_or_org: Optional[str] = None, is_org: bool = False) -> Dict[str, Any]:
        if not user_or_org:
            return self._request("GET", "/user/repos", params={"sort": "updated", "per_page": 100})
        if is_org:
            return self._request("GET", f"/orgs/{user_or_org}/repos", params={"sort": "updated", "per_page": 100})
        return self._request("GET", f"/users/{user_or_org}/repos", params={"sort": "updated", "per_page": 100})

    # 4. Retrieve details about a specific repository
    def get_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        return self._request("GET", f"/repos/{owner}/{repo}")

    # 5. Create a new repository
    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = True,
        org: Optional[str] = None
    ) -> Dict[str, Any]:
        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init
        }
        endpoint = f"/orgs/{org}/repos" if org else "/user/repos"
        return self._request("POST", endpoint, json=payload)

    # 6. Delete an existing repository
    def delete_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/repos/{owner}/{repo}")

    # 7. Retrieve the contents of a file in a repository
    def get_file_content(self, owner: str, repo: str, file_path: str, ref: str = "main") -> Dict[str, Any]:
        res = self._request("GET", f"/repos/{owner}/{repo}/contents/{file_path.lstrip('/')}", params={"ref": ref})
        if res.get("success") and isinstance(res.get("data"), dict):
            file_data = res["data"]
            encoding = file_data.get("encoding", "")
            raw_content = file_data.get("content", "")
            if encoding == "base64" and raw_content:
                try:
                    decoded = base64.b64decode(raw_content).decode("utf-8")
                    file_data["decoded_content"] = decoded
                except Exception:
                    pass
            return {"success": True, "file_data": file_data, "sha": file_data.get("sha")}
        return res

    # 8. Upload or update a file in a repository
    def upload_or_update_file(
        self,
        owner: str,
        repo: str,
        file_path: str,
        content: str,
        message: str = "Update file via GitHub API",
        sha: Optional[str] = None,
        branch: str = "main"
    ) -> Dict[str, Any]:
        # If SHA not provided, attempt to fetch current SHA if file exists
        if not sha:
            existing = self.get_file_content(owner, repo, file_path, ref=branch)
            if existing.get("success"):
                sha = existing.get("sha")

        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload = {
            "message": message,
            "content": encoded_content,
            "branch": branch
        }
        if sha:
            payload["sha"] = sha
        return self._request("PUT", f"/repos/{owner}/{repo}/contents/{file_path.lstrip('/')}", json=payload)

    # 9. Delete a file from a repository
    def delete_file(
        self,
        owner: str,
        repo: str,
        file_path: str,
        message: str = "Delete file via GitHub API",
        sha: Optional[str] = None,
        branch: str = "main"
    ) -> Dict[str, Any]:
        if not sha:
            existing = self.get_file_content(owner, repo, file_path, ref=branch)
            if existing.get("success"):
                sha = existing.get("sha")
            else:
                return {"success": False, "error": f"Cannot delete '{file_path}': file not found or SHA missing."}

        payload = {
            "message": message,
            "sha": sha,
            "branch": branch
        }
        return self._request("DELETE", f"/repos/{owner}/{repo}/contents/{file_path.lstrip('/')}", json=payload)

    # 10. List issues in a repository
    def list_issues(self, owner: str, repo: str, state: str = "open") -> Dict[str, Any]:
        return self._request("GET", f"/repos/{owner}/{repo}/issues", params={"state": state})

    # 11. Create a new issue in a repository
    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"title": title, "body": body}
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        return self._request("POST", f"/repos/{owner}/{repo}/issues", json=payload)

    # 12. Add a comment to an existing issue
    def comment_issue(self, owner: str, repo: str, issue_number: Union[int, str], body: str) -> Dict[str, Any]:
        return self._request("POST", f"/repos/{owner}/{repo}/issues/{issue_number}/comments", json={"body": body})

    # 13. Close an existing issue
    def close_issue(self, owner: str, repo: str, issue_number: Union[int, str]) -> Dict[str, Any]:
        return self._request("PATCH", f"/repos/{owner}/{repo}/issues/{issue_number}", json={"state": "closed"})

    # 14. List pull requests in a repository
    def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> Dict[str, Any]:
        return self._request("GET", f"/repos/{owner}/{repo}/pulls", params={"state": state})

    # 15. Create a new pull request
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = ""
    ) -> Dict[str, Any]:
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body
        }
        return self._request("POST", f"/repos/{owner}/{repo}/pulls", json=payload)

    # 16. Merge an existing pull request
    def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pull_number: Union[int, str],
        commit_title: str = "Merged via GitHub API",
        merge_method: str = "merge"
    ) -> Dict[str, Any]:
        payload = {
            "commit_title": commit_title,
            "merge_method": merge_method
        }
        return self._request("PUT", f"/repos/{owner}/{repo}/pulls/{pull_number}/merge", json=payload)

    # 17. Search for repositories based on a query
    def search_repositories(self, query: str, sort: str = "stars", order: str = "desc") -> Dict[str, Any]:
        return self._request("GET", "/search/repositories", params={"q": query, "sort": sort, "order": order})

    # 18. Search for issues based on a query
    def search_issues(self, query: str, sort: str = "updated", order: str = "desc") -> Dict[str, Any]:
        return self._request("GET", "/search/issues", params={"q": query, "sort": sort, "order": order})

    # 19. Search for code based on a query
    def search_code(self, query: str) -> Dict[str, Any]:
        return self._request("GET", "/search/code", params={"q": query})


# Global Singleton Helper
_gh_service: Optional[GitHubService] = None

def get_github_service() -> GitHubService:
    global _gh_service
    if _gh_service is None:
        _gh_service = GitHubService()
    return _gh_service
