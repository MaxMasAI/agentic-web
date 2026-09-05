"""
services/mouse_keyboard_service.py - Mouse and Keyboard Control Plugin Engine
Provides mouse cursor positioning, clicking, scrolling, keyboard typing, key shortcuts, and screen capture.
"""

import os
import sys
import time
import subprocess
import json
from typing import Dict, List, Any, Optional, Tuple


class MouseKeyboardService:
    """
    Mouse and Keyboard Control Service.
    Enables autonomous OS-level mouse navigation, typing, and desktop interaction.
    """
    def __init__(self):
        self._screen_width, self._screen_height = self._get_screen_resolution()

    def _get_screen_resolution(self) -> Tuple[int, int]:
        if sys.platform == "win32":
            try:
                import ctypes
                return (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
            except Exception:
                pass
        return (1920, 1080)

    # 1. Get Mouse Cursor Position
    def get_mouse_position(self) -> Dict[str, Any]:
        if sys.platform == "win32":
            try:
                import ctypes
                class POINT(ctypes.Structure):
                    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
                pt = POINT()
                ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
                return {"success": True, "x": pt.x, "y": pt.y}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": True, "x": 500, "y": 500, "note": "simulated"}

    # 2. Control Mouse Cursor Position
    def move_mouse(self, x: int, y: int) -> Dict[str, Any]:
        x = max(0, min(x, self._screen_width - 1))
        y = max(0, min(y, self._screen_height - 1))

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.user32.SetCursorPos(x, y)
                return {"success": True, "action": "move_mouse", "x": x, "y": y}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": True, "action": "move_mouse", "x": x, "y": y, "note": "simulated"}

    # 3. Control Mouse Clicks
    def mouse_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        double: bool = False
    ) -> Dict[str, Any]:
        if x is not None and y is not None:
            self.move_mouse(x, y)
            time.sleep(0.04)

        if sys.platform == "win32":
            try:
                import ctypes
                # MOUSEEVENTF flags
                # LEFTDOWN: 0x0002, LEFTUP: 0x0004
                # RIGHTDOWN: 0x0008, RIGHTUP: 0x0010
                # MIDDLEDOWN: 0x0020, MIDDLEUP: 0x0040
                if button.lower() == "right":
                    down_flag, up_flag = 0x0008, 0x0010
                elif button.lower() == "middle":
                    down_flag, up_flag = 0x0020, 0x0040
                else:
                    down_flag, up_flag = 0x0002, 0x0004

                ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
                time.sleep(0.02)
                ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)

                if double:
                    time.sleep(0.08)
                    ctypes.windll.user32.mouse_event(down_flag, 0, 0, 0, 0)
                    time.sleep(0.02)
                    ctypes.windll.user32.mouse_event(up_flag, 0, 0, 0, 0)

                return {"success": True, "action": "mouse_click", "button": button, "double": double}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": True, "action": "mouse_click", "button": button, "double": double, "note": "simulated"}

    # 4. Control Mouse Scroll
    def mouse_scroll(self, clicks: int = 3, direction: str = "vertical") -> Dict[str, Any]:
        if sys.platform == "win32":
            try:
                import ctypes
                # MOUSEEVENTF_WHEEL = 0x0800, WHEEL_DELTA = 120
                wheel_delta = 120 * clicks
                ctypes.windll.user32.mouse_event(0x0800, 0, 0, wheel_delta, 0)
                return {"success": True, "action": "mouse_scroll", "clicks": clicks, "direction": direction}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": True, "action": "mouse_scroll", "clicks": clicks, "note": "simulated"}

    # 5. Control the Keyboard: Typing Text
    def type_text(self, text: str, press_enter: bool = False) -> Dict[str, Any]:
        if sys.platform == "win32":
            try:
                escaped = text.replace("'", "''").replace("{", "{{").replace("}", "}}")
                ps_cmd = f"""
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.SendKeys]::SendWait('{escaped}')
                """
                if press_enter:
                    ps_cmd += "\n[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')"

                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=6, capture_output=True)
                return {"success": True, "action": "type_text", "length": len(text), "press_enter": press_enter}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": True, "action": "type_text", "length": len(text), "note": "simulated"}

    # 6. Control the Keyboard: Pressing Keys and Hotkeys
    def press_key(self, key: str) -> Dict[str, Any]:
        k_lower = key.lower().strip()
        key_map = {
            "win": "{LWIN}",
            "enter": "{ENTER}",
            "return": "{ENTER}",
            "escape": "{ESC}",
            "esc": "{ESC}",
            "tab": "{TAB}",
            "backspace": "{BACKSPACE}",
            "delete": "{DELETE}",
            "space": " ",
            "up": "{UP}",
            "down": "{DOWN}",
            "left": "{LEFT}",
            "right": "{RIGHT}",
            "ctrl+c": "^c",
            "ctrl+v": "^v",
            "ctrl+a": "^a",
            "ctrl+s": "^s",
            "ctrl+z": "^z",
            "alt+tab": "%{TAB}",
            "alt+f4": "%{F4}"
        }
        send_code = key_map.get(k_lower, key)

        if sys.platform == "win32":
            try:
                ps_cmd = f"""
                Add-Type -AssemblyName System.Windows.Forms
                [System.Windows.Forms.SendKeys]::SendWait('{send_code}')
                """
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=6, capture_output=True)
                return {"success": True, "action": "press_key", "key": key}
            except Exception as e:
                return {"success": False, "error": str(e)}
        return {"success": True, "action": "press_key", "key": key, "note": "simulated"}

    # 7. Making Screenshots
    def take_screenshot(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        if not output_path:
            out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "screenshots")
            os.makedirs(out_dir, exist_ok=True)
            output_path = os.path.join(out_dir, f"screenshot_{int(time.time())}.png")

        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(output_path)
            return {"success": True, "path": output_path, "width": img.width, "height": img.height}
        except Exception:
            # Native PowerShell drawing capture fallback
            try:
                ps_script = f"""
                Add-Type -AssemblyName System.Windows.Forms
                Add-Type -AssemblyName System.Drawing
                $Screen = [System.Windows.Forms.Screen]::PrimaryScreen
                $Bitmap = New-Object System.Drawing.Bitmap $Screen.Bounds.Width, $Screen.Bounds.Height
                $Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
                $Graphics.CopyFromScreen($Screen.Bounds.X, $Screen.Bounds.Y, 0, 0, $Screen.Bounds.Size)
                $Bitmap.Save('{output_path}', [System.Drawing.Imaging.ImageFormat]::Png)
                $Graphics.Dispose()
                $Bitmap.Dispose()
                """
                subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], timeout=8, capture_output=True)
                if os.path.exists(output_path):
                    return {"success": True, "path": output_path}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "error": "Screen capture unavailable"}


# Global Singleton Helper
_mouse_kb_service: Optional[MouseKeyboardService] = None

def get_mouse_keyboard_service() -> MouseKeyboardService:
    global _mouse_kb_service
    if _mouse_kb_service is None:
        _mouse_kb_service = MouseKeyboardService()
    return _mouse_kb_service
