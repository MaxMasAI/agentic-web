"""
services/system_app_launcher.py - Native Windows Desktop & System Application Launcher.

Detects requests to open/start/launch native Windows applications, system utilities,
and desktop software (e.g., Task Manager, Notepad, Calculator, VS Code, Settings, Spotify, etc.)
and launches them directly on the OS without routing to web searches.
"""

import os
import sys
import re
import shutil
import subprocess
from typing import Optional, Tuple, Dict, Any

# Map of common aliases to their Windows executable, control panel command, or URI scheme
KNOWN_SYSTEM_APPS: Dict[str, Dict[str, str]] = {
    # System Utilities & Diagnostics
    "task manager": {"cmd": "taskmgr.exe", "name": "Task Manager", "type": "System Utility"},
    "taskmanger": {"cmd": "taskmgr.exe", "name": "Task Manager", "type": "System Utility"},
    "taskmgr": {"cmd": "taskmgr.exe", "name": "Task Manager", "type": "System Utility"},
    "task man": {"cmd": "taskmgr.exe", "name": "Task Manager", "type": "System Utility"},
    "notepad": {"cmd": "notepad.exe", "name": "Notepad", "type": "Text Editor"},
    "calculator": {"cmd": "calc.exe", "name": "Calculator", "type": "Utility"},
    "calc": {"cmd": "calc.exe", "name": "Calculator", "type": "Utility"},
    "paint": {"cmd": "mspaint.exe", "name": "Paint", "type": "Graphics Tool"},
    "mspaint": {"cmd": "mspaint.exe", "name": "Paint", "type": "Graphics Tool"},
    "explorer": {"cmd": "explorer.exe", "name": "File Explorer", "type": "System Utility"},
    "file explorer": {"cmd": "explorer.exe", "name": "File Explorer", "type": "System Utility"},
    "files": {"cmd": "explorer.exe", "name": "File Explorer", "type": "System Utility"},
    "my computer": {"cmd": "explorer.exe", "name": "File Explorer", "type": "System Utility"},
    "this pc": {"cmd": "explorer.exe", "name": "File Explorer", "type": "System Utility"},
    "cmd": {"cmd": "cmd.exe /c start cmd.exe", "name": "Command Prompt", "type": "Shell Terminal"},
    "command prompt": {"cmd": "cmd.exe /c start cmd.exe", "name": "Command Prompt", "type": "Shell Terminal"},
    "terminal": {"cmd": "wt.exe", "fallback": "cmd.exe /c start cmd.exe", "name": "Windows Terminal", "type": "Shell Terminal"},
    "windows terminal": {"cmd": "wt.exe", "fallback": "cmd.exe /c start cmd.exe", "name": "Windows Terminal", "type": "Shell Terminal"},
    "powershell": {"cmd": "powershell.exe", "name": "PowerShell", "type": "Shell Terminal"},
    "control panel": {"cmd": "control.exe", "name": "Control Panel", "type": "System Settings"},
    "control": {"cmd": "control.exe", "name": "Control Panel", "type": "System Settings"},
    "settings": {"cmd": "start ms-settings:", "name": "Windows Settings", "type": "System Settings"},
    "windows settings": {"cmd": "start ms-settings:", "name": "Windows Settings", "type": "System Settings"},
    "snipping tool": {"cmd": "snippingtool.exe", "name": "Snipping Tool", "type": "Screenshot Tool"},
    "snip": {"cmd": "snippingtool.exe", "name": "Snipping Tool", "type": "Screenshot Tool"},
    "device manager": {"cmd": "devmgmt.msc", "name": "Device Manager", "type": "Management Console"},
    "disk management": {"cmd": "diskmgmt.msc", "name": "Disk Management", "type": "Management Console"},
    "resource monitor": {"cmd": "resmon.exe", "name": "Resource Monitor", "type": "Diagnostics Tool"},
    "resmon": {"cmd": "resmon.exe", "name": "Resource Monitor", "type": "Diagnostics Tool"},
    "event viewer": {"cmd": "eventvwr.msc", "name": "Event Viewer", "type": "Diagnostics Tool"},
    "services": {"cmd": "services.msc", "name": "Services Console", "type": "Management Console"},
    "services.msc": {"cmd": "services.msc", "name": "Services Console", "type": "Management Console"},
    "registry editor": {"cmd": "regedit.exe", "name": "Registry Editor", "type": "System Utility"},
    "regedit": {"cmd": "regedit.exe", "name": "Registry Editor", "type": "System Utility"},
    "system information": {"cmd": "msinfo32.exe", "name": "System Information", "type": "Diagnostics Tool"},
    "character map": {"cmd": "charmap.exe", "name": "Character Map", "type": "Utility"},
    "magnifier": {"cmd": "magnify.exe", "name": "Magnifier", "type": "Accessibility Tool"},
    "on screen keyboard": {"cmd": "osk.exe", "name": "On-Screen Keyboard", "type": "Accessibility Tool"},
    "camera": {"cmd": "start microsoft.windows.camera:", "name": "Camera App", "type": "Media App"},
    "photos": {"cmd": "start ms-photos:", "name": "Photos App", "type": "Media App"},
    "clock": {"cmd": "start ms-clock:", "name": "Clock & Alarms", "type": "Utility"},
    "alarms": {"cmd": "start ms-clock:", "name": "Clock & Alarms", "type": "Utility"},
    "wifi settings": {"cmd": "start ms-settings:network-wifi", "name": "Wi-Fi Settings", "type": "System Settings"},
    "bluetooth settings": {"cmd": "start ms-settings:bluetooth", "name": "Bluetooth Settings", "type": "System Settings"},
    "sound settings": {"cmd": "start ms-settings:sound", "name": "Sound Settings", "type": "System Settings"},
    "display settings": {"cmd": "start ms-settings:display", "name": "Display Settings", "type": "System Settings"},
    "windows update": {"cmd": "start ms-settings:windowsupdate", "name": "Windows Update", "type": "System Settings"},

    # Desktop Software & Applications
    "vscode": {"cmd": "code", "name": "Visual Studio Code", "type": "Developer IDE"},
    "vs code": {"cmd": "code", "name": "Visual Studio Code", "type": "Developer IDE"},
    "visual studio code": {"cmd": "code", "name": "Visual Studio Code", "type": "Developer IDE"},
    "code": {"cmd": "code", "name": "Visual Studio Code", "type": "Developer IDE"},
    "word": {"cmd": "winword.exe", "name": "Microsoft Word", "type": "Office Suite"},
    "ms word": {"cmd": "winword.exe", "name": "Microsoft Word", "type": "Office Suite"},
    "microsoft word": {"cmd": "winword.exe", "name": "Microsoft Word", "type": "Office Suite"},
    "excel": {"cmd": "excel.exe", "name": "Microsoft Excel", "type": "Office Suite"},
    "ms excel": {"cmd": "excel.exe", "name": "Microsoft Excel", "type": "Office Suite"},
    "microsoft excel": {"cmd": "excel.exe", "name": "Microsoft Excel", "type": "Office Suite"},
    "powerpoint": {"cmd": "powerpnt.exe", "name": "Microsoft PowerPoint", "type": "Office Suite"},
    "ppt": {"cmd": "powerpnt.exe", "name": "Microsoft PowerPoint", "type": "Office Suite"},
    "spotify": {"cmd": "start spotify:", "name": "Spotify", "type": "Media Music App"},
    "discord": {"cmd": "start discord:", "name": "Discord", "type": "Communication"},
    "telegram": {"cmd": "telegram.exe", "name": "Telegram", "type": "Communication"},
    "whatsapp": {"cmd": "start whatsapp:", "name": "WhatsApp", "type": "Communication"},
    "steam": {"cmd": "start steam:", "name": "Steam", "type": "Gaming Client"},
    "vlc": {"cmd": "vlc.exe", "name": "VLC Media Player", "type": "Media Player"},
    "brave": {"cmd": "brave.exe", "name": "Brave Browser", "type": "Web Browser"},
    "obs": {"cmd": "obs64.exe", "name": "OBS Studio", "type": "Broadcast Studio"},
    "git bash": {"cmd": "git-bash.exe", "name": "Git Bash", "type": "Developer Tool"},
    "github desktop": {"cmd": "GitHubDesktop.exe", "name": "GitHub Desktop", "type": "Developer Tool"},
}


