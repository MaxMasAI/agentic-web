"""
system/cli_launcher.py - Platform-Agnostic CLI Command & Workstation Controller.

Provides cross-platform terminal orchestration commands for starting GUI, CLI orchestrator,
development mode, test execution, and window layout fixing on Windows, macOS, and Linux.
"""

import os
import sys
import argparse
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cmd_gui(args):
    """Launches the PySide6 Desktop Workstation GUI."""
    print("[*] Launching Agentic Web PySide6 Desktop Console...")
    app_py = os.path.join(PROJECT_ROOT, "app.py")
    subprocess.run([sys.executable, app_py])


def cmd_cli(args):
    """Executes the CLI Multi-Agent Orchestrator."""
    main_py = os.path.join(PROJECT_ROOT, "core", "main.py")
    task = " ".join(args.task) if args.task else ""
    cmd = [sys.executable, main_py]
    if task:
        cmd.extend(["--task", task])
    subprocess.run(cmd)


def cmd_dev(args):
    """Starts live auto-reloading development runner."""
    dev_py = os.path.join(PROJECT_ROOT, "dev.py")
    subprocess.run([sys.executable, dev_py])


def cmd_test(args):
    """Runs all unit and integration test suites."""
    print("[*] Running Agentic Web Test Suites...")
    subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests"])


def cmd_layout_fix(args):
    """Fixes and snaps desktop windows into FancyZones."""
    from system.fancyzones_manager import fix_system_layout
    layout = args.layout or "3_columns"
    spacing = args.spacing or 16
    windows = args.windows or ["Gemini", "DeepSeek", "Claude"]
    print(f"[*] Snapping windows {windows} into '{layout}' layout (spacing: {spacing}px)...")
    res = fix_system_layout(windows, layout_name=layout, spacing=spacing)
    print(f"[OK] Layout result: {res}")


def cmd_pids(args):
    """Lists or terminates active tracked agent process trees."""
    from system.pid_tracker import get_tracked_pids, cleanup_tracked_pids
    if args.clean:
        print("[*] Terminating all tracked agent processes...")
        cleanup_tracked_pids()
    else:
        pids = get_tracked_pids()
        print(f"[*] Active Tracked Process IDs: {pids}")


def main():
    parser = argparse.ArgumentParser(
        prog="agentic",
        description="Agentic Web Workstation - Cross-Platform CLI Command Interface"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # GUI Command
    p_gui = subparsers.add_parser("gui", help="Launch desktop PySide6 workstation")
    p_gui.set_defaults(func=cmd_gui)

    # CLI Orchestrator Command
    p_cli = subparsers.add_parser("cli", help="Execute multi-agent CLI orchestrator")
    p_cli.add_argument("task", nargs="*", help="Optional prompt task description")
    p_cli.set_defaults(func=cmd_cli)

    # Dev Command
    p_dev = subparsers.add_parser("dev", help="Start auto-reloading development runner")
    p_dev.set_defaults(func=cmd_dev)

    # Test Command
    p_test = subparsers.add_parser("test", help="Run comprehensive unit test suites")
    p_test.set_defaults(func=cmd_test)

    # Layout Fix Command
    p_layout = subparsers.add_parser("layout-fix", help="Snap windows into FancyZones")
    p_layout.add_argument("--layout", default="3_columns", help="Layout template name")
    p_layout.add_argument("--spacing", type=int, default=16, help="Spacing in pixels")
    p_layout.add_argument("--windows", nargs="*", help="List of window title keywords")
    p_layout.set_defaults(func=cmd_layout_fix)

    # PIDs Command
    p_pids = subparsers.add_parser("pids", help="Manage tracked browser process trees")
    p_pids.add_argument("--clean", action="store_true", help="Terminate all tracked process trees")
    p_pids.set_defaults(func=cmd_pids)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
