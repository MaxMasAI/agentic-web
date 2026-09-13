"""
utils/capture_app_tabs.py - Autonomous Application Tab & Page Screenshot Generator.

Renders and captures high-resolution (1920x1080 / 1400x900) pixel-perfect screenshots
of all 19 internal Agentic Web application pages/tabs, saving them labeled into the 'images/' folder.
"""

import os
import sys
import time

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, Qt, QSize
from PySide6.QtGui import QPixmap

# Friendly human-readable names for all application tabs
PAGE_DISPLAY_NAMES = {
    "home": "01_Mission_Control_Dashboard",
    "launch": "02_Task_Dispatch_Console",
    "subagents": "03_Multi_Agent_Squads",
    "history": "04_Mission_History_Archives",
    "chat": "05_Multi_Model_AI_Chat",
    "chat_files": "06_Document_Knowledge_Chat",
    "research": "07_Deep_Research_Studio",
    "media_studio": "08_Media_Studio",
    "vscode": "09_Inbuilt_VS_Code_Monaco_Studio",
    "canvas_dev": "10_Infinite_Agent_Canvas_IDE",
    "playground": "11_Agent_Playground_Arena",
    "agent_builder": "12_Custom_Agent_Builder",
    "painter": "13_AI_Painter_Studio",
    "notepad": "14_Scratchpad_Notepad",
    "scheduler": "15_Automated_Job_Scheduler",
    "mcp": "16_MCP_Server_Hub",
    "memory": "17_Semantic_Neural_Memory",
    "explorer": "18_Project_File_Explorer",
    "settings": "19_System_Settings",
}


def capture_all_app_tabs(output_dir: str = None) -> list:
    """
    Renders every tab of the desktop application and captures a full-window screenshot
    saved to images/{tab_name}.png.
    """
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "images")
    os.makedirs(output_dir, exist_ok=True)

    # Initialize QApplication if not already created
    app = QApplication.instance()
    owns_app = False
    if not app:
        app = QApplication(sys.argv)
        owns_app = True

    # Load application dark theme
    from gui.theme import APP_QSS
    app.setStyleSheet(APP_QSS)

    from app import MainWindow
    window = MainWindow()
    window.resize(1440, 920)
    window.show()

    results = []
    print(f"\n[*] Starting batch capture of all {len(window.pages)} application tabs to '{output_dir}'...")

    for key, page_widget in window.pages.items():
        tab_name = PAGE_DISPLAY_NAMES.get(key, f"Tab_{key}")
        window.switch_page(key)
        
        # Force Qt event loop processing to let animations and layouts settle
        for _ in range(8):
            app.processEvents()
            time.sleep(0.04)

        # Grab full high-DPI window pixmap
        pixmap = window.grab()
        file_path = os.path.join(output_dir, f"{tab_name}.png")
        pixmap.save(file_path, "PNG")

        results.append({
            "key": key,
            "tab_name": tab_name,
            "file_path": file_path,
            "size": f"{pixmap.width()}x{pixmap.height()}"
        })
        print(f"  [+] Captured App Tab [{key.upper()}] -> images/{tab_name}.png ({pixmap.width()}x{pixmap.height()})")

    # Also capture full window overview on Mission Control
    window.switch_page("home")
    for _ in range(5):
        app.processEvents()
        time.sleep(0.03)
    overview_path = os.path.join(output_dir, "00_Agentic_Web_Full_Overview.png")
    window.grab().save(overview_path, "PNG")
    results.insert(0, {
        "key": "overview",
        "tab_name": "00_Agentic_Web_Full_Overview",
        "file_path": overview_path,
        "size": f"{window.width()}x{window.height()}"
    })
    print(f"  [+] Captured Full App Overview -> images/00_Agentic_Web_Full_Overview.png")

    window.close()
    print(f"\n[OK] Successfully saved {len(results)} application screenshots into '{output_dir}'!\n")
    return results


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT_ROOT, "images")
    res = capture_all_app_tabs(out)
    print(f"Total screenshots generated: {len(res)}")