def clean_app_request(task: str) -> str:
    """Strips command verbs ('open', 'launch', 'start', 'run') and filler words."""
    if not task:
        return ""
    t = task.strip().lower()
    
    # Remove leading phrases
    t = re.sub(r"^(please\s+|can\s+you\s+)?(open|launch|start|run|execute|bring\s+up)\s+(the\s+|my\s+|a\s+|an\s+|in\s+system\s+|system\s+)?", "", t).strip()
    # Remove trailing phrases
    t = re.sub(r"\s+(app|application|software|utility|program|tool|in\s+windows|on\s+system|on\s+my\s+pc|on\s+pc)$", "", t).strip()
    return t


def is_system_app_task(task: str) -> bool:
    """
    Determines whether a user task is a request to open/launch a native system utility
    or desktop application.
    """
    if not task:
        return False
    t = task.strip().lower()

    # Exclude coding/script generation requests
    if any(w in t for w in ["write a script", "write code", "how to code", "implement in python", "create a function"]):
        return False

    # Exclude explicit website URLs or internet searches
    if any(p in t for p in ["http://", "https://", ".com", ".org", ".net", ".io", "search on google", "search google for"]):
        return False

    cleaned = clean_app_request(t)
    if not cleaned:
        return False

    # Check known system app registry
    if cleaned in KNOWN_SYSTEM_APPS:
        return True

    # Check for direct executable commands (e.g., 'taskmgr', 'notepad', 'calc')
    if re.match(r"^(open|launch|start|run)\s+[a-zA-Z0-9_\-\.]{2,20}$", t, re.IGNORECASE):
        # Look for matching .lnk in Start Menu or on PATH
        match_path = find_installed_app_path(cleaned)
        if match_path:
            return True

    return False


