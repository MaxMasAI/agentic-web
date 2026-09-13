"""
dev.py - Robust Live Auto-Reload Development Engine.
Watches all '*.py' files in the workspace and restarts the application cleanly
after all file changes have settled (debounced delay).

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

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

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
        self._pending_changes = set()

    def start_process(self):
        with self._lock:
            kill_process_tree(self.proc)
            time.sleep(0.2)
            full_cmd = [sys.executable] + self.target_cmd
            print(f"\033[92m[⚡ Launching Application]:\033[0m {' '.join(full_cmd)}")
            self.proc = subprocess.Popen(full_cmd, cwd=WORKSPACE_DIR)

    def on_file_changed(self, changed_file=""):
        """Accumulates changed files and resets the settling timer so all edits finish before reloading."""
        with self._lock:
            rel = os.path.relpath(changed_file, WORKSPACE_DIR) if changed_file else "code file"
            self._pending_changes.add(rel)

            if self._debounce_timer is not None:
                self._debounce_timer.cancel()

            print(f"\033[93m[⏳ Change in '{rel}'] Waiting {self.settle_delay}s for all file edits to finish...\033[0m")
            self._debounce_timer = threading.Timer(self.settle_delay, self._execute_debounced_restart)
            self._debounce_timer.daemon = True
            self._debounce_timer.start()

    def _execute_debounced_restart(self):
        """Fires only after all file modifications have finished and settled."""
        with self._lock:
            changed_list = ", ".join(sorted(self._pending_changes))
            self._pending_changes.clear()
            self._debounce_timer = None
            print(f"\n\033[96m[🔄 Edits Settled: {changed_list}] Reloading application now...\033[0m")
        self.start_process()

    def run_with_watchdog(self):
        """Uses watchdog Python library if installed."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import PatternMatchingEventHandler

            class PyFileHandler(PatternMatchingEventHandler):
                def __init__(self, reloader):
                    super().__init__(
                        patterns=["*.py"],
                        ignore_patterns=["*/.git/*", "*/venv/*", "*/dist/*", "*/build/*", "*/__pycache__/*", "*/logs/*", "*/downloads/*"],
                        ignore_directories=True
                    )
                    self.reloader = reloader

                def on_any_event(self, event):
                    if event.event_type in ("modified", "created", "deleted", "moved"):
                        src = getattr(event, "dest_path", None) or event.src_path
                        if src.endswith(".py"):
                            self.reloader.on_file_changed(src)

            event_handler = PyFileHandler(self)
            observer = Observer()
            observer.schedule(event_handler, path=WORKSPACE_DIR, recursive=True)
            observer.start()
            print(f"\033[96m[✓] Native Watchdog Engine Active (Debounce Settling: {self.settle_delay}s)\033[0m")

            self.start_process()
            try:
                while True:
                    time.sleep(0.5)
            except KeyboardInterrupt:
                observer.stop()
            observer.join()
            return True
        except ImportError:
            return False

    def run_with_polling(self):
        """Fast cross-platform polling fallback."""
        print(f"\033[96m[✓] Polling Watcher Active (Debounce Settling: {self.settle_delay}s)\033[0m")

        def get_mtimes():
            mtimes = {}
            for root, dirs, files in os.walk(WORKSPACE_DIR):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("venv", "build", "dist", "__pycache__", "downloads", "logs")]
                for f in files:
                    if f.endswith(".py"):
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
        print("   AGENTIC WEB - LIVE AUTO-RELOAD DEVELOPMENT ENGINE   ")
        print(f"   Monitoring workspace with {self.settle_delay}s edit settling delay   ")
        print("=" * 64 + "\033[0m\n")

        # Try watchdog first, fallback to polling
        if not self.run_with_watchdog():
            self.run_with_polling()

        with self._lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
        kill_process_tree(self.proc)
        print("\033[92m[OK] Auto-reload watcher closed cleanly.\033[0m")

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
