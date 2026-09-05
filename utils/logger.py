"""
logger.py - Centralized logging for the multi-agent pipeline.
Writes all output to both the terminal (with ANSI colors) and a
timestamped plain-text log file inside the logs/ directory.
Includes automatic cleanup to cap total logs directory size at 25 MB.
"""

import os
import re
import sys
import time
import glob
import logging

# Max size configuration (25 MB)
MAX_LOGS_DIR_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
TARGET_CLEANUP_SIZE_BYTES = 18 * 1024 * 1024  # Target to retain when cleanup triggers

# ── ANSI stripping for clean log files ────────────────────────────────────
_ANSI_RE = re.compile(r"\033\[[0-9;]*m")

def strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def get_total_logs_size(logs_dir: str = "logs") -> int:
    """Returns the total size in bytes of all log files in logs/ directory."""
    if not os.path.exists(logs_dir):
        return 0
    total = 0
    for root, _, files in os.walk(logs_dir):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except Exception:
                pass
    return total


def auto_cleanup_logs(logs_dir: str = "logs", max_size_bytes: int = MAX_LOGS_DIR_SIZE_BYTES):
    """
    Checks total size of logs directory. If it exceeds 25 MB,
    deletes oldest log files until total size is reduced below the target limit.
    """
    if not os.path.exists(logs_dir):
        return

    try:
        log_files = glob.glob(os.path.join(logs_dir, "*.log"))
        if not log_files:
            return

        total_size = sum(os.path.getsize(f) for f in log_files if os.path.exists(f))
        if total_size <= max_size_bytes:
            return

        # Sort log files by modification time (oldest first)
        log_files.sort(key=lambda f: os.path.getmtime(f))

        deleted_count = 0
        freed_bytes = 0

        for f in log_files:
            if total_size <= TARGET_CLEANUP_SIZE_BYTES:
                break
            try:
                sz = os.path.getsize(f)
                os.remove(f)
                total_size -= sz
                freed_bytes += sz
                deleted_count += 1
            except Exception:
                pass

        if deleted_count > 0:
            freed_mb = freed_bytes / (1024 * 1024)
            sys.__stdout__.write(f"\n\033[93m[*] [Auto-Cleanup] Total logs exceeded 25 MB limit. Removed {deleted_count} older log file(s), freeing {freed_mb:.1f} MB.\033[0m\n")
            sys.__stdout__.flush()
    except Exception as e:
        pass


# ── Tee: writes to both terminal and file ─────────────────────────────────
class _Tee:
    """Wraps sys.stdout so every print() also writes to a log file with size limit."""
    def __init__(self, log_path: str):
        self._terminal = sys.__stdout__
        self._log_path = log_path
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._file = open(log_path, "a", encoding="utf-8", buffering=1)
        self._bytes_written = 0

    def write(self, message: str):
        self._terminal.write(message)
        clean_msg = strip_ansi(message)
        self._file.write(clean_msg)
        self._bytes_written += len(clean_msg.encode("utf-8", errors="replace"))

        # Safety check: if current file alone exceeds 25 MB, truncate oldest half
        if self._bytes_written > MAX_LOGS_DIR_SIZE_BYTES:
            try:
                self._file.flush()
                self._file.close()
                # Keep latest 10MB of the file
                with open(self._log_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                half = content[len(content)//2:]
                with open(self._log_path, "w", encoding="utf-8") as f:
                    f.write("[... Earlier log truncated due to 25MB limit ...]\n" + half)
                self._file = open(self._log_path, "a", encoding="utf-8", buffering=1)
                self._bytes_written = len(half.encode("utf-8", errors="replace"))
            except Exception:
                pass

    def flush(self):
        self._terminal.flush()
        self._file.flush()

    def close(self):
        try:
            self._file.close()
        except Exception:
            pass

    def isatty(self):
        return self._terminal.isatty()


# Singleton reference so we can close it gracefully
_tee_instance: _Tee | None = None


def setup_logging(task_slug: str = "session") -> str:
    """
    Install the tee into sys.stdout and create a timestamped log file.
    Runs 25 MB auto-cleanup before creating new log file.
    """
    global _tee_instance

    os.makedirs("logs", exist_ok=True)
    
    # Auto clean up old logs if directory size > 25 MB
    auto_cleanup_logs("logs", MAX_LOGS_DIR_SIZE_BYTES)

    timestamp  = time.strftime("%Y%m%d_%H%M%S")
    clean_slug = re.sub(r"[^\w-]", "_", task_slug)[:40]
    log_file_path = os.path.join("logs", f"{timestamp}_{clean_slug}.log")

    # Write a header into the log file
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write(f"{'='*60}\n")
        f.write(f"MULTI-AGENT PIPELINE LOG\n")
        f.write(f"Task   : {task_slug}\n")
        f.write(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Max Log Retention: 25 MB (Auto-Managed)\n")
        f.write(f"{'='*60}\n\n")

    # Replace sys.stdout with the tee
    if _tee_instance:
        _tee_instance.close()

    _tee_instance = _Tee(log_file_path)
    sys.stdout = _tee_instance

    return log_file_path


def close_logging():
    """Restore sys.stdout and close the log file."""
    global _tee_instance
    if _tee_instance:
        sys.stdout = sys.__stdout__
        _tee_instance.close()
        _tee_instance = None
    
    # Run cleanup on close as well
    auto_cleanup_logs("logs", MAX_LOGS_DIR_SIZE_BYTES)


def log_path() -> str | None:
    """Returns current log file path if logging is active."""
    if _tee_instance:
        return _tee_instance._file.name
    return None