def find_installed_app_path(app_query: str) -> Optional[str]:
    """
    Dynamically scans Windows Start Menu shortcuts and system PATH to locate any installed app.
    """
    q = app_query.lower().strip()
    if not q:
        return None

    # 1. Check direct system PATH
    direct_which = shutil.which(q) or shutil.which(f"{q}.exe")
    if direct_which:
        return direct_which

    # 2. Check Windows Start Menu folders for matching .lnk shortcuts
    search_dirs = [
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        r"C:\Users\Public\Desktop",
        os.path.join(os.environ.get("USERPROFILE", ""), "Desktop"),
    ]

    for s_dir in search_dirs:
        if not os.path.exists(s_dir):
            continue
        try:
            for root, _, files in os.walk(s_dir):
                for f in files:
                    if f.lower().endswith((".lnk", ".exe")):
                        f_name = os.path.splitext(f)[0].lower()
                        if q == f_name or q in f_name or f_name.startswith(q):
                            return os.path.join(root, f)
        except Exception:
            continue

    return None


def execute_system_app_launch(task: str) -> str:
    """
    Launches the requested system utility or desktop application on Windows.
    Returns a formatted deliverable status message.
    """
    cleaned = clean_app_request(task)
    app_info = KNOWN_SYSTEM_APPS.get(cleaned)
    
    app_name = cleaned.title()
    app_type = "Desktop Software"
    launched = False
    exec_cmd = ""
    error_msg = ""

    # 1. Launch known app entry
    if app_info:
        app_name = app_info["name"]
        app_type = app_info.get("type", "System Utility")
        exec_cmd = app_info["cmd"]

        try:
            from voice.voice_narrator import speak_narrator
            speak_narrator(f"Opening {app_name} on your system now...")
        except Exception:
            pass

        try:
            if exec_cmd.startswith("start "):
                subprocess.Popen(exec_cmd, shell=True)
            else:
                try:
                    subprocess.Popen(exec_cmd, shell=True)
                except Exception:
                    if "fallback" in app_info:
                        subprocess.Popen(app_info["fallback"], shell=True)
            launched = True
        except Exception as e:
            error_msg = str(e)

    # 2. Dynamic lookup for any other installed application
    if not launched:
        app_path = find_installed_app_path(cleaned)
        if app_path:
            app_name = os.path.splitext(os.path.basename(app_path))[0]
            exec_cmd = app_path
            try:
                from voice.voice_narrator import speak_narrator
                speak_narrator(f"Launching {app_name} on your system now...")
            except Exception:
                pass
            try:
                if hasattr(os, "startfile"):
                    os.startfile(app_path)
                else:
                    subprocess.Popen(f'start "" "{app_path}"', shell=True)
                launched = True
            except Exception as e:
                error_msg = str(e)
        else:
            # Fallback direct shell start
            exec_cmd = f"start {cleaned}"
            try:
                subprocess.Popen(exec_cmd, shell=True)
                launched = True
            except Exception as e:
                error_msg = str(e)

    # 3. System Cursor Following & Focus
    cursor_info = ""
    if launched:
        try:
            cursor_pos = follow_system_app_with_cursor(app_name)
            if cursor_pos:
                cursor_info = f"\n🎯 System Cursor: Followed to ({cursor_pos[0]}, {cursor_pos[1]})"
        except Exception:
            pass

    status_icon = "🟢" if launched else "🔴"
    status_text = "Running natively on Windows" if launched else f"Failed to launch ({error_msg})"

    result_summary = (
        f"💻 SYSTEM APPLICATION LAUNCHED\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"▶ Application: {app_name}\n"
        f"⚙️ Command: {exec_cmd}\n"
        f"📁 Category: {app_type}\n"
        f"📱 Status: {status_icon} {status_text}{cursor_info}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    return result_summary


def follow_system_app_with_cursor(app_name: str) -> Optional[Tuple[int, int]]:
    """
    Locates the newly opened application window on the Windows desktop,
    smoothly glides the system mouse cursor over to it, and focuses the app.
    """
    import time
    time.sleep(0.4)  # Brief wait for window creation and display

    target_x = 960
    target_y = 540

    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if hwnd:
                rect = wintypes.RECT()
                if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                    w = rect.right - rect.left
                    h = rect.bottom - rect.top
                    if w > 100 and h > 100:
                        target_x = rect.left + w // 2
                        target_y = rect.top + min(h // 2, 200)
            else:
                # Screen center fallback
                target_x = ctypes.windll.user32.GetSystemMetrics(0) // 2
                target_y = ctypes.windll.user32.GetSystemMetrics(1) // 2

            smooth_move_system_cursor(target_x, target_y, steps=20, duration=0.3)

            # Perform a gentle click to focus the application
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
            time.sleep(0.02)
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
            return (target_x, target_y)
        except Exception:
            pass

    return None


def smooth_move_system_cursor(target_x: int, target_y: int, steps: int = 20, duration: float = 0.3):
    """
    Smoothly glides the native OS mouse cursor to the target coordinates using cubic ease-out.
    """
    if sys.platform != "win32":
        return

    try:
        import ctypes
        import time

        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        pt = POINT()
        ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
        start_x, start_y = pt.x, pt.y

        for i in range(1, steps + 1):
            t = i / steps
            ease = 1 - (1 - t) ** 3  # Ease-out cubic
            cur_x = int(start_x + (target_x - start_x) * ease)
            cur_y = int(start_y + (target_y - start_y) * ease)
            ctypes.windll.user32.SetCursorPos(cur_x, cur_y)
            time.sleep(duration / steps)
    except Exception:
        pass

