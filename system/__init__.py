"""
system/ - Antigravity OS & Desktop System Automation Package.

Consolidates all system-level modules:
- fancyzones_manager: PowerToys FancyZones window layout engine & system window layout fixer.
- system_cursor: Antigravity-styled visual desktop & browser system cursor overlay.
- system_os_service: OS shell command execution, environment, and system diagnostics.
- system_app_launcher: Autonomous native desktop application launcher & window controller.
- mouse_keyboard_service: OS-level mouse movement, clicking, typing, and screen capture.
- pid_tracker: Process tree tracking, PID persistence, and clean process tree termination.
- system_prompts: System prompt catalogs and extended instructions.
"""

from system.fancyzones_manager import (
    FancyZone,
    get_screen_resolution_and_workarea,
    get_powertoys_config_dir,
    load_powertoys_custom_layouts,
    load_powertoys_applied_layout,
    calculate_3_columns_layout,
    calculate_dynamic_columns_layout,
    calculate_priority_grid_layout,
    calculate_grid_4_layout,
    calculate_focus_3_layout,
    get_fancyzones_layout,
    calculate_zone_bounds,
    snap_window_by_title_keyword,
    snap_system_app_to_zone,
    fix_system_layout
)
from system.system_cursor import (
    inject_system_cursor,
    animate_system_cursor_move,
    simulate_system_cursor_click,
    DesktopSystemCursorOverlay
)
from system.system_os_service import SystemOSService
from system.system_app_launcher import is_system_app_task, launch_system_application
from system.mouse_keyboard_service import MouseKeyboardService
from system.pid_tracker import (
    track_pid,
    get_tracked_pids,
    cleanup_tracked_pids,
    find_pid_on_port,
    kill_pid_tree
)
from system.issue_reporter import (
    GitHubIssueReporter,
    CrashReport,
    get_issue_reporter,
    install_crash_reporter,
    global_exception_handler
)

__all__ = [
    # FancyZones Layout Engine & Fixer
    "FancyZone",
    "get_screen_resolution_and_workarea",
    "get_powertoys_config_dir",
    "load_powertoys_custom_layouts",
    "load_powertoys_applied_layout",
    "calculate_3_columns_layout",
    "calculate_dynamic_columns_layout",
    "calculate_priority_grid_layout",
    "calculate_grid_4_layout",
    "calculate_focus_3_layout",
    "get_fancyzones_layout",
    "calculate_zone_bounds",
    "snap_window_by_title_keyword",
    "snap_system_app_to_zone",
    "fix_system_layout",
    # System Cursor
    "inject_system_cursor",
    "animate_system_cursor_move",
    "simulate_system_cursor_click",
    "DesktopSystemCursorOverlay",
    # System OS & Launchers
    "SystemOSService",
    "is_system_app_task",
    "launch_system_application",
    "MouseKeyboardService",
    # PID Tracker
    "track_pid",
    "get_tracked_pids",
    "cleanup_tracked_pids",
    "find_pid_on_port",
    "kill_pid_tree",
    # GitHub Crash & Issue Reporter
    "GitHubIssueReporter",
    "CrashReport",
    "get_issue_reporter",
    "install_crash_reporter",
    "global_exception_handler"
]

