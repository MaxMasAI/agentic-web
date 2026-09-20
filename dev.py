"""
dev.py - Robust Live Auto-Reload & Auto-Dependency Development Engine.
Watches all '*.py' and 'requirements.txt' files in the workspace, automatically
installs missing packages directly into 'venv/', and restarts the application
cleanly after all file changes have settled (debounced delay).

Usage:
    python dev.py             # Auto-reloads Desktop GUI (app.py) on code changes
    python dev.py --cli       # Auto-reloads CLI orchestrator (main.py) on code changes
    python dev.py --delay 2   # Custom debounce settling delay in seconds
"""

import os
import sys
import time
import subprocess
import threading
import re
from typing import Set, Dict, Optional

# Set development mode flag for this process and all subprocesses
os.environ["AGENTIC_DEV_MODE"] = "1"

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

# Common Python module name to pip package name mapping
MODULE_TO_PIP_MAP: Dict[str, str] = {
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "yaml": "pyyaml",
    "fitz": "PyMuPDF",
    "sklearn": "scikit-learn",
    "watchdog": "watchdog",
    "playwright": "playwright",
    "uvicorn": "uvicorn",
    "fastapi": "fastapi",
    "pydantic": "pydantic",
    "PySide6": "PySide6",
    "requests": "requests",
    "websockets": "websockets"
}


def get_venv_python() -> str:
    """Finds the workspace virtual environment python executable or falls back to sys.executable."""
    if sys.platform == "win32":
        venv_py = os.path.join(WORKSPACE_DIR, "venv", "Scripts", "python.exe")
    else:
        venv_py = os.path.join(WORKSPACE_DIR, "venv", "bin", "python")
    if os.path.exists(venv_py):
        return venv_py
    return sys.executable


