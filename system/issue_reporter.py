"""
system/issue_reporter.py - Automated GitHub Issue & Crash Reporting Subsystem.

Automatically intercepts unhandled exceptions, crashes, and pipeline errors across
the PySide6 GUI, CLI Orchestrator, and background workers, sanitizes sensitive tokens,
and files structured GitHub issues or updates existing ones on https://github.com/MaxMasAI/agentic-web/issues.
"""

import os
import sys
import json
import time
import hashlib
import platform
import traceback
import threading
from typing import Dict, List, Any, Optional, Tuple

import requests

from services.app_config import config
from system.security_guard import SENSITIVE_ENV_KEYS

DEFAULT_REPO_OWNER = "MaxMasAI"
DEFAULT_REPO_NAME = "agentic-web"
GITHUB_API_BASE = "https://api.github.com"
CREDS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "github_creds.json")
CRASH_LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "crashes")


def sanitize_text(text: str) -> str:
    """Removes sensitive tokens and API keys from error messages and tracebacks."""
    if not text:
        return ""
    sanitized = text
    # Sanitize known sensitive environment values if present
    for key in SENSITIVE_ENV_KEYS:
        val = os.environ.get(key)
        if val and len(val) > 4:
            sanitized = sanitized.replace(val, f"[{key}_REDACTED]")

    # Redact common PAT and Bearer token formats
    import re
    sanitized = re.sub(r"ghp_[a-zA-Z0-9]{20,}", "[GH_PAT_REDACTED]", sanitized)
    sanitized = re.sub(r"AIza[0-9A-Za-z-_]{35}", "[GEMINI_KEY_REDACTED]", sanitized)
    sanitized = re.sub(r"sk-[a-zA-Z0-9]{20,}", "[API_KEY_REDACTED]", sanitized)
    return sanitized


def compute_traceback_fingerprint(exc_type: str, tb_str: str) -> str:
    """Generates a stable hash of the traceback structure ignoring line numbers."""
    import re
    # Remove specific line numbers and file paths to match same error across machines
    normalized = re.sub(r'File ".*?", line \d+', 'File "<path>", line 0', tb_str)
    normalized = re.sub(r'\d+', '0', normalized)
    raw = f"{exc_type}:{normalized}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


class CrashReport:
    """Encapsulates diagnostic context for a detected application crash or error."""
    def __init__(
        self,
        exc_type: str,
        exc_value: str,
        tb_str: str,
        extra_context: Optional[Dict[str, Any]] = None
    ):
        self.exc_type = exc_type
        self.exc_value = sanitize_text(str(exc_value))
        self.raw_traceback = sanitize_text(tb_str)
        self.fingerprint = compute_traceback_fingerprint(exc_type, self.raw_traceback)
        self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        self.extra_context = extra_context or {}

        # System telemetry
        self.os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
        self.python_info = f"{platform.python_implementation()} {platform.python_version()} ({platform.architecture()[0]})"
        self.app_mode = "PySide6 GUI Desktop" if "PySide6" in sys.modules else "CLI Orchestrator"

    def to_markdown_issue(self, repo_owner: str, repo_name: str) -> Tuple[str, str]:
        """Generates GitHub issue title and formatted markdown body."""
        short_val = (self.exc_value[:75] + '...') if len(self.exc_value) > 75 else self.exc_value
        title = f"[Auto-Crash] {self.exc_type}: {short_val}"

        body = f"""### 🚨 Autonomous Application Crash Report

An unhandled exception was automatically captured by **Agentic Web Mission Control**.

---

#### 📋 Crash Summary
- **Exception Type:** `{self.exc_type}`
- **Exception Message:** `{self.exc_value}`
- **Crash Fingerprint:** `FP-{self.fingerprint}`
- **Timestamp:** `{self.timestamp}`
- **Runtime Mode:** `{self.app_mode}`

---

#### 💻 System Environment
| Property | Value |
|---|---|
| **Operating System** | `{self.os_info}` |
| **Python Version** | `{self.python_info}` |
| **Machine / Node** | `{platform.node()}` |
| **Repository Target** | `https://github.com/{repo_owner}/{repo_name}` |

---

#### 🔍 Full Sanitized Stack Trace
<details>
<summary><b>Click to expand traceback</b></summary>

```python
{self.raw_traceback}
```
</details>

---

#### 🤖 Execution Context
```json
{json.dumps(self.extra_context, indent=2)}
```

---
*Reported automatically by [Agentic Web](https://github.com/{repo_owner}/{repo_name}) Autonomous Issue Dispatcher.*  
*Fingerprint Token: `<!-- FP:{self.fingerprint} -->`*
"""
        return title, body

    def save_local_dump(self) -> str:
        """Saves crash report locally for offline inspection."""
        os.makedirs(CRASH_LOGS_DIR, exist_ok=True)
        filename = f"crash_{int(time.time())}_{self.fingerprint}.json"
        filepath = os.path.join(CRASH_LOGS_DIR, filename)
        payload = {
            "exc_type": self.exc_type,
            "exc_value": self.exc_value,
            "fingerprint": self.fingerprint,
            "timestamp": self.timestamp,
            "system_info": {
                "os": self.os_info,
                "python": self.python_info,
                "mode": self.app_mode
            },
            "traceback": self.raw_traceback,
            "extra_context": self.extra_context
        }
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        except Exception as e:
            print(f"[IssueReporter] Could not save local crash dump: {e}")
        return filepath


