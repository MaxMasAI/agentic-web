"""
system/fancyzones_manager.py - System & Desktop FancyZones Window Layout Engine.

Calculates precise window geometry, margins, and column layouts matching
Microsoft PowerToys FancyZones (3-Columns, 'yeong-sil musical', Priority Grid, 2-Columns, etc.)
and provides system-level layout fixing and window snapping for desktop apps, browsers, and OS utilities.
"""

import os
import sys
import json
import ctypes
from typing import Dict, List, Tuple, Any, Optional

CYAN  = "\033[96m"
GREEN = "\033[92m"
YELLOW= "\033[93m"
RESET = "\033[0m"


class FancyZone:
    """Represents a single target zone bounding box on the screen."""
    def __init__(self, x: int, y: int, width: int, height: int, zone_index: int = 0, name: str = ""):
        self.x = max(0, int(round(x)))
        self.y = max(0, int(round(y)))
        self.width = max(100, int(round(width)))
        self.height = max(100, int(round(height)))
        self.zone_index = zone_index
        self.name = name or f"Zone {zone_index + 1}"

    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Returns (left, top, width, height) tuple."""
        return (self.x, self.y, self.width, self.height)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "zone_index": self.zone_index,
            "name": self.name
        }

    def __repr__(self) -> str:
        return f"<FancyZone #{self.zone_index} [{self.name}] x={self.x}, y={self.y}, w={self.width}, h={self.height}>"


def get_screen_resolution_and_workarea() -> Tuple[int, int, int, int]:
    """
    Returns (left, top, width, height) of the primary display workarea (excluding taskbar)
    in physical pixels on Windows.
    """
    if sys.platform == "win32":
        try:
            from ctypes import wintypes
            user32 = ctypes.windll.user32
            try:
                # Enable DPI awareness to obtain physical pixel boundaries
                user32.SetProcessDPIAware()
            except Exception:
                pass
            rect = wintypes.RECT()
            # SPI_GETWORKAREA = 0x0030
            if user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                if w > 0 and h > 0:
                    return (rect.left, rect.top, w, h)
            # Fallback to GetSystemMetrics
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            if sw > 0 and sh > 0:
                return (0, 0, sw, max(200, sh - 48))
        except Exception:
            pass
    return (0, 0, 1920, 1032)


def get_powertoys_config_dir() -> Optional[str]:
    """Returns the local AppData directory for PowerToys FancyZones if present."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    pt_dir = os.path.join(local_app_data, "Microsoft", "PowerToys", "FancyZones")
    if os.path.isdir(pt_dir):
        return pt_dir
    return None


