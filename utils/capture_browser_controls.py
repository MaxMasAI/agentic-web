"""
utils/capture_browser_controls.py - High-Resolution Screenshot Generator for Browser Controls & Multi-Agent HUD.

Renders and saves high-resolution screenshots of the Multi-Agent Workflow, Browser Window Controls,
and Browser Automation Control Center directly into the 'images/' folder.
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QLineEdit, QComboBox, QGridLayout,
    QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont

from gui.theme import APP_QSS
from gui.widgets.workflow_hud_widget import WorkflowHUDWidget
from gui.widgets.pool_monitor import PoolMonitor


def create_browser_control_center_widget() -> QWidget:
    """Creates a dedicated Browser Automation & Window Control Center widget."""
    widget = QWidget()
    widget.setStyleSheet("""
        QWidget {
            background-color: #080b11;
            color: #f8fafc;
            font-family: 'Segoe UI', system-ui, sans-serif;
        }
        QFrame.panel {
            background-color: #0d121f;
            border: 1px solid #1e293b;
            border-radius: 12px;
            padding: 16px;
        }
        QFrame.control-card {
            background-color: #131b2e;
            border: 1px solid #22324e;
            border-radius: 8px;
            padding: 12px;
        }
        QPushButton {
            background-color: #1e293b;
            color: #38bdf8;
            border: 1px solid #38bdf8;
            border-radius: 6px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #38bdf8;
            color: #080b11;
        }
        QPushButton.primary {
            background-color: #0284c7;
            color: #ffffff;
            border: 1px solid #38bdf8;
        }
        QPushButton.danger {
            background-color: #881337;
            color: #fca5a5;
            border: 1px solid #f43f5e;
        }
        QPushButton.success {
            background-color: #064e3b;
            color: #6ee7b7;
            border: 1px solid #10b981;
        }
        QLineEdit {
            background-color: #090d16;
            border: 1px solid #334155;
            border-radius: 6px;
            padding: 8px 12px;
            color: #f8fafc;
            font-size: 13px;
        }
    """)
    
    root_layout = QVBoxLayout(widget)
    root_layout.setContentsMargins(20, 20, 20, 20)
    root_layout.setSpacing(16)

    # 1. Header & Navigation Bar
    top_panel = QFrame()
    top_panel.setProperty("class", "panel")
    top_panel_layout = QVBoxLayout(top_panel)
    top_panel_layout.setSpacing(12)

    # Title row
    title_row = QHBoxLayout()
    title = QLabel("🌐 MULTI-AGENT BROWSER AUTOMATION & CONTROLS")
    title.setStyleSheet("font-size: 18px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px;")
    title_row.addWidget(title)
    
    status_badge = QLabel("🟢 CDP CONNECTED · PORT 9222 · 5 AGENT CURSORS ACTIVE")
    status_badge.setStyleSheet("font-size: 11px; font-weight: 700; color: #10b981; background: #064e3b; border: 1px solid #059669; padding: 4px 10px; border-radius: 12px;")
    title_row.addWidget(status_badge)
    title_row.addStretch()
    top_panel_layout.addLayout(title_row)

    # Navigation & URL Bar
    nav_row = QHBoxLayout()
    nav_row.setSpacing(8)
    
    btn_back = QPushButton("◀")
    btn_back.setFixedWidth(36)
    btn_fwd = QPushButton("▶")
    btn_fwd.setFixedWidth(36)
    btn_reload = QPushButton("⟳")
    btn_reload.setFixedWidth(36)
    
    url_input = QLineEdit()
    url_input.setText("https://github.com/trending · [Tab #1 - Active Focus]")
    url_input.setStyleSheet("font-family: monospace; font-size: 13px; color: #38bdf8; background: #080c14; border: 1px solid #0284c7; padding: 8px 12px; border-radius: 6px;")
    
    btn_navigate = QPushButton("Navigate")
    btn_navigate.setProperty("class", "primary")
    btn_take_shot = QPushButton("📸 Take Tab Screenshot")
    btn_rec = QPushButton("🔴 Record Session")
    btn_rec.setProperty("class", "danger")

    nav_row.addWidget(btn_back)
    nav_row.addWidget(btn_fwd)
    nav_row.addWidget(btn_reload)
    nav_row.addWidget(url_input, stretch=1)
    nav_row.addWidget(btn_navigate)
    nav_row.addWidget(btn_take_shot)
    nav_row.addWidget(btn_rec)
    top_panel_layout.addLayout(nav_row)
    root_layout.addWidget(top_panel)

    # 2. Main Grid: Active Tabs + Cursors & Actions + DevTools Telemetry
    grid_layout = QGridLayout()
    grid_layout.setSpacing(14)

    # Left Column: Browser Tabs & Window Focus Switcher
    tabs_panel = QFrame()
    tabs_panel.setProperty("class", "panel")
    tabs_layout = QVBoxLayout(tabs_panel)
    tabs_title = QLabel("📑 ACTIVE BROWSER TABS & FOCUS")
    tabs_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8; margin-bottom: 6px;")
    tabs_layout.addWidget(tabs_title)

    tab_items = [
        ("Tab 1", "GitHub Trending - AI & LLM Repos", "ACTIVE FOCUS", "#10b981", "gemini"),
        ("Tab 2", "ArXiv Computer Science Research", "AGENT SCRAPING", "#38bdf8", "deepseek"),
        ("Tab 3", "Hugging Face Models & Datasets", "STANDBY", "#a855f7", "claude"),
        ("Tab 4", "Playwright Automation Viewport", "RECORDING", "#f43f5e", "web_agent"),
    ]

    for tid, tname, tstatus, tcolor, agent in tab_items:
        tab_card = QFrame()
        tab_card.setProperty("class", "control-card")
        t_card_layout = QHBoxLayout(tab_card)
        t_card_layout.setContentsMargins(10, 8, 10, 8)

        tab_info = QVBoxLayout()
        t_label = QLabel(f"<b>{tid}:</b> {tname}")
        t_label.setStyleSheet("font-size: 12px; color: #f1f5f9;")
        t_sub = QLabel(f"Managed by: <b>@{agent}</b>")
        t_sub.setStyleSheet("font-size: 10px; color: #64748b;")
        tab_info.addWidget(t_label)
        tab_info.addWidget(t_sub)
        t_card_layout.addLayout(tab_info, stretch=1)

        t_badge = QLabel(tstatus)
        t_badge.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {tcolor}; border: 1px solid {tcolor}; padding: 3px 8px; border-radius: 10px;")
        t_card_layout.addWidget(t_badge)

        btn_focus = QPushButton("Focus")
        btn_focus.setStyleSheet("font-size: 10px; padding: 4px 8px;")
        t_card_layout.addWidget(btn_focus)
        tabs_layout.addWidget(tab_card)

    tabs_layout.addStretch()
    grid_layout.addWidget(tabs_panel, 0, 0)

    # Right Column: Parallel Agent Cursors & System Control
    cursors_panel = QFrame()
    cursors_panel.setProperty("class", "panel")
    cursors_layout = QVBoxLayout(cursors_panel)
    cursors_title = QLabel("🎯 MULTI-AGENT CURSOR CONTROLS & SYSTEM INTEGRATION")
    cursors_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8; margin-bottom: 6px;")
    cursors_layout.addWidget(cursors_title)

    cursors_list = [
        ("Google Gemini Cursor", "(X: 840, Y: 420)", "#10b981", "Active Navigation & Click Stream"),
        ("DeepSeek Coder Cursor", "(X: 1220, Y: 680)", "#38bdf8", "Code Block Extraction & Parsing"),
        ("Claude Reviewer Cursor", "(X: 450, Y: 310)", "#a855f7", "Accessibility & Security Inspection"),
        ("Web-Agent Overseer", "(Full Screen)", "#f59e0b", "Full Viewport Coordinate Mapping"),
        ("System OS Cursor", "(Native Windows)", "#ec4899", "Smooth Follow & Focus on System Apps"),
    ]

    for cname, ccoords, ccolor, cdesc in cursors_list:
        cursor_card = QFrame()
        cursor_card.setProperty("class", "control-card")
        c_layout = QHBoxLayout(cursor_card)
        c_layout.setContentsMargins(10, 8, 10, 8)

        dot = QLabel("●")
        dot.setStyleSheet(f"color: {ccolor}; font-size: 16px; margin-right: 4px;")
        c_layout.addWidget(dot)

        c_info = QVBoxLayout()
        c_title = QLabel(f"<b>{cname}</b> <span style='color: #64748b;'>{ccoords}</span>")
        c_title.setStyleSheet("font-size: 12px; color: #f1f5f9;")
        c_desc_lbl = QLabel(cdesc)
        c_desc_lbl.setStyleSheet("font-size: 10px; color: #94a3b8;")
        c_info.addWidget(c_title)
        c_info.addWidget(c_desc_lbl)
        c_layout.addLayout(c_info, stretch=1)

        btn_toggle = QPushButton("Highlight")
        btn_toggle.setStyleSheet("font-size: 10px; padding: 4px 8px;")
        c_layout.addWidget(btn_toggle)
        cursors_layout.addWidget(cursor_card)

    cursors_layout.addStretch()
    grid_layout.addWidget(cursors_panel, 0, 1)

    root_layout.addLayout(grid_layout)
    return widget


def capture_browser_controls(output_dir: str = None) -> list:
    if output_dir is None:
        output_dir = os.path.join(PROJECT_ROOT, "images")
    os.makedirs(output_dir, exist_ok=True)

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)

    results = []
    print(f"\n[*] Capturing Browser Controls & Multi-Agent HUD screenshots to '{output_dir}'...")

    # 1. Multi-Agent Workflow & Browser Window Focus HUD
    container1 = QWidget()
    container1.setObjectName("CentralWidget")
    container1.setStyleSheet("background-color: #080b11; padding: 20px;")
    layout1 = QVBoxLayout(container1)
    layout1.setContentsMargins(20, 20, 20, 20)
    layout1.setSpacing(16)

    title1 = QLabel("🤖 MULTI-AGENT WORKFLOW & BROWSER WINDOW HUD")
    title1.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;")
    sub1 = QLabel("Live Collaborative Window Focus Controls · Step Progress Tracking · Instant Tab Viewers")
    sub1.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 8px;")
    layout1.addWidget(title1)
    layout1.addWidget(sub1)

    hud = WorkflowHUDWidget()
    hud.set_active_squad([
        {"id": "gemini", "name": "Google Gemini", "role": "Master Orchestrator", "is_leader": True},
        {"id": "deepseek", "name": "DeepSeek Coder", "role": "Senior Build Specialist", "is_leader": False},
        {"id": "claude", "name": "Claude Reviewer", "role": "Quality & Security Auditor", "is_leader": False},
        {"id": "chatgpt", "name": "ChatGPT Writer", "role": "Deliverable Synthesizer", "is_leader": False},
        {"id": "web_agent", "name": "Web-Agent", "role": "Full-Screen Overseer", "is_leader": False},
    ])
    hud.update_agent_status("gemini", "WORKING", "Orchestrating multi-model pipeline...")
    hud.update_agent_status("deepseek", "WORKING", "Writing production components...")
    hud.update_agent_status("claude", "WAITING", "Awaiting build artifacts for review...")
    hud.update_agent_status("chatgpt", "IDLE", "Ready in dispatch pool.")
    hud.update_agent_status("web_agent", "WORKING", "Auditing full-screen browser viewport...")
    layout1.addWidget(hud)

    container1.resize(1350, 480)
    container1.show()
    for _ in range(6):
        app.processEvents()
        time.sleep(0.04)

    hud_path = os.path.join(output_dir, "20_Multi_Agent_Browser_HUD_Controls.png")
    container1.grab().save(hud_path, "PNG")
    results.append({"name": "20_Multi_Agent_Browser_HUD_Controls.png", "path": hud_path})
    print(f"  [+] Saved Browser HUD -> images/20_Multi_Agent_Browser_HUD_Controls.png")
    container1.close()

    # 2. Live Multi-Agent Pool & Direct Action Controls
    container2 = QWidget()
    container2.setObjectName("CentralWidget")
    container2.setStyleSheet("background-color: #080b11; padding: 20px;")
    layout2 = QVBoxLayout(container2)
    layout2.setContentsMargins(20, 20, 20, 20)

    title2 = QLabel("⚡ LIVE AGENT POOL & REAL-TIME DISPATCH MONITOR")
    title2.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8; letter-spacing: 1px;")
    layout2.addWidget(title2)

    pool = PoolMonitor()
    layout2.addWidget(pool)

    container2.resize(1350, 680)
    container2.show()
    for _ in range(6):
        app.processEvents()
        time.sleep(0.04)

    pool_path = os.path.join(output_dir, "21_Live_Agent_Pool_Browser_Monitor.png")
    container2.grab().save(pool_path, "PNG")
    results.append({"name": "21_Live_Agent_Pool_Browser_Monitor.png", "path": pool_path})
    print(f"  [+] Saved Pool Monitor -> images/21_Live_Agent_Pool_Browser_Monitor.png")
    container2.close()

    # 3. Browser Automation & Window Control Center
    container3 = create_browser_control_center_widget()
    container3.setObjectName("CentralWidget")
    container3.resize(1400, 750)
    container3.show()
    for _ in range(6):
        app.processEvents()
        time.sleep(0.04)

    ctrl_path = os.path.join(output_dir, "22_Browser_Automation_Control_Center.png")
    container3.grab().save(ctrl_path, "PNG")
    results.append({"name": "22_Browser_Automation_Control_Center.png", "path": ctrl_path})
    print(f"  [+] Saved Browser Automation Controls -> images/22_Browser_Automation_Control_Center.png")
    container3.close()

    print(f"\n[OK] Successfully saved {len(results)} browser control screenshots to '{output_dir}'!\n")
    return results


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT_ROOT, "images")
    res = capture_browser_controls(out)
    print(f"Browser controls captured: {len(res)}")

