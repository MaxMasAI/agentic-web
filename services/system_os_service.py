"""
services/system_os_service.py - System (OS) Command Execution Plugin
Provides access to operating system execution and sys_exec command tools with configurable CWD auto-append.
"""

import os
import sys
import subprocess
import time
import json
from typing import Dict, List, Any, Optional

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "json", "system_os_config.json")


class SystemOSService:
    """
    System (OS) Tool Service.
    Executes local operating system commands with auto_cwd support.
    """
    def __init__(self, config_path: str = SETTINGS_FILE):
        self.config_path = config_path
        self.auto_cwd: bool = True
        self.sys_exec_enabled: bool = True
        self.default_timeout: int = 60
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.auto_cwd = data.get("auto_cwd", True)
                    self.sys_exec_enabled = data.get("sys_exec_enabled", True)
                    self.default_timeout = data.get("default_timeout", 60)
                    return
            except Exception:
                pass
        self.save_config()

    def save_config(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "auto_cwd": self.auto_cwd,
                    "sys_exec_enabled": self.sys_exec_enabled,
                    "default_timeout": self.default_timeout
                }, f, indent=2)
        except Exception:
            pass

    def set_options(self, auto_cwd: Optional[bool] = None, sys_exec_enabled: Optional[bool] = None):
        if auto_cwd is not None:
            self.auto_cwd = auto_cwd
        if sys_exec_enabled is not None:
            self.sys_exec_enabled = sys_exec_enabled
        self.save_config()

    def sys_exec(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Executes a system shell command (cmd.sys_exec).
        """
        if not self.sys_exec_enabled:
            return {
                "success": False,
                "error": "System command execution (sys_exec) is disabled in System (OS) plugin settings."
            }

        target_cwd = cwd or (os.getcwd() if self.auto_cwd else None)
        exec_timeout = timeout or self.default_timeout
        start_time = time.time()

        # Cross-platform shell formulation
        shell_kwargs = {
            "shell": True,
            "capture_output": True,
            "text": True,
            "timeout": exec_timeout,
            "cwd": target_cwd,
            "env": {**os.environ, **(env or {})}
        }

        try:
            proc = subprocess.run(command, **shell_kwargs)
            duration = round(time.time() - start_time, 3)
            return {
                "success": proc.returncode == 0,
                "command": command,
                "returncode": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "cwd": target_cwd,
                "duration_sec": duration
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "command": command,
                "error": f"Command timed out after {exec_timeout} seconds.",
                "cwd": target_cwd
            }
        except Exception as e:
            return {
                "success": False,
                "command": command,
                "error": f"Execution failed: {str(e)}",
                "cwd": target_cwd
            }


# Global Singleton Helper
_sys_os_service: Optional[SystemOSService] = None

def get_system_os_service() -> SystemOSService:
    global _sys_os_service
    if _sys_os_service is None:
        _sys_os_service = SystemOSService()
    return _sys_os_service
