"""
system/security_guard.py - Enterprise Security Guard & Command Inspection Engine.

Provides deep inspection of shell commands, scripts, and tool calls executed by AI agents
to prevent prompt-injection attacks, destructive system drops (e.g. rm -rf, disk formats),
reverse shells, and credential exfiltration.
"""

import os
import sys
import re
from enum import Enum
from typing import Dict, List, Tuple, Any, Optional, Set

# Permission Tiers for Agent Execution
class PermissionLevel(Enum):
    SAFE_READ = "safe_read"           # File reads, directory listings, harmless inspection
    STANDARD_DEV = "standard_dev"     # Normal development commands (git, npm, pip, python, pytest)
    RESTRICTED_ADMIN = "restricted"   # System modifications, network calls, file overwrites
    BLOCKED = "blocked"               # Destructive, dangerous, or malicious commands


class SecurityViolation(Exception):
    """Raised when a command violates security policy."""
    pass


# High-Risk / Destructive Command Patterns
DANGEROUS_PATTERNS: List[Tuple[re.Pattern, str]] = [
    # 1. Destructive File/Directory Deletion
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f*|-rf|-fr)\s+([/\\]|\*|~|\$HOME|\.\.)", re.IGNORECASE), "Recursive root/home/wildcard filesystem deletion"),
    (re.compile(r"\bdel(\s+/[a-zA-Z]+)+\s+([a-zA-Z]:[/\\]|\*|\.\.)", re.IGNORECASE), "Windows destructive root/recursive deletion"),
    (re.compile(r"\brmdir(\s+/[a-zA-Z]+)+\s+([a-zA-Z]:[/\\]|\*|\.\.)", re.IGNORECASE), "Windows root rmdir deletion"),
    (re.compile(r"\bformat\s+[a-zA-Z]:", re.IGNORECASE), "Windows volume format command"),
    (re.compile(r"\bdiskpart\b", re.IGNORECASE), "Direct Windows disk partition manipulation"),

    # 3. Fork Bombs & Resource Exhaustion
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.IGNORECASE), "Bash fork bomb"),
    (re.compile(r"%\s*0\s*\|\s*%\s*0", re.IGNORECASE), "Windows batch fork bomb"),

    # 4. Hidden Download & Execute Pipelines (Remote Shell Drop)
    (re.compile(r"\b(curl|wget|fetch|powershell|certutil)\b.*\|\s*(bash|sh|zsh|cmd|powershell)\b", re.IGNORECASE), "Pipe-to-shell remote code execution"),
    (re.compile(r"\bInvoke-Expression\s*\(?\s*(New-Object\s+Net\.WebClient|iwr|curl)", re.IGNORECASE), "PowerShell download-and-execute string"),

    # 5. Reverse Shells & Socket Hijacking
    (re.compile(r"\b(nc|ncat|netcat)\s+(-e|/bin/sh|/bin/bash|cmd\.exe|powershell\.exe)", re.IGNORECASE), "Netcat reverse shell spawn"),
    (re.compile(r"\bpython[0-9.]*\s+-c\s+.*(socket.*connect.*os\.dup2|pty\.spawn)", re.IGNORECASE), "Python reverse shell socket invocation"),

    # 6. Shadow Copy / Backup Deletion (Ransomware patterns)
    (re.compile(r"\bvssadmin\s+delete\s+shadows", re.IGNORECASE), "Volume shadow copy deletion"),
    (re.compile(r"\bbcdedit\s+/set.*recoveryenabled\s+no", re.IGNORECASE), "Windows boot recovery disabling"),

    # 7. Environment Credential Exfiltration
    (re.compile(r"\b(env|printenv|set)\b.*\|\s*(curl|wget|nc)\b", re.IGNORECASE), "Environment variable exfiltration over network"),
]

# Sensitive Environment Variable Keys that must be stripped from child processes
SENSITIVE_ENV_KEYS: Set[str] = {
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "OPENROUTER_API_KEY",
    "HF_TOKEN",
    "PERPLEXITY_API_KEY",
    "GROK_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "AZURE_CLIENT_SECRET",
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "AUTH0_CLIENT_SECRET"
}


class SecurityGuard:
    """
    Centralized Security Guard for command auditing, permission ring enforcement,
    and sandbox environment sanitization.
    """
    def __init__(self, default_level: PermissionLevel = PermissionLevel.STANDARD_DEV):
        self.permission_level = default_level
        self.blocked_count = 0
        self.audit_log: List[Dict[str, Any]] = []

    def validate_command(self, cmd: str, allowed_level: Optional[PermissionLevel] = None) -> Tuple[bool, str]:
        """
        Scans a shell command against security policies and dangerous pattern filters.
        Returns (is_allowed: bool, reason: str).
        """
        if not cmd or not cmd.strip():
            return True, "Empty command"

        target_cmd = cmd.strip()

        # 1. Match against known dangerous patterns
        for pattern, desc in DANGEROUS_PATTERNS:
            if pattern.search(target_cmd):
                self.blocked_count += 1
                violation_msg = f"SECURITY ALERT: Command blocked by policy: {desc} -> '{target_cmd[:60]}...'"
                self._record_audit(target_cmd, False, violation_msg)
                return False, violation_msg

        # 2. Permission level gating
        req_level = allowed_level or self.permission_level
        if req_level == PermissionLevel.SAFE_READ:
            write_indicators = [">", ">>", "rm ", "del ", "mkdir ", "touch ", "mv ", "move ", "install ", "npm i", "pip install"]
            if any(w in target_cmd.lower() for w in write_indicators):
                return False, f"SECURITY POLICY: Command writes/modifies system but current level is {req_level.value}"

        self._record_audit(target_cmd, True, "Allowed")
        return True, "Allowed"

    def sanitize_environment(self, base_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Creates a sanitized environment dictionary with sensitive tokens redacted
        to prevent untrusted tools from exfiltrating system API secrets.
        """
        env = dict(base_env or os.environ)
        for key in list(env.keys()):
            if key in SENSITIVE_ENV_KEYS or any(s in key.upper() for s in ["SECRET", "PRIVATE_KEY", "PASSWORD", "AUTH_TOKEN"]):
                env[key] = "[REDACTED_BY_SECURITY_GUARD]"
        return env

    def _record_audit(self, command: str, allowed: bool, note: str):
        self.audit_log.append({
            "command": command,
            "allowed": allowed,
            "note": note
        })
        if len(self.audit_log) > 500:
            self.audit_log.pop(0)


# Global Singleton Instance
_global_security_guard: Optional[SecurityGuard] = None

def get_security_guard() -> SecurityGuard:
    global _global_security_guard
    if _global_security_guard is None:
        _global_security_guard = SecurityGuard()
    return _global_security_guard