def is_module_installed(raw_name: str) -> bool:
    """Checks if a module is already available in the virtual environment without running pip."""
    clean_name = raw_name.strip().strip("'").strip('"').split(".")[0]
    py_exec = get_venv_python()
    try:
        res = subprocess.run(
            [py_exec, "-c", f"import importlib.util; exit(0 if importlib.util.find_spec('{clean_name}') else 1)"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=WORKSPACE_DIR,
            timeout=5
        )
        return res.returncode == 0
    except Exception:
        return False


def auto_install_package(raw_name: str) -> bool:
    """Installs missing package ONLY if it does not already exist in the virtual environment."""
    clean_name = raw_name.strip().strip("'").strip('"').split(".")[0]
    if not clean_name or clean_name in ("gui", "core", "services", "system", "utils", "voice", "browser"):
        return False

    # Skip if already available in venv
    if is_module_installed(clean_name):
        return True

    pip_pkg = MODULE_TO_PIP_MAP.get(clean_name, clean_name.replace("_", "-"))
    py_exec = get_venv_python()
    print(f"\n\033[93m[📦 Auto-Dependency Resolver]: Missing module '{clean_name}'. Installing '{pip_pkg}' into venv...\033[0m")
    try:
        cmd = [py_exec, "-m", "pip", "install", pip_pkg]
        res = subprocess.run(cmd, cwd=WORKSPACE_DIR)
        if res.returncode == 0:
            print(f"\033[92m[✓ Installed Successfully]: '{pip_pkg}' ready in venv.\033[0m\n")
            return True
        else:
            print(f"\033[91m[!] Failed to install '{pip_pkg}' (exit code {res.returncode})\033[0m\n")
            return False
    except Exception as e:
        print(f"\033[91m[!] Error installing '{pip_pkg}': {e}\033[0m\n")
        return False


def install_requirements() -> bool:
    """Syncs dependencies from requirements.txt into the virtual environment."""
    req_file = os.path.join(WORKSPACE_DIR, "requirements.txt")
    if not os.path.exists(req_file):
        return True
    py_exec = get_venv_python()
    print(f"\n\033[93m[📦 Auto-Syncing Requirements]: Installing packages from requirements.txt into venv...\033[0m")
    try:
        cmd = [py_exec, "-m", "pip", "install", "-r", "requirements.txt"]
        res = subprocess.run(cmd, cwd=WORKSPACE_DIR)
        return res.returncode == 0
    except Exception as e:
        print(f"\033[91m[!] Error syncing requirements.txt: {e}\033[0m")
        return False


def kill_process_tree(proc):
    """Cleanly terminates the process and any child processes across Windows / Unix."""
    if proc is None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            proc.terminate()
            proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


class LiveReloader:
    def __init__(self, target_cmd, settle_delay: float = 1.2):
        self.target_cmd = target_cmd
        self.settle_delay = settle_delay  # Wait for all edits to finish
        self.proc = None
        self._lock = threading.Lock()
        self._debounce_timer = None
        self._pending_changes: Set[str] = set()
        self._installed_in_session: Set[str] = set()

    def start_process(self):
        with self._lock:
            kill_process_tree(self.proc)
            time.sleep(0.2)
            py_exec = get_venv_python()
            full_cmd = [py_exec] + self.target_cmd
            print(f"\033[92m[⚡ Launching Application]:\033[0m {' '.join(full_cmd)}")
            env = dict(os.environ, AGENTIC_DEV_MODE="1")
            
            # Pipe stderr to intercept missing ModuleNotFoundError in real time
            self.proc = subprocess.Popen(
                full_cmd,
                cwd=WORKSPACE_DIR,
                env=env,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1
            )

            # Start background stderr monitor thread
            t = threading.Thread(target=self._monitor_stderr, args=(self.proc,), daemon=True)
            t.start()

    def _monitor_stderr(self, proc):
        """Reads stderr stream and auto-downloads missing Python modules if detected."""
        if not proc or not proc.stderr:
            return
        missing_module_pattern = re.compile(r"ModuleNotFoundError:\s+No\s+module\s+named\s+['\"]?([a-zA-Z0-9_\.]+)['\"]?")

        try:
            for line in proc.stderr:
                sys.stderr.write(line)
                sys.stderr.flush()

                match = missing_module_pattern.search(line)
                if match:
                    raw_mod = match.group(1).split(".")[0]
                    if raw_mod not in self._installed_in_session and raw_mod not in ("gui", "core", "services", "system", "utils", "voice", "browser"):
                        self._installed_in_session.add(raw_mod)
                        if not is_module_installed(raw_mod):
                            success = auto_install_package(raw_mod)
                            if success:
                                time.sleep(0.5)
                                self._execute_debounced_restart()
        except Exception:
            pass

    def on_file_changed(self, changed_file=""):
        """Accumulates changed files and resets the settling timer so all edits finish before reloading."""
        norm_file = (changed_file or "").replace("\\", "/").lower()
        if "/venv/" in norm_file or "/.git/" in norm_file or "/__pycache__/" in norm_file or "/logs/" in norm_file or "/downloads/" in norm_file:
            return

        with self._lock:
            rel = os.path.relpath(changed_file, WORKSPACE_DIR) if changed_file else "code file"
            self._pending_changes.add(rel)

            # Only sync requirements if the root requirements.txt is modified
            if os.path.basename(changed_file) == "requirements.txt":
                install_requirements()

            if self._debounce_timer is not None:
                self._debounce_timer.cancel()

            print(f"\033[93m[⏳ Change in '{rel}'] Waiting {self.settle_delay}s for all file edits to finish...\033[0m")
            self._debounce_timer = threading.Timer(self.settle_delay, self._execute_debounced_restart)
            self._debounce_timer.daemon = True
            self._debounce_timer.start()

    def _execute_debounced_restart(self):
        """Fires only after all file modifications have finished and settled."""
        with self._lock:
            changed_list = ", ".join(sorted(self._pending_changes)) if self._pending_changes else "dependencies"
            self._pending_changes.clear()
            self._debounce_timer = None
            print(f"\n\033[96m[🔄 Edits Settled: {changed_list}] Reloading application now...\033[0m")
        self.start_process()

    def run_with_watchdog(self):
        """Uses watchdog Python library if installed (auto-installs if missing)."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import PatternMatchingEventHandler
        except ImportError:
            # Auto-install watchdog into venv
            auto_install_package("watchdog")
            try:
                from watchdog.observers import Observer
                from watchdog.events import PatternMatchingEventHandler
            except ImportError:
                return False

        class PyFileHandler(PatternMatchingEventHandler):
            def __init__(self, reloader):
                super().__init__(
                    patterns=["*.py", "*requirements.txt"],
                    ignore_patterns=["*/.git/*", "*/venv/*", "*\\venv\\*", "*/dist/*", "*/build/*", "*/__pycache__/*", "*/logs/*", "*/downloads/*"],
                    ignore_directories=True
                )
                self.reloader = reloader

            def on_any_event(self, event):
                if event.event_type in ("modified", "created", "deleted", "moved"):
                    src = getattr(event, "dest_path", None) or event.src_path
                    norm_src = src.replace("\\", "/").lower()
                    if "/venv/" in norm_src or "/.git/" in norm_src or "/__pycache__/" in norm_src or "/logs/" in norm_src or "/downloads/" in norm_src:
                        return
                    if norm_src.endswith(".py") or norm_src.endswith("requirements.txt"):
                        self.reloader.on_file_changed(src)

        event_handler = PyFileHandler(self)
        observer = Observer()
        observer.schedule(event_handler, path=WORKSPACE_DIR, recursive=True)
        observer.start()
        print(f"\033[96m[✓] Native Watchdog Engine Active (Debounce Settling: {self.settle_delay}s | Venv: {get_venv_python()})\033[0m")

        self.start_process()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()
        return True

    def run_with_polling(self):
        """Fast cross-platform polling fallback."""
        print(f"\033[96m[✓] Polling Watcher Active (Debounce Settling: {self.settle_delay}s | Venv: {get_venv_python()})\033[0m")

        def get_mtimes():
            mtimes = {}
            for root, dirs, files in os.walk(WORKSPACE_DIR):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("venv", "build", "dist", "__pycache__", "downloads", "logs")]
                for f in files:
                    if f.endswith(".py") or f == "requirements.txt":
                        p = os.path.join(root, f)
                        try:
                            mtimes[p] = os.path.getmtime(p)
                        except OSError:
                            pass
            return mtimes

        last_mtimes = get_mtimes()
        self.start_process()

        try:
            while True:
                time.sleep(0.35)
                current_mtimes = get_mtimes()

                changed = []
                for p, mtime in current_mtimes.items():
                    if p not in last_mtimes or mtime > last_mtimes[p]:
                        changed.append(p)

                if changed:
                    last_mtimes = current_mtimes
                    for p in changed:
                        self.on_file_changed(p)
        except KeyboardInterrupt:
            pass

    def run(self):
        print("\n\033[96m" + "=" * 64)
        print("   AGENTIC WEB - LIVE AUTO-RELOAD & AUTO-DEPENDENCY ENGINE   ")
        print(f"   Monitoring workspace with {self.settle_delay}s edit settling delay   ")
        print(f"   Auto-Install to VirtualEnv: {get_venv_python()}   ")
        print("=" * 64 + "\033[0m\n")

        # Try watchdog first, fallback to polling
        if not self.run_with_watchdog():
            self.run_with_polling()

        with self._lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
        kill_process_tree(self.proc)
        print("\033[92m[OK] Auto-reload watcher closed cleanly.\033[0m")


def run_watchdog_cli(cmd_list, delay: float = 1.2) -> bool:
    """Helper entry point for --watch / --dev flags."""
    # Filter out sys.executable if passed in cmd_list
    clean_cmd = [c for c in cmd_list if not c.endswith("python.exe") and not c.endswith("python")]
    if not clean_cmd:
        clean_cmd = ["app.py"]
    reloader = LiveReloader(clean_cmd, settle_delay=delay)
    return reloader.run_with_watchdog()


def run_python_watcher(cmd_list, delay: float = 1.2):
    """Fallback polling entry point."""
    clean_cmd = [c for c in cmd_list if not c.endswith("python.exe") and not c.endswith("python")]
    if not clean_cmd:
        clean_cmd = ["app.py"]
    reloader = LiveReloader(clean_cmd, settle_delay=delay)
    reloader.run_with_polling()


if __name__ == "__main__":
    args = sys.argv[1:]
    delay = 1.2
    clean_args = []

    i = 0
    while i < len(args):
        if args[i] in ("--delay", "-d") and i + 1 < len(args):
            try:
                delay = float(args[i + 1])
                i += 2
                continue
            except ValueError:
                pass
        clean_args.append(args[i])
        i += 1

    if "--cli" in clean_args:
        cmd = ["main.py"] + [a for a in clean_args if a != "--cli"]
    elif "--gui" in clean_args:
        cmd = ["app.py"] + [a for a in clean_args if a != "--gui"]
    elif clean_args:
        cmd = clean_args
    else:
        cmd = ["app.py"]  # Default to Desktop GUI app

    reloader = LiveReloader(cmd, settle_delay=delay)
    reloader.run()