class GitHubIssueReporter:
    """
    Manages automated and manual GitHub issue creation, deduplication,
    and pull request dispatch on https://github.com/MaxMasAI/agentic-web.
    """
    def __init__(
        self,
        repo_owner: str = DEFAULT_REPO_OWNER,
        repo_name: str = DEFAULT_REPO_NAME,
        token: Optional[str] = None
    ):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token or self._resolve_token()

    def _resolve_token(self) -> str:
        """Finds token in environment, local.env, or saved json/github_creds.json."""
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PAT") or os.environ.get("GH_TOKEN")
        if token:
            return token

        # Check local.env or .env
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for env_name in ["local.env", ".env"]:
            env_path = os.path.join(root_dir, env_name)
            if os.path.exists(env_path):
                try:
                    with open(env_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if line.startswith("GITHUB_TOKEN=") or line.startswith("GITHUB_PAT="):
                                return line.split("=", 1)[1].strip().strip('"').strip("'")
                except Exception:
                    pass

        # Check json/github_creds.json
        if os.path.exists(CREDS_FILE):
            try:
                with open(CREDS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("token", "")
            except Exception:
                pass

        return ""

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgenticWeb-CrashReporter/1.0"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def find_existing_issue_by_fingerprint(self, fingerprint: str) -> Optional[int]:
        """Searches repository for an existing open issue matching the crash fingerprint."""
        if not self.token:
            return None
        query = f"repo:{self.repo_owner}/{self.repo_name} is:issue is:open \"FP:{fingerprint}\""
        url = f"{GITHUB_API_BASE}/search/issues"
        try:
            resp = requests.get(url, headers=self._get_headers(), params={"q": query}, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    return items[0].get("number")
        except Exception as e:
            print(f"[IssueReporter] Deduplication search failed: {e}")
        return None

    def report_crash(
        self,
        exc_type: str,
        exc_value: str,
        tb_str: str,
        extra_context: Optional[Dict[str, Any]] = None,
        async_dispatch: bool = True
    ) -> Dict[str, Any]:
        """
        Processes a crash report, writes local dump, and files/updates a GitHub issue.
        """
        report = CrashReport(exc_type, exc_value, tb_str, extra_context)
        local_path = report.save_local_dump()

        # Check if enabled in app config
        auto_report = config.get("github.auto_report_issues", True)
        if not auto_report:
            return {
                "success": True,
                "status": "local_only",
                "message": "Auto-reporting disabled in settings; saved locally.",
                "local_dump": local_path
            }

        def _dispatch():
            return self._submit_to_github(report, local_path)

        if async_dispatch:
            t = threading.Thread(target=_dispatch, daemon=True)
            t.start()
            return {
                "success": True,
                "status": "dispatching_async",
                "fingerprint": report.fingerprint,
                "local_dump": local_path
            }
        else:
            return _dispatch()

    def _submit_to_github(self, report: CrashReport, local_path: str) -> Dict[str, Any]:
        """Performs network submission to GitHub API."""
        if not self.token:
            msg = f"No GITHUB_TOKEN configured. Crash report preserved locally at: {local_path}"
            print(f"[IssueReporter] {msg}")
            return {"success": False, "error": "Missing GITHUB_TOKEN", "local_dump": local_path}

        title, body = report.to_markdown_issue(self.repo_owner, self.repo_name)

        # 1. Deduplication check
        existing_number = self.find_existing_issue_by_fingerprint(report.fingerprint)
        if existing_number:
            # Add update comment to existing issue
            comment_url = f"{GITHUB_API_BASE}/repos/{self.repo_owner}/{self.repo_name}/issues/{existing_number}/comments"
            comment_body = f"""🔄 **New crash recurrence detected** at `{report.timestamp}` on `{report.os_info}`.
Runtime mode: `{report.app_mode}`.
<details>
<summary>Recurrence Traceback</summary>

```python
{report.raw_traceback}
```
</details>
"""
            try:
                resp = requests.post(comment_url, headers=self._get_headers(), json={"body": comment_body}, timeout=12)
                if resp.status_code in (200, 201):
                    issue_url = f"https://github.com/{self.repo_owner}/{self.repo_name}/issues/{existing_number}"
                    print(f"\033[92m[IssueReporter] Appended crash recurrence to existing issue #{existing_number}: {issue_url}\033[0m")
                    return {"success": True, "action": "commented", "issue_url": issue_url, "issue_number": existing_number}
            except Exception as e:
                print(f"[IssueReporter] Error updating issue #{existing_number}: {e}")

        # 2. Create new issue
        issue_url = f"{GITHUB_API_BASE}/repos/{self.repo_owner}/{self.repo_name}/issues"
        payload = {
            "title": title,
            "body": body,
            "labels": ["bug", "automated-crash-report"]
        }
        try:
            resp = requests.post(issue_url, headers=self._get_headers(), json=payload, timeout=12)
            if resp.status_code in (200, 201):
                data = resp.json()
                created_url = data.get("html_url", f"https://github.com/{self.repo_owner}/{self.repo_name}/issues")
                issue_num = data.get("number")
                print(f"\033[92m[IssueReporter] 🚀 Successfully filed automated GitHub Issue #{issue_num}: {created_url}\033[0m")
                return {"success": True, "action": "created", "issue_url": created_url, "issue_number": issue_num}
            else:
                err_text = resp.text
                print(f"\033[91m[IssueReporter] Failed to create GitHub issue (HTTP {resp.status_code}): {err_text}\033[0m")
                return {"success": False, "status_code": resp.status_code, "error": err_text}
        except Exception as e:
            print(f"\033[91m[IssueReporter] HTTP Exception when posting issue: {e}\033[0m")
            return {"success": False, "error": str(e)}

    def create_manual_issue(self, title: str, body: str, labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Allows direct issue submission from GUI or CLI."""
        if not self.token:
            return {"success": False, "error": "No GITHUB_TOKEN configured."}
        url = f"{GITHUB_API_BASE}/repos/{self.repo_owner}/{self.repo_name}/issues"
        payload = {
            "title": title,
            "body": body,
            "labels": labels or ["user-report"]
        }
        try:
            resp = requests.post(url, headers=self._get_headers(), json=payload, timeout=12)
            if resp.status_code in (200, 201):
                data = resp.json()
                return {"success": True, "issue_url": data.get("html_url"), "issue_number": data.get("number")}
            return {"success": False, "status_code": resp.status_code, "error": resp.text}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global Reporter Singleton
_global_issue_reporter: Optional[GitHubIssueReporter] = None

def get_issue_reporter() -> GitHubIssueReporter:
    global _global_issue_reporter
    if _global_issue_reporter is None:
        owner = config.get("github.repo_owner", DEFAULT_REPO_OWNER)
        name = config.get("github.repo_name", DEFAULT_REPO_NAME)
        _global_issue_reporter = GitHubIssueReporter(repo_owner=owner, repo_name=name)
    return _global_issue_reporter


# Global Exception Hooks
_original_excepthook = sys.excepthook

def global_exception_handler(exc_type, exc_value, exc_traceback):
    """Intercepts unhandled Python exceptions and forwards them to GitHubIssueReporter."""
    # First print to standard stderr
    if _original_excepthook:
        _original_excepthook(exc_type, exc_value, exc_traceback)

    if issubclass(exc_type, KeyboardInterrupt):
        return

    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    reporter = get_issue_reporter()
    reporter.report_crash(
        exc_type=exc_type.__name__ if hasattr(exc_type, "__name__") else str(exc_type),
        exc_value=str(exc_value),
        tb_str=tb_str,
        extra_context={
            "argv": sys.argv,
            "cwd": os.getcwd()
        },
        async_dispatch=True
    )


def install_crash_reporter():
    """Installs global exception handlers into sys and threading modules."""
    sys.excepthook = global_exception_handler
    if hasattr(threading, "excepthook"):
        def thread_exception_handler(args):
            global_exception_handler(args.exc_type, args.exc_value, args.exc_traceback)
        threading.excepthook = thread_exception_handler
    print("\033[92m[IssueReporter] Autonomous GitHub Crash & Issue Reporter Active (Target: MaxMasAI/agentic-web)\033[0m")


if __name__ == "__main__":
    # Test CLI invocation
    if "--test" in sys.argv:
        print("[*] Testing GitHub Issue Reporter...")
        rep = get_issue_reporter()
        test_tb = "Traceback (most recent call last):\n  File \"app.py\", line 100, in test_func\n    raise ValueError('Test diagnostic exception')\nValueError: Test diagnostic exception"
        res = rep.report_crash("ValueError", "Test diagnostic exception from Agentic Web", test_tb, extra_context={"test": True}, async_dispatch=False)
        print(f"Result: {json.dumps(res, indent=2)}")
