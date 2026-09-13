"""
gui/pages/mcp_hub.py - Dynamic MCP Service Hub & Real-Time Tool Executor
"""

import os
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QComboBox, QLineEdit, QTextEdit, QPlainTextEdit,
    QScrollArea, QFrame, QMessageBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor

from gui.widgets.metric_card import MetricCard
from utils.mcp_service import (
    list_mcp_servers, list_mcp_tools, call_mcp_tool,
    load_mcp_config, save_mcp_config, get_skills_count
)


class MCPHubPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tool_arg_inputs = {}
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🔌 DYNAMIC MCP SERVICE HUB")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Model Context Protocol (MCP) Infrastructure, Tool Catalog & Real-Time Executor")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # 4 Telemetry Cards
        self.telemetry_layout = QHBoxLayout()
        self.card_servers = MetricCard("0", "Connected Servers", "#38bdf8")
        self.card_tools = MetricCard("0", "Registered Tools", "#10b981")
        self.card_skills = MetricCard("0", "Engineering Skills", "#fbbf24")
        self.card_proto = MetricCard("Live Git", "Transport Protocol", "#818cf8")

        for c in [self.card_servers, self.card_tools, self.card_skills, self.card_proto]:
            self.telemetry_layout.addWidget(c)
        main_layout.addLayout(self.telemetry_layout)

        # 5 Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_tool_tester_tab(), "⚡ Live Tool Tester & Dispatcher")
        self.tabs.addTab(self.create_server_registry_tab(), "🗄️ MCP Server Registry")
        self.tabs.addTab(self.create_tool_catalog_tab(), "📜 Dynamic Tool Catalog & Schemas")
        self.tabs.addTab(self.create_add_server_tab(), "➕ Register Custom MCP Server")
        self.tabs.addTab(self.create_git_plugins_tab(), "🧩 Git Plugins & Extensions")

        main_layout.addWidget(self.tabs, stretch=1)
        self.refresh_mcp_data()

    def refresh_mcp_data(self):
        servers = list_mcp_servers()
        tools = list_mcp_tools()
        skills = get_skills_count()

        self.card_servers.set_value(str(len(servers)))
        self.card_tools.set_value(str(len(tools)))
        self.card_skills.set_value(str(skills))

        # Update Tool Tester Combo
        self.tool_combo.blockSignals(True)
        self.tool_combo.clear()
        self.all_tools = tools
        for t in tools:
            self.tool_combo.addItem(f"{t['tool_id']} ({t.get('server', 'MCP')})", t["tool_id"])
        self.tool_combo.blockSignals(False)

        if tools:
            self.on_tool_selected()

        # Update Server Registry List
        self.render_server_cards(servers)

        # Update Tool Catalog List
        self.render_catalog_cards(tools)

    # ──────────────────────────────────────────
    #  Tab 1: Live Tool Tester
    # ──────────────────────────────────────────
    def create_tool_tester_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        split = QHBoxLayout()
        split.setSpacing(16)

        # Left: Config & Arguments
        left_v = QVBoxLayout()
        left_v.setSpacing(10)
        left_v.addWidget(QLabel("<b>Select MCP Tool to Execute:</b>"))

        self.tool_combo = QComboBox()
        self.tool_combo.currentIndexChanged.connect(self.on_tool_selected)
        left_v.addWidget(self.tool_combo)

        self.tool_desc_lbl = QLabel()
        self.tool_desc_lbl.setStyleSheet("font-size: 11.5px; color: #94a3b8;")
        self.tool_desc_lbl.setWordWrap(True)
        left_v.addWidget(self.tool_desc_lbl)

        self.args_container = QWidget()
        self.args_layout = QVBoxLayout(self.args_container)
        self.args_layout.setContentsMargins(0, 0, 0, 0)
        self.args_layout.setSpacing(8)
        left_v.addWidget(self.args_container, stretch=1)

        self.btn_exec_tool = QPushButton("⚡ Execute MCP Tool Live")
        self.btn_exec_tool.setProperty("class", "primary-btn")
        self.btn_exec_tool.setFixedHeight(38)
        self.btn_exec_tool.clicked.connect(self.on_execute_tool)
        left_v.addWidget(self.btn_exec_tool)

        split.addLayout(left_v, stretch=1)

        # Right: Response JSON Viewer
        right_v = QVBoxLayout()
        right_v.setSpacing(8)
        
        top_resp = QHBoxLayout()
        top_resp.addWidget(QLabel("<b>📡 Live Tool Execution Response:</b>"))
        self.resp_status_lbl = QLabel("Ready")
        self.resp_status_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 700;")
        top_resp.addStretch()
        top_resp.addWidget(self.resp_status_lbl)
        right_v.addLayout(top_resp)

        self.resp_viewer = QPlainTextEdit()
        self.resp_viewer.setReadOnly(True)
        self.resp_viewer.setStyleSheet("""
            QPlainTextEdit {
                background-color: #030712;
                color: #38bdf8;
                font-family: 'Consolas', 'JetBrains Mono', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.5;
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        right_v.addWidget(self.resp_viewer, stretch=1)

        split.addLayout(right_v, stretch=1)
        layout.addLayout(split)
        return tab

    def on_tool_selected(self):
        tool_id = self.tool_combo.currentData()
        tool_meta = next((t for t in self.all_tools if t["tool_id"] == tool_id), None)

        while self.args_layout.count():
            item = self.args_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.tool_arg_inputs.clear()

        if not tool_meta:
            self.tool_desc_lbl.setText("No tool selected.")
            return

        self.tool_desc_lbl.setText(f"<b>Target Server:</b> <code>{tool_meta.get('server', 'MCP')}</code><br>{tool_meta.get('description', '')}")

        params = tool_meta.get("parameters", {})
        if params:
            self.args_layout.addWidget(QLabel("<b>Tool Arguments (JSON Schema):</b>"))
            for p_name, p_info in params.items():
                p_desc = p_info.get("description", p_name)
                p_default = str(p_info.get("default", ""))

                row = QVBoxLayout()
                row.addWidget(QLabel(f"{p_name} <i>({p_desc})</i>:"))
                if p_name == "code":
                    inp = QTextEdit()
                    inp.setPlainText("print('Hello from PySide6 MCP runner!')")
                    inp.setFixedHeight(90)
                else:
                    inp = QLineEdit()
                    inp.setText(p_default)
                row.addWidget(inp)
                self.args_layout.addLayout(row)
                self.tool_arg_inputs[p_name] = inp

    def on_execute_tool(self):
        tool_id = self.tool_combo.currentData()
        if not tool_id:
            return

        args = {}
        for k, widget in self.tool_arg_inputs.items():
            val = widget.toPlainText().strip() if isinstance(widget, QTextEdit) else widget.text().strip()
            if val.isdigit():
                args[k] = int(val)
            else:
                args[k] = val

        self.resp_status_lbl.setText("Executing...")
        response = call_mcp_tool(tool_id, args)

        status = response.get("status", "unknown").upper()
        elapsed = response.get("elapsed_ms", 0)
        col = "#10b981" if status == "SUCCESS" else "#ef4444"
        self.resp_status_lbl.setText(f"<span style='color:{col};'>{status}</span> ({elapsed} ms)")
        self.resp_viewer.setPlainText(json.dumps(response, indent=2))

    # ──────────────────────────────────────────
    #  Tab 2: MCP Server Registry
    # ──────────────────────────────────────────
    def create_server_registry_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.servers_container = QWidget()
        self.servers_layout = QVBoxLayout(self.servers_container)
        self.servers_layout.setContentsMargins(0, 0, 0, 0)
        self.servers_layout.setSpacing(10)
        scroll.setWidget(self.servers_container)

        layout.addWidget(scroll)
        return tab

    def render_server_cards(self, servers: list):
        while self.servers_layout.count():
            item = self.servers_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not servers:
            empty = QLabel("No custom MCP servers currently registered.")
            empty.setStyleSheet("color: #64748b; font-style: italic; padding: 12px;")
            self.servers_layout.addWidget(empty)
            return

        for s in servers:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: rgba(12, 38, 56, 0.65);
                    border: 1px solid rgba(56, 189, 248, 0.25);
                    border-left: 4px solid #38bdf8;
                    border-radius: 10px;
                    padding: 10px;
                }
            """)
            c_v = QVBoxLayout(card)
            c_v.setContentsMargins(8, 8, 8, 8)
            c_v.setSpacing(4)

            hdr = QHBoxLayout()
            title = QLabel(f"🔌  <b>{s.get('name', s['id'])}</b>")
            title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
            hdr.addWidget(title)
            hdr.addStretch()

            badge = QLabel(f"v{s.get('version','1.0.0')} · {s.get('status','ACTIVE')}")
            badge.setStyleSheet("background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b98155; border-radius: 10px; padding: 2px 8px; font-size: 10px; font-weight: 800;")
            hdr.addWidget(badge)
            c_v.addLayout(hdr)

            meta = QLabel(f"<b>ID:</b> <code>{s['id']}</code>  |  <b>Type:</b> <code>{s.get('type','remote-git-provider')}</code>  |  <b>Skills Count:</b> <code>{s.get('skills_count', 0)}</code><br><b>Repo:</b> <span style='color:#38bdf8;'>{s.get('repository','N/A')}</span>")
            meta.setStyleSheet("font-size: 11px; color: #94a3b8; font-family: monospace;")
            c_v.addWidget(meta)

            if s.get("description"):
                desc = QLabel(s["description"])
                desc.setStyleSheet("font-size: 12px; color: #cbd5e1;")
                c_v.addWidget(desc)

            self.servers_layout.addWidget(card)

    # ──────────────────────────────────────────
    #  Tab 3: Dynamic Tool Catalog
    # ──────────────────────────────────────────
    def create_tool_catalog_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.catalog_container = QWidget()
        self.catalog_layout = QVBoxLayout(self.catalog_container)
        self.catalog_layout.setContentsMargins(0, 0, 0, 0)
        self.catalog_layout.setSpacing(10)
        scroll.setWidget(self.catalog_container)

        layout.addWidget(scroll)
        return tab

    def render_catalog_cards(self, tools: list):
        while self.catalog_layout.count():
            item = self.catalog_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not tools:
            empty = QLabel("Tool catalog is empty.")
            empty.setStyleSheet("color: #64748b; font-style: italic; padding: 12px;")
            self.catalog_layout.addWidget(empty)
            return

        for t in tools:
            card = QFrame()
            card.setStyleSheet("background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 10px;")
            c_v = QVBoxLayout(card)
            c_v.setContentsMargins(8, 8, 8, 8)
            c_v.setSpacing(4)

            title = QLabel(f"⚙️  <b>{t['tool_id']}</b>  <span style='color:#64748b;'>({t.get('server', 'MCP')})</span>")
            title.setStyleSheet("font-size: 13.5px; color: #38bdf8;")
            c_v.addWidget(title)

            desc = QLabel(f"<b>Description:</b> {t.get('description', '')}")
            desc.setStyleSheet("font-size: 12px; color: #cbd5e1;")
            c_v.addWidget(desc)

            schema_str = json.dumps(t.get("parameters", {}), indent=2)
            pv = QPlainTextEdit()
            pv.setReadOnly(True)
            pv.setPlainText(schema_str)
            pv.setFixedHeight(90)
            pv.setStyleSheet("background: #030712; color: #fde68a; font-family: monospace; font-size: 11px; border: 1px solid rgba(245, 158, 11, 0.2);")
            c_v.addWidget(pv)

            self.catalog_layout.addWidget(card)

    # ──────────────────────────────────────────
    #  Tab 4: Register Custom MCP Server
    # ──────────────────────────────────────────
    def create_add_server_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        grid = QHBoxLayout()
        grid.setSpacing(14)

        # Left Fields
        left_v = QVBoxLayout()
        left_v.addWidget(QLabel("<b>Server Identifier (ID):</b>"))
        self.new_sid = QLineEdit()
        self.new_sid.setPlaceholderText("e.g. database_service, custom_tools")
        left_v.addWidget(self.new_sid)

        left_v.addWidget(QLabel("<b>Display Name:</b>"))
        self.new_sname = QLineEdit()
        self.new_sname.setPlaceholderText("e.g. Custom Database MCP Server")
        left_v.addWidget(self.new_sname)

        left_v.addWidget(QLabel("<b>Git Repository URL:</b>"))
        self.new_repo = QLineEdit()
        self.new_repo.setPlaceholderText("https://github.com/org/repo.git")
        left_v.addWidget(self.new_repo)

        left_v.addWidget(QLabel("<b>API Endpoint:</b>"))
        self.new_endpoint = QLineEdit()
        self.new_endpoint.setPlaceholderText("https://api.github.com/repos/org/repo/contents")
        left_v.addWidget(self.new_endpoint)
        grid.addLayout(left_v, stretch=1)

        # Right Fields
        right_v = QVBoxLayout()
        right_v.addWidget(QLabel("<b>Raw Base URL:</b>"))
        self.new_raw = QLineEdit()
        self.new_raw.setPlaceholderText("https://raw.githubusercontent.com/org/repo/main")
        right_v.addWidget(self.new_raw)

        right_v.addWidget(QLabel("<b>Version:</b>"))
        self.new_ver = QLineEdit("1.0.0")
        right_v.addWidget(self.new_ver)

        right_v.addWidget(QLabel("<b>Skills Count:</b>"))
        self.new_count = QSpinBox()
        self.new_count.setRange(0, 500)
        self.new_count.setValue(1)
        right_v.addWidget(self.new_count)

        right_v.addWidget(QLabel("<b>Transport Type:</b>"))
        self.new_stype = QComboBox()
        self.new_stype.addItems(["remote-git-provider", "browser-spaces-automation", "stdio", "sse", "internal"])
        right_v.addWidget(self.new_stype)
        grid.addLayout(right_v, stretch=1)

        layout.addLayout(grid)

        layout.addWidget(QLabel("<b>Server Description:</b>"))
        self.new_sdesc = QTextEdit()
        self.new_sdesc.setPlaceholderText("What capabilities does this MCP server provide?")
        self.new_sdesc.setFixedHeight(80)
        layout.addWidget(self.new_sdesc)

        self.btn_save_server = QPushButton("💾 Save Standardized MCP Server")
        self.btn_save_server.setProperty("class", "primary-btn")
        self.btn_save_server.setFixedHeight(40)
        self.btn_save_server.clicked.connect(self.on_save_custom_server)
        layout.addWidget(self.btn_save_server)

        layout.addStretch()
        return tab

    def on_save_custom_server(self):
        sid = self.new_sid.text().strip()
        sname = self.new_sname.text().strip()
        if not sid or not sname:
            QMessageBox.warning(self, "Missing Fields", "Please provide both Server ID and Display Name.")
            return

        cfg = load_mcp_config()
        if "mcpServers" not in cfg:
            cfg["mcpServers"] = {}

        cfg["mcpServers"][sid] = {
            "name": sname,
            "repository": self.new_repo.text().strip(),
            "api_endpoint": self.new_endpoint.text().strip(),
            "raw_base_url": self.new_raw.text().strip(),
            "version": self.new_ver.text().strip(),
            "skills_count": self.new_count.value(),
            "status": "active",
            "type": self.new_stype.currentText(),
            "description": self.new_sdesc.toPlainText().strip()
        }
        save_mcp_config(cfg)
        self.refresh_mcp_data()

        self.new_sid.clear()
        self.new_sname.clear()
        self.new_repo.clear()
        self.new_endpoint.clear()
        self.new_raw.clear()
        self.new_sdesc.clear()

        QMessageBox.information(self, "MCP Server Saved", f"Registered MCP Server '{sname}' successfully!")

    # ──────────────────────────────────────────
    #  Tab 5: Git Plugins & Extensions Manager
    # ──────────────────────────────────────────
    def create_git_plugins_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Action Bar
        bar = QHBoxLayout()
        info_label = QLabel("<b>Installed Extensions & Dynamic Git Plugins</b>")
        info_label.setStyleSheet("font-size: 13px; color: #38bdf8;")
        bar.addWidget(info_label)
        bar.addStretch()

        self.btn_open_folder = QPushButton("📁 Open Plugins Folder")
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                padding: 6px 14px;
                border-radius: 5px;
                font-size: 11.5px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """)
        self.btn_open_folder.clicked.connect(self.on_open_plugins_folder)
        bar.addWidget(self.btn_open_folder)

        self.btn_reload_plugins = QPushButton("🔄 Reload Plugins")
        self.btn_reload_plugins.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                padding: 6px 14px;
                border-radius: 5px;
                font-size: 11.5px;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """)
        self.btn_reload_plugins.clicked.connect(self.refresh_plugins_list)
        bar.addWidget(self.btn_reload_plugins)

        self.btn_install_git_plugin = QPushButton("📥 Install Plugin from Git...")
        self.btn_install_git_plugin.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                padding: 6px 16px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 11.5px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.btn_install_git_plugin.clicked.connect(self.open_git_plugin_installer)
        bar.addWidget(self.btn_install_git_plugin)
        layout.addLayout(bar)

        # Scrollable Cards View
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: transparent; border: none;")

        self.plugins_container = QWidget()
        self.plugins_layout = QVBoxLayout(self.plugins_container)
        self.plugins_layout.setContentsMargins(0, 0, 0, 0)
        self.plugins_layout.setSpacing(10)
        scroll.setWidget(self.plugins_container)
        layout.addWidget(scroll, stretch=1)

        self.refresh_plugins_list()
        return tab

    def open_git_plugin_installer(self):
        from core.plugin_base import get_plugin_manager
        from plugins.plugin_installer import PluginInstallerDialog

        pm = get_plugin_manager(app_context=self.window())
        dialog = PluginInstallerDialog(pm, parent=self)
        dialog.plugin_installed.connect(lambda manifest: self.refresh_plugins_list())
        dialog.exec()

    def on_open_plugins_folder(self):
        import subprocess
        from core.plugin_base import get_plugin_manager
        pm = get_plugin_manager()
        p_dir = str(pm.plugins_dir.resolve())
        if os.name == "nt":
            os.startfile(p_dir)
        elif sys.platform == "darwin":
            subprocess.run(["open", p_dir], check=False)
        else:
            subprocess.run(["xdg-open", p_dir], check=False)

    def refresh_plugins_list(self):
        from core.plugin_base import get_plugin_manager
        pm = get_plugin_manager(app_context=self.window())
        pm.discover_custom_plugins()
        plugins = pm.list_plugins()

        # Clear container
        while self.plugins_layout.count():
            item = self.plugins_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not plugins:
            empty = QLabel("No extensions currently installed. Click 'Install Plugin from Git...' to add one.")
            empty.setStyleSheet("color: #64748b; font-style: italic; padding: 20px; font-size: 12px;")
            self.plugins_layout.addWidget(empty)
        else:
            for p in plugins:
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #0f172a;
                        border: 1px solid #1e293b;
                        border-radius: 8px;
                        padding: 12px;
                    }
                    QFrame:hover {
                        border: 1px solid #38bdf8;
                    }
                """)
                c_layout = QVBoxLayout(card)
                c_layout.setSpacing(6)

                top = QHBoxLayout()
                p_name = QLabel(f"<b>{p['name']}</b> <span style='color:#38bdf8;'>v{p['version']}</span>")
                p_name.setStyleSheet("font-size: 13px; color: #f8fafc;")
                top.addWidget(p_name)
                top.addStretch()

                id_badge = QLabel(f"ID: {p['id']}")
                id_badge.setStyleSheet("background-color: #1e293b; color: #94a3b8; padding: 2px 6px; border-radius: 4px; font-size: 10.5px; font-family: monospace;")
                top.addWidget(id_badge)

                del_btn = QPushButton("🗑️ Uninstall")
                del_btn.setStyleSheet("""
                    QPushButton {
                        background-color: rgba(239, 68, 68, 0.12);
                        color: #fca5a5;
                        border: 1px solid #ef4444;
                        padding: 3px 8px;
                        border-radius: 4px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #ef4444;
                        color: #ffffff;
                    }
                """)
                del_btn.clicked.connect(lambda _, pid=p["id"], pname=p["name"]: self.on_uninstall_plugin(pid, pname))
                top.addWidget(del_btn)
                c_layout.addLayout(top)

                if p.get("description"):
                    desc = QLabel(p["description"])
                    desc.setStyleSheet("color: #94a3b8; font-size: 11.5px;")
                    desc.setWordWrap(True)
                    c_layout.addWidget(desc)

                path_lbl = QLabel(f"📁 Path: {p['path']}")
                path_lbl.setStyleSheet("color: #475569; font-size: 10.5px; font-family: monospace;")
                c_layout.addWidget(path_lbl)

                self.plugins_layout.addWidget(card)

        self.plugins_layout.addStretch()

    def on_uninstall_plugin(self, plugin_id: str, plugin_name: str):
        reply = QMessageBox.question(
            self,
            "Confirm Uninstall",
            f"Are you sure you want to uninstall and remove '{plugin_name}' ({plugin_id})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            from core.plugin_base import get_plugin_manager
            pm = get_plugin_manager()
            success, msg = pm.uninstall_plugin(plugin_id)
            if success:
                QMessageBox.information(self, "Plugin Removed", f"Successfully removed {plugin_name}.")
                self.refresh_plugins_list()
            else:
                QMessageBox.warning(self, "Removal Failed", msg)

