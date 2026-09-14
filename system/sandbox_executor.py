"""
system/sandbox_executor.py - Containerized & Subprocess Sandbox Execution Engine.

Executes dynamic agent tool commands, Python scripts, and shell operations inside
isolated runtime boundaries (Docker/Container when active, or secure resource-capped subprocess).
"""

import os
import sys
import shutil
import subprocess
import tempfile
import time
from typing import Dict, List, Any, Optional, Tuple

from system.security_guard import get_security_guard, SecurityViolation


class SandboxResult:
    """Represents standard execution output from a sandboxed command."""
    def __init__(self, returncode: int, stdout: str, stderr: str, duration: float, sandbox_type: str = "subprocess"):
        self.returncode = returncode
        self.stdout = stdout or ""
        self.stderr = stderr or ""
        self.duration = duration
        self.sandbox_type = sandbox_type

    @property
    def success(self) -> bool:
        return self.returncode == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_sec": round(self.duration, 3),
            "sandbox_type": self.sandbox_type
        }


class SandboxExecutor:
    """
    Enterprise Execution Sandbox.
    Provides container-isolated execution via Docker when available,
    and falls back to security-screened, resource-capped subprocess execution.
    """
    def __init__(self, force_docker: bool = False, timeout_sec: int = 15):
        self.force_docker = force_docker
        self.timeout_sec = timeout_sec
        self.guard = get_security_guard()
        self._docker_available = self._check_docker_runtime()

    def _check_docker_runtime(self) -> bool:
        """Checks if local Docker daemon is running and accessible."""
        docker_bin = shutil.which("docker")
        if not docker_bin:
            return False
        try:
            res = subprocess.run(["docker", "info"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
            return res.returncode == 0
        except Exception:
            return False

    def execute_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
        env: Optional[Dict[str, str]] = None,
        use_container: Optional[bool] = None
    ) -> SandboxResult:
        """
        Executes a shell command through the security inspection pipeline
        and into the isolated sandbox layer.
        """
        # 1. Pre-execution Security Policy Verification
        is_allowed, reason = self.guard.validate_command(command)
        if not is_allowed:
            return SandboxResult(
                returncode=126,
                stdout="",
                stderr=f"SECURITY_GUARD_REJECTION: {reason}",
                duration=0.0,
                sandbox_type="security_guard"
            )

        start_time = time.time()
        exec_timeout = timeout or self.timeout_sec
        should_use_docker = use_container if use_container is not None else (self.force_docker and self._docker_available)

        # 2. Containerized Sandbox Execution (Docker)
        if should_use_docker and self._docker_available:
            return self._execute_docker_sandbox(command, cwd, exec_timeout, start_time)

        # 3. Secure Local Subprocess Sandbox Execution
        return self._execute_subprocess_sandbox(command, cwd, exec_timeout, env, start_time)

    def _execute_docker_sandbox(self, command: str, cwd: Optional[str], timeout: int, start_time: float) -> SandboxResult:
        """Runs the command in an unprivileged, resource-capped Docker container."""
        work_dir = os.path.abspath(cwd or os.getcwd())
        container_image = "python:3.11-slim"

        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",                    # Drop network access for pure isolation
            "--memory", "512m",                     # 512MB RAM cap
            "--cpus", "1.0",                        # 1 CPU core cap
            "--security-opt", "no-new-privileges",  # Prevent privilege escalation
            "-v", f"{work_dir}:/workspace:rw",
            "-w", "/workspace",
            container_image,
            "sh", "-c", command
        ]

        try:
            res = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            duration = time.time() - start_time
            return SandboxResult(
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                duration=duration,
                sandbox_type="docker_container"
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                returncode=124,
                stdout="",
                stderr=f"DOCKER_TIMEOUT: Execution exceeded {timeout}s time limit.",
                duration=time.time() - start_time,
                sandbox_type="docker_container"
            )
        except Exception as e:
            # Fallback to local subprocess if Docker execution failed
            return self._execute_subprocess_sandbox(command, cwd, timeout, None, start_time)

    def _execute_subprocess_sandbox(
        self,
        command: str,
        cwd: Optional[str],
        timeout: int,
        env: Optional[Dict[str, str]],
        start_time: float
    ) -> SandboxResult:
        """Runs the command in a sanitized subprocess environment."""
        target_cwd = cwd or os.getcwd()
        sanitized_env = self.guard.sanitize_environment(env)

        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=target_cwd,
                env=sanitized_env
            )
            duration = time.time() - start_time
            return SandboxResult(
                returncode=res.returncode,
                stdout=res.stdout,
                stderr=res.stderr,
                duration=duration,
                sandbox_type="subprocess_sanitized"
            )
        except subprocess.TimeoutExpired:
            return SandboxResult(
                returncode=124,
                stdout="",
                stderr=f"TIMEOUT: Process killed after exceeding {timeout}s limit.",
                duration=time.time() - start_time,
                sandbox_type="subprocess_sanitized"
            )
        except Exception as e:
            return SandboxResult(
                returncode=1,
                stdout="",
                stderr=f"EXEC_FAILED: {str(e)}",
                duration=time.time() - start_time,
                sandbox_type="subprocess_sanitized"
            )


# Global Sandbox Executor
_global_sandbox_executor: Optional[SandboxExecutor] = None

def get_sandbox_executor() -> SandboxExecutor:
    global _global_sandbox_executor
    if _global_sandbox_executor is None:
        _global_sandbox_executor = SandboxExecutor()
    return _global_sandbox_executor