def load_powertoys_custom_layouts() -> List[Dict[str, Any]]:
    """Loads all custom layouts created by the user in PowerToys FancyZones."""
    pt_dir = get_powertoys_config_dir()
    if not pt_dir:
        return []
    custom_file = os.path.join(pt_dir, "custom-layouts.json")
    if not os.path.exists(custom_file):
        return []
    try:
        with open(custom_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("custom-layouts", [])
    except Exception as e:
        print(f"{YELLOW}[FancyZones] Could not read custom-layouts.json: {e}{RESET}")
        return []


def load_powertoys_applied_layout() -> Optional[Dict[str, Any]]:
    """Loads the currently active/applied layout from PowerToys."""
    pt_dir = get_powertoys_config_dir()
    if not pt_dir:
        return None
    applied_file = os.path.join(pt_dir, "applied-layouts.json")
    if not os.path.exists(applied_file):
        return None
    try:
        with open(applied_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            applied_list = data.get("applied-layouts", [])
            if applied_list:
                return applied_list[0].get("applied-layout")
    except Exception as e:
        print(f"{YELLOW}[FancyZones] Could not read applied-layouts.json: {e}{RESET}")
    return None


def calculate_3_columns_layout(
    screen_w: int,
    screen_h: int,
    spacing: int = 16,
    show_spacing: bool = True,
    taskbar_margin: int = 40
) -> List[FancyZone]:
    """
    Calculates the 3-column FancyZone layout (Left, Middle, Right)
    spanning the entire screen width with precise spacing and zero overlapping.
    """
    usable_h = max(200, screen_h - taskbar_margin if taskbar_margin > 0 else screen_h)
    
    if not show_spacing or spacing <= 0:
        w0 = screen_w // 3
        w1 = screen_w // 3
        w2 = screen_w - (w0 + w1)
        return [
            FancyZone(0, 0, w0, usable_h, 0, "Left Column"),
            FancyZone(w0, 0, w1, usable_h, 1, "Middle Column"),
            FancyZone(w0 + w1, 0, w2, usable_h, 2, "Right Column")
        ]

    # Total horizontal padding: 2 outer margins + 2 inner gaps = 4 * spacing
    total_gaps_w = spacing * 4
    avail_w = screen_w - total_gaps_w
    col_w = max(100, avail_w // 3)
    zone_h = max(100, usable_h - (spacing * 2))
    zone_y = spacing

    z0_x = spacing
    z1_x = z0_x + col_w + spacing
    z2_x = z1_x + col_w + spacing
    z2_w = screen_w - z2_x - spacing  # absorbs remainder to cover screen edge perfectly

    return [
        FancyZone(z0_x, zone_y, col_w, zone_h, 0, "Left Column (Leader/Primary)"),
        FancyZone(z1_x, zone_y, col_w, zone_h, 1, "Middle Column (Specialist 1)"),
        FancyZone(z2_x, zone_y, z2_w, zone_h, 2, "Right Column (Specialist 2)")
    ]


def calculate_dynamic_columns_layout(
    count: int,
    screen_w: int,
    screen_h: int,
    spacing: int = 16,
    show_spacing: bool = True,
    taskbar_margin: int = 40
) -> List[FancyZone]:
    """Calculates N equal vertical column FancyZones across the screen with spacing."""
    if count <= 0:
        count = 1
    if count == 3:
        return calculate_3_columns_layout(screen_w, screen_h, spacing, show_spacing, taskbar_margin)

    usable_h = max(200, screen_h - taskbar_margin if taskbar_margin > 0 else screen_h)

    if not show_spacing or spacing <= 0:
        col_w = screen_w // count
        zones = []
        for i in range(count):
            x = col_w * i
            w = col_w if i < count - 1 else (screen_w - x)
            zones.append(FancyZone(x, 0, w, usable_h, i, f"Column {i+1}"))
        return zones

    total_gaps_w = spacing * (count + 1)
    avail_w = screen_w - total_gaps_w
    col_w = max(80, avail_w // count)
    zone_h = max(100, usable_h - (spacing * 2))
    zone_y = spacing

    zones = []
    for i in range(count):
        x = spacing + i * (col_w + spacing)
        w = col_w if i < count - 1 else (screen_w - x - spacing)
        zones.append(FancyZone(x, zone_y, w, zone_h, i, f"Column {i+1}"))
    return zones


def calculate_priority_grid_layout(
    screen_w: int,
    screen_h: int,
    spacing: int = 16,
    taskbar_margin: int = 40
) -> List[FancyZone]:
    """
    Priority Grid layout:
    - Zone 0 (Left 50%): Primary Leader / Main Window
    - Zone 1 (Top Right 50%): Secondary Window 1
    - Zone 2 (Bottom Right 50%): Secondary Window 2
    """
    usable_h = max(200, screen_h - taskbar_margin if taskbar_margin > 0 else screen_h)
    zone_h_half = max(80, (usable_h - (spacing * 3)) // 2)
    left_w = max(100, (screen_w - (spacing * 3)) // 2)
    right_x = spacing + left_w + spacing
    right_w = screen_w - right_x - spacing

    return [
        FancyZone(spacing, spacing, left_w, usable_h - (spacing * 2), 0, "Primary Main Zone"),
        FancyZone(right_x, spacing, right_w, zone_h_half, 1, "Upper Stack Zone"),
        FancyZone(right_x, spacing + zone_h_half + spacing, right_w, zone_h_half, 2, "Lower Stack Zone")
    ]


def calculate_grid_4_layout(
    screen_w: int,
    screen_h: int,
    spacing: int = 16,
    taskbar_margin: int = 40
) -> List[FancyZone]:
    """2x2 Quadrant Grid Layout."""
    usable_h = max(200, screen_h - taskbar_margin if taskbar_margin > 0 else screen_h)
    col_w = max(100, (screen_w - (spacing * 3)) // 2)
    row_h = max(80, (usable_h - (spacing * 3)) // 2)

    return [
        FancyZone(spacing, spacing, col_w, row_h, 0, "Top-Left Zone"),
        FancyZone(spacing * 2 + col_w, spacing, col_w, row_h, 1, "Top-Right Zone"),
        FancyZone(spacing, spacing * 2 + row_h, col_w, row_h, 2, "Bottom-Left Zone"),
        FancyZone(spacing * 2 + col_w, spacing * 2 + row_h, col_w, row_h, 3, "Bottom-Right Zone")
    ]


def calculate_focus_3_layout(
    screen_w: int,
    screen_h: int,
    spacing: int = 16,
    taskbar_margin: int = 40
) -> List[FancyZone]:
    """Focus Layout: 25% Left, 50% Center Main, 25% Right."""
    usable_h = max(200, screen_h - taskbar_margin if taskbar_margin > 0 else screen_h)
    total_gaps = spacing * 4
    avail_w = max(200, screen_w - total_gaps)
    side_w = avail_w // 4
    center_w = avail_w - (side_w * 2)
    zone_h = max(100, usable_h - (spacing * 2))

    z0_x = spacing
    z1_x = z0_x + side_w + spacing
    z2_x = z1_x + center_w + spacing

    return [
        FancyZone(z0_x, spacing, side_w, zone_h, 0, "Left Flank"),
        FancyZone(z1_x, spacing, center_w, zone_h, 1, "Center Focus"),
        FancyZone(z2_x, spacing, screen_w - z2_x - spacing, zone_h, 2, "Right Flank")
    ]


def get_fancyzones_layout(
    layout_name: str = "auto",
    total_agents: int = 3,
    screen_w: int = 1920,
    screen_h: int = 1080,
    spacing: int = 16,
    show_spacing: bool = True,
    taskbar_margin: int = 40
) -> List[FancyZone]:
    """
    Main layout resolver. Resolves appropriate FancyZone bounding boxes
    based on requested layout template, active PowerToys configuration, and count.
    """
    clean_name = (layout_name or "auto").lower().strip()

    # 1. Check PowerToys custom layouts if requested or auto
    if clean_name in ["auto", "powertoys", "yeong_sil_musical", "yeong-sil musical"]:
        custom_layouts = load_powertoys_custom_layouts()
        for cl in custom_layouts:
            c_name = cl.get("name", "").strip().lower()
            if "yeong-sil" in c_name or "musical" in c_name or clean_name in ["yeong_sil_musical", "yeong-sil musical"]:
                info = cl.get("info", {})
                sp = info.get("spacing", spacing)
                sh_sp = info.get("show-spacing", show_spacing)
                cols = info.get("columns", 3)
                if cols == 3 or total_agents == 3:
                    return calculate_3_columns_layout(screen_w, screen_h, spacing=sp, show_spacing=sh_sp, taskbar_margin=taskbar_margin)
                return calculate_dynamic_columns_layout(total_agents or cols, screen_w, screen_h, spacing=sp, show_spacing=sh_sp, taskbar_margin=taskbar_margin)

    # 2. Template Matches
    if clean_name in ["priority_grid", "priority", "leader_stack"]:
        return calculate_priority_grid_layout(screen_w, screen_h, spacing=spacing, taskbar_margin=taskbar_margin)
    elif clean_name in ["focus", "focus_3"]:
        return calculate_focus_3_layout(screen_w, screen_h, spacing=spacing, taskbar_margin=taskbar_margin)
    elif clean_name in ["grid", "grid_4", "2x2"]:
        return calculate_grid_4_layout(screen_w, screen_h, spacing=spacing, taskbar_margin=taskbar_margin)
    elif clean_name in ["columns_2", "split_2", "2_columns"]:
        return calculate_dynamic_columns_layout(2, screen_w, screen_h, spacing=spacing, show_spacing=show_spacing, taskbar_margin=taskbar_margin)
    elif clean_name in ["columns_3", "3_columns", "columns", "yeong-sil musical", "auto"]:
        if total_agents == 3 or total_agents <= 0:
            return calculate_3_columns_layout(screen_w, screen_h, spacing=spacing, show_spacing=show_spacing, taskbar_margin=taskbar_margin)
        return calculate_dynamic_columns_layout(total_agents, screen_w, screen_h, spacing=spacing, show_spacing=show_spacing, taskbar_margin=taskbar_margin)
    else:
        return calculate_dynamic_columns_layout(total_agents, screen_w, screen_h, spacing=spacing, show_spacing=show_spacing, taskbar_margin=taskbar_margin)


def calculate_zone_bounds(
    agent_index: int,
    total_agents: int = 3,
    screen_w: int = 1920,
    screen_h: int = 1080,
    layout_name: str = "auto",
    spacing: int = 16,
    show_spacing: bool = True,
    taskbar_margin: int = 40
) -> Tuple[int, int, int, int]:
    """Returns (left, top, width, height) for a specific zone index within the layout."""
    zones = get_fancyzones_layout(
        layout_name=layout_name,
        total_agents=total_agents,
        screen_w=screen_w,
        screen_h=screen_h,
        spacing=spacing,
        show_spacing=show_spacing,
        taskbar_margin=taskbar_margin
    )
    if not zones:
        return (0, 0, screen_w, screen_h)

    idx = max(0, min(agent_index, len(zones) - 1))
    return zones[idx].bounds


# ─────────────────────────────────────────────────────────────────────────────
#  Native Windows System Window Snapping & Layout Fixing Engine
# ─────────────────────────────────────────────────────────────────────────────
def snap_window_by_title_keyword(title_keyword: str, x: int, y: int, width: int, height: int) -> bool:
    """
    Finds native top-level window by title keyword (e.g. 'Notepad', 'Calculator', 'Gemini', 'VS Code')
    and positions it with Win32 SetWindowPos with zero overlap.
    """
    if sys.platform != "win32":
        return False
    try:
        from ctypes import wintypes
        user32 = ctypes.windll.user32
        
        SWP_NOZORDER = 0x0004
        SWP_SHOWWINDOW = 0x0040
        SWP_FRAMECHANGED = 0x0020
        SW_RESTORE = 9
        
        found = False

        def enum_windows_callback(hwnd, extra):
            nonlocal found
            if not user32.IsWindowVisible(hwnd):
                return True
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
                kw = title_keyword.lower().strip()
                if kw in title.lower() or (kw == "chatgpt" and "openai" in title.lower()):
                    user32.ShowWindow(hwnd, SW_RESTORE)
                    user32.SetWindowPos(hwnd, 0, int(x), int(y), int(width), int(height), SWP_NOZORDER | SWP_SHOWWINDOW | SWP_FRAMECHANGED)
                    found = True
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
        return found
    except Exception as e:
        return False


def snap_system_app_to_zone(
    app_name_or_keyword: str,
    zone_index: int = 0,
    total_zones: int = 3,
    layout_name: str = "auto",
    spacing: int = 16
) -> bool:
    """
    Snaps any native Windows desktop application (Notepad, Calculator, VS Code, Task Manager, Explorer, etc.)
    into a designated FancyZone slot.
    """
    _, _, screen_w, screen_h = get_screen_resolution_and_workarea()
    left, top, width, height = calculate_zone_bounds(
        agent_index=zone_index,
        total_agents=total_zones,
        screen_w=screen_w,
        screen_h=screen_h,
        layout_name=layout_name,
        spacing=spacing,
        show_spacing=True,
        taskbar_margin=40
    )
    return snap_window_by_title_keyword(app_name_or_keyword, left, top, width, height)


def fix_system_layout(
    app_keywords: Optional[List[str]] = None,
    layout_name: str = "auto",
    spacing: int = 16
) -> Dict[str, Any]:
    """
    Fixes and arranges multiple desktop system windows side-by-side into clean FancyZones.
    
    Args:
        app_keywords: Optional list of window title keywords (e.g. ["Notepad", "Calculator", "Command Prompt"]).
                      If None or empty, automatically snaps active known agent/system windows.
        layout_name: Layout template ("3_columns", "priority_grid", "columns_2", etc.).
        spacing: Gap spacing in pixels (default 16px).
    """
    if not app_keywords:
        app_keywords = ["Gemini", "DeepSeek", "Claude"]

    _, _, screen_w, screen_h = get_screen_resolution_and_workarea()
    total = len(app_keywords)
    results = {}

    for idx, kw in enumerate(app_keywords):
        left, top, width, height = calculate_zone_bounds(
            agent_index=idx,
            total_agents=total,
            screen_w=screen_w,
            screen_h=screen_h,
            layout_name=layout_name,
            spacing=spacing,
            show_spacing=True,
            taskbar_margin=40
        )
        snapped = snap_window_by_title_keyword(kw, left, top, width, height)
        results[kw] = {
            "snapped": snapped,
            "bounds": (left, top, width, height),
            "zone_index": idx
        }

    return {
        "success": True,
        "screen_resolution": (screen_w, screen_h),
        "layout_applied": layout_name,
        "spacing": spacing,
        "windows": results
    }
