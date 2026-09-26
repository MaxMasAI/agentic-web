"""
gui/pages/squad_roster.py - Autonomous AI Squad Generation & Roster Management
Conforms strictly to design_system_ui_theme_documentation.md & modern dark UI standards.
"""

import os
import json
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QCheckBox, QComboBox, QFrame, QScrollArea,
    QMessageBox, QGroupBox, QTabWidget, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from core.squad_learner import detect_and_create_repeated_pattern_squads
from core.agency_agents_manager import agency_manager

SUBAGENTS_FILE = os.path.join("json", "subagents.json")

AUTOGEN_TEMPLATES = [
    {
        "name": "Full-Stack Web & E-Commerce Prototypers",
        "desc": "High-velocity web development, responsive CSS, API architecture & visual assets",
        "task": "Develop a production-ready responsive e-commerce web application with animated product cards and interactive checkout",
        "agents": ["gemini", "deepseek", "chatgpt", "dalle"]
    },
    {
        "name": "Architecture, Security & QA Red Team",
        "desc": "Deep technical analysis, zero-trust security audit, accessibility compliance & unit testing",
        "task": "Perform a comprehensive security audit, architecture review, and defensive programming verification",
        "agents": ["gemini", "claude", "deepseek", "perplexity"]
    },
    {
        "name": "Viral Growth, Content & Social Strategy",
        "desc": "Audience hooks, platform-tailored copy, trend citations & graphic design",
        "task": "Create a multi-channel viral product launch campaign with social copy, hashtags, and hero visual assets",
        "agents": ["gemini", "chatgpt", "meta_ai", "dalle"]
    },
    {
        "name": "High-Performance Compute & Scientific Reasoning",
        "desc": "GPU optimization, algorithmic complexity analysis & live technical search",
        "task": "Benchmark computational efficiency, optimize algorithm latency, and verify live scientific citations",
        "agents": ["gemini", "nvidia_ai", "deepseek", "perplexity"]
    },
    {
        "name": "Enterprise Multilingual & Logistics Hub",
        "desc": "Cross-language localization, enterprise spreadsheets & structured documentation",
        "task": "Translate and localize software documentation across European languages with formatted enterprise sheets",
        "agents": ["gemini", "mistral", "copilot", "chatgpt"]
    }
]

AGENT_DISPLAY_MAP = {
    "gemini": ("♊ Gemini", "#38bdf8"),
    "deepseek": ("⚡ DeepSeek", "#818cf8"),
    "chatgpt": ("🤖 ChatGPT", "#10b981"),
    "claude": ("🛡 Claude", "#f59e0b"),
    "perplexity": ("🔍 Perplexity", "#06b6d4"),
    "dalle": ("🎨 DALL-E 3", "#ec4899"),
    "copilot": ("💻 Copilot", "#3b82f6"),
    "meta_ai": ("🌐 Meta AI", "#6366f1"),
    "mistral": ("🌪 Mistral", "#f97316"),
    "nvidia_ai": ("🟢 Nvidia NIM", "#84cc16"),
    "grok": ("⚡ Grok", "#eab308"),
}


class SquadRosterPage(QWidget):
    launch_squad_requested = Signal(str, str, str)
    squads_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.subagents = []
        self.create_agent_boxes = {}
        self.display_limit = 60
        self.init_ui()

    def init_ui(self):
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(20, 16, 20, 16)
        page_layout.setSpacing(14)

        # 1. Top Header & Action Row
        header_row = QHBoxLayout()
        header_row.setSpacing(12)

        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("AGENT SQUAD ROSTER")
        title.setProperty("class", "metric-value")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc; letter-spacing: 0.5px;")

        subtitle = QLabel("Deploy, Assemble & Manage High-Performance Multi-Agent Squads")
        subtitle.setProperty("class", "metric-label")
        subtitle.setStyleSheet("font-size: 11.5px; color: #94a3b8;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        header_row.addLayout(t_box)
        header_row.addStretch()

        self.btn_skills_vault = QPushButton("📥 Skills Vault (*.md)")
        self.btn_skills_vault.setProperty("class", "btn-secondary")
        self.btn_skills_vault.setToolTip("Open Skills Vault to ingest or manage dynamic agent skills")
        self.btn_skills_vault.clicked.connect(self.on_open_skills_vault)
        header_row.addWidget(self.btn_skills_vault)

        self.btn_agency_catalog = QPushButton("🎭 Browse 287+ Agency Agents")
        self.btn_agency_catalog.setProperty("class", "btn-secondary")
        self.btn_agency_catalog.setToolTip("Explore complete Agency catalog across 18 specialist divisions")
        self.btn_agency_catalog.clicked.connect(self.on_open_agency_catalog)
        header_row.addWidget(self.btn_agency_catalog)

        self.btn_add_all_agency = QPushButton("⚡ Add All 287+ Agency Squads")
        self.btn_add_all_agency.setProperty("class", "btn-primary")
        self.btn_add_all_agency.setToolTip("Batch registers all 287+ Agency personas into your Squad Roster")
        self.btn_add_all_agency.clicked.connect(self.on_add_all_agency_squads)
        header_row.addWidget(self.btn_add_all_agency)

        page_layout.addLayout(header_row)

        # 2. Tabs: Roster / Auto-Generator / Assemble Custom
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1e293b;
                background-color: #0b1120;
                border-radius: 8px;
                padding: 12px;
            }
            QTabBar::tab {
                background: #141c2e;
                color: #94a3b8;
                padding: 9px 20px;
                margin-right: 6px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 700;
                font-size: 12.5px;
            }
            QTabBar::tab:selected {
                background: #1e293b;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
            QTabBar::tab:hover:!selected {
                background: #1a2438;
                color: #f8fafc;
            }
        """)

        # Tab 1: Active Squad Roster
        tab_roster = QWidget()
        self.setup_roster_tab(tab_roster)
        self.tab_widget.addTab(tab_roster, "📋 Registered Squad Roster")

        # Tab 2: Auto-Generator
        tab_auto = QWidget()
        self.setup_auto_generator_tab(tab_auto)
        self.tab_widget.addTab(tab_auto, "⚡ Auto-Squad Generator")

        # Tab 3: Assemble Custom Squad
        tab_assemble = QWidget()
        self.setup_assemble_tab(tab_assemble)
        self.tab_widget.addTab(tab_assemble, "🛠 Assemble Custom Squad")

        page_layout.addWidget(self.tab_widget, stretch=1)

        self.load_squads_from_file()

    # =========================================================================
    # TAB 1: REGISTERED SQUAD ROSTER
    # =========================================================================
    def setup_roster_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Filter & Search Bar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        self.div_filter_combo = QComboBox()
        self.div_filter_combo.setMinimumWidth(180)
        self.div_filter_combo.addItem("🌐 All Divisions", "all")
        divisions = agency_manager.get_divisions()
        for dkey, dinfo in sorted(divisions.items()):
            self.div_filter_combo.addItem(f"{dinfo.get('label', dkey.title())}", dkey)
        self.div_filter_combo.currentIndexChanged.connect(self.on_division_filter_changed)
        filter_bar.addWidget(self.div_filter_combo)

        self.squad_search_edit = QLineEdit()
        self.squad_search_edit.setPlaceholderText("🔍 Filter squads by codename, role, division, agent...")
        self.squad_search_edit.textChanged.connect(self.on_squad_search_changed)
        filter_bar.addWidget(self.squad_search_edit, stretch=1)

        self.roster_count_badge = QLabel("0 Squads Ready")
        self.roster_count_badge.setStyleSheet(
            "background: rgba(56, 189, 248, 0.12); color: #38bdf8; "
            "border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 6px; "
            "padding: 5px 12px; font-weight: 700; font-size: 11.5px;"
        )
        filter_bar.addWidget(self.roster_count_badge)

        self.btn_scan_learner = QPushButton("⚡ Scan History")
        self.btn_scan_learner.setProperty("class", "btn-secondary")
        self.btn_scan_learner.setToolTip("Analyze past workflow patterns and auto-create squads")
        self.btn_scan_learner.clicked.connect(self.on_scan_learner)
        filter_bar.addWidget(self.btn_scan_learner)

        layout.addLayout(filter_bar)

        # Scrollable cards area
        self.roster_scroll = QScrollArea()
        self.roster_scroll.setWidgetResizable(True)
        self.roster_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.squads_list_container = QWidget()
        self.squads_list_layout = QVBoxLayout(self.squads_list_container)
        self.squads_list_layout.setContentsMargins(2, 2, 2, 2)
        self.squads_list_layout.setSpacing(10)
        self.roster_scroll.setWidget(self.squads_list_container)

        layout.addWidget(self.roster_scroll, stretch=1)

    # =========================================================================
    # TAB 2: AUTONOMOUS GENERATOR
    # =========================================================================
    def setup_auto_generator_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        desc = QLabel(
            "Let the AI orchestrator analyze your project scope and automatically assemble synergy-matched specialist teams."
        )
        desc.setStyleSheet("color: #94a3b8; font-size: 12.5px;")
        layout.addWidget(desc)

        # 2 Feature Cards
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        # Card 1: Custom Goal Synthesizer
        syn_card = QFrame()
        syn_card.setStyleSheet("background: #141c2e; border: 1px solid #1e293b; border-radius: 8px; padding: 16px;")
        syn_layout = QVBoxLayout(syn_card)
        syn_layout.setSpacing(10)

        syn_title = QLabel("🎯 Auto-Synthesize from Any Custom Goal")
        syn_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
        syn_layout.addWidget(syn_title)

        syn_help = QLabel("Enter your target objective, application type, or mission scope:")
        syn_help.setStyleSheet("font-size: 11.5px; color: #94a3b8;")
        syn_layout.addWidget(syn_help)

        self.auto_goal_edit = QLineEdit()
        self.auto_goal_edit.setPlaceholderText("e.g. AI-Powered Medical Fact Checker, Crypto Trading Dashboard, 3D Game UI...")
        syn_layout.addWidget(self.auto_goal_edit)

        syn_layout.addStretch()

        self.btn_auto_create = QPushButton("⚡ Auto-Generate && Register Custom Squad")
        self.btn_auto_create.setProperty("class", "btn-primary")
        self.btn_auto_create.setFixedHeight(38)
        self.btn_auto_create.clicked.connect(self.on_auto_synthesize)
        syn_layout.addWidget(self.btn_auto_create)

        cards_row.addWidget(syn_card, stretch=1)

        # Card 2: 1-Click Fast Presets
        pre_card = QFrame()
        pre_card.setStyleSheet("background: #141c2e; border: 1px solid #1e293b; border-radius: 8px; padding: 16px;")
        pre_layout = QVBoxLayout(pre_card)
        pre_layout.setSpacing(10)

        pre_title = QLabel("🚀 1-Click High-Performance Presets")
        pre_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #a855f7;")
        pre_layout.addWidget(pre_title)

        pre_help = QLabel("Select curated multi-agent architectures ready for enterprise tasks:")
        pre_help.setStyleSheet("font-size: 11.5px; color: #94a3b8;")
        pre_layout.addWidget(pre_help)

        self.preset_combo = QComboBox()
        for p in AUTOGEN_TEMPLATES:
            self.preset_combo.addItem(p["name"])
        self.preset_combo.currentIndexChanged.connect(self.on_preset_combo_changed)
        pre_layout.addWidget(self.preset_combo)

        self.preset_desc_lbl = QLabel(AUTOGEN_TEMPLATES[0]["desc"])
        self.preset_desc_lbl.setWordWrap(True)
        self.preset_desc_lbl.setStyleSheet("color: #94a3b8; font-size: 11.5px; font-style: italic;")
        pre_layout.addWidget(self.preset_desc_lbl)

        pre_layout.addStretch()

        self.btn_add_preset = QPushButton("➕ Add Selected Preset to Roster")
        self.btn_add_preset.setProperty("class", "btn-secondary")
        self.btn_add_preset.setFixedHeight(38)
        self.btn_add_preset.clicked.connect(self.on_add_preset)
        pre_layout.addWidget(self.btn_add_preset)

        cards_row.addWidget(pre_card, stretch=1)
        layout.addLayout(cards_row)
        layout.addStretch()

    def on_preset_combo_changed(self, idx: int):
        if 0 <= idx < len(AUTOGEN_TEMPLATES):
            self.preset_desc_lbl.setText(AUTOGEN_TEMPLATES[idx]["desc"])

    # =========================================================================
    # TAB 3: ASSEMBLE CUSTOM SQUAD
    # =========================================================================
    def setup_assemble_tab(self, parent: QWidget):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        form_widget = QWidget()
        form_layout = QVBoxLayout(form_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)

        # Name & Scope
        row_names = QHBoxLayout()
        row_names.setSpacing(12)

        v_name = QVBoxLayout()
        v_name.addWidget(QLabel("<b>Squad Codename:</b>"))
        self.squad_name_edit = QLineEdit()
        self.squad_name_edit.setPlaceholderText("e.g. Web Dev Strike Team, Research & Fact Checking")
        v_name.addWidget(self.squad_name_edit)
        row_names.addLayout(v_name, stretch=1)

        v_scope = QVBoxLayout()
        v_scope.addWidget(QLabel("<b>Specialization / Scope:</b>"))
        self.squad_desc_edit = QLineEdit()
        self.squad_desc_edit.setPlaceholderText("Brief scope summary")
        v_scope.addWidget(self.squad_desc_edit)
        row_names.addLayout(v_scope, stretch=1)

        form_layout.addLayout(row_names)

        # Task directive
        form_layout.addWidget(QLabel("<b>Preset Mission Directive:</b>"))
        self.squad_task_edit = QTextEdit()
        self.squad_task_edit.setPlaceholderText("Default task instructions assigned when launching this squad...")
        self.squad_task_edit.setFixedHeight(100)
        form_layout.addWidget(self.squad_task_edit)

        # Specialist checkboxes in a 3-column grid
        form_layout.addWidget(QLabel("<b>Assign Specialist LLMs to Squad:</b>"))
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(4, 4, 4, 4)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        agent_options = [
            ("deepseek", "⚡ DeepSeek (Coder & Logic)"),
            ("chatgpt", "🤖 ChatGPT (Synthesis & Copy)"),
            ("claude", "🛡 Claude (Review & Safety)"),
            ("perplexity", "🔍 Perplexity (Live Search)"),
            ("dalle", "🎨 DALL-E 3 (Visual Design)"),
            ("copilot", "💻 Copilot (Enterprise Tools)"),
            ("meta_ai", "🌐 Meta AI (Social & Viral)"),
            ("mistral", "🌪 Mistral (Multilingual)"),
            ("nvidia_ai", "🟢 Nvidia NIM (Compute & Math)"),
        ]

        for i, (aid, label) in enumerate(agent_options):
            cb = QCheckBox(label)
            self.create_agent_boxes[aid] = cb
            grid.addWidget(cb, i // 3, i % 3)

        form_layout.addWidget(grid_widget)

        # Save button
        self.btn_save_squad = QPushButton("💾 Register Squad in Roster")
        self.btn_save_squad.setProperty("class", "btn-primary")
        self.btn_save_squad.setFixedHeight(40)
        self.btn_save_squad.clicked.connect(self.on_save_manual_squad)
        form_layout.addWidget(self.btn_save_squad)

        form_layout.addStretch()
        form_scroll.setWidget(form_widget)
        layout.addWidget(form_scroll)

    # =========================================================================
    # LOGIC & EVENT HANDLERS
    # =========================================================================
    def on_open_skills_vault(self):
        try:
            from gui.widgets.skill_importer_dialog import SkillImporterDialog
            dialog = SkillImporterDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Skills Vault Error", f"Failed to open Skills Vault: {e}")

    def on_open_agency_catalog(self):
        try:
            from gui.widgets.agency_agents_dialog import AgencyAgentsDialog
            dialog = AgencyAgentsDialog(self)
            dialog.agent_selected.connect(self.on_agency_agent_selected)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Catalog Error", f"Failed to open Agency Agents Catalog: {e}")

    def on_agency_agent_selected(self, agent: dict):
        agent_name = agent.get("name", "Specialist")
        emoji = agent.get("emoji", "")
        div_label = agent.get("division_label", "General")
        vibe = agent.get("vibe", "")
        desc = agent.get("description", "")

        self.tab_widget.setCurrentIndex(2)  # Switch to Assemble Tab
        self.squad_name_edit.setText(f"{agent_name} Strike Squad")
        self.squad_desc_edit.setText(f"[{div_label}] {vibe or desc[:80]}")
        self.squad_task_edit.setPlainText(
            f"Act as senior specialist: {agent_name} ({div_label}).\n"
            f"Directive: {vibe}\n"
            f"Deliverable: {desc}\n"
            f"Execute specialized domain task adhering to production-grade quality."
        )

        div_lower = agent.get("division", "").lower()
        for cb in self.create_agent_boxes.values():
            cb.setChecked(False)

        if div_lower in ["engineering", "testing", "game-development"]:
            self.create_agent_boxes.get("deepseek", QCheckBox()).setChecked(True)
            self.create_agent_boxes.get("claude", QCheckBox()).setChecked(True)
        elif div_lower in ["security"]:
            self.create_agent_boxes.get("claude", QCheckBox()).setChecked(True)
            self.create_agent_boxes.get("deepseek", QCheckBox()).setChecked(True)
        elif div_lower in ["design", "spatial-computing"]:
            self.create_agent_boxes.get("dalle", QCheckBox()).setChecked(True)
            self.create_agent_boxes.get("chatgpt", QCheckBox()).setChecked(True)
        elif div_lower in ["marketing", "paid-media", "sales"]:
            self.create_agent_boxes.get("meta_ai", QCheckBox()).setChecked(True)
            self.create_agent_boxes.get("chatgpt", QCheckBox()).setChecked(True)
        elif div_lower in ["research", "academic", "healthcare", "gis"]:
            self.create_agent_boxes.get("perplexity", QCheckBox()).setChecked(True)
            self.create_agent_boxes.get("claude", QCheckBox()).setChecked(True)
        else:
            self.create_agent_boxes.get("chatgpt", QCheckBox()).setChecked(True)
            self.create_agent_boxes.get("deepseek", QCheckBox()).setChecked(True)

        QMessageBox.information(
            self,
            "Agent Loaded into Form",
            f"Loaded '{agent_name}' ({div_label}) into the Assemble Custom Squad tab!\nClick 'Register Squad in Roster' to finalize."
        )

    def on_add_all_agency_squads(self):
        added, total = agency_manager.register_all_agents_as_squads()
        self.load_squads_from_file()
        if added > 0:
            QMessageBox.information(
                self,
                "Agency Squads Added",
                f"⚡ Successfully registered {added} new Agency Squads into your Roster!\nTotal squads ready: {total}"
            )
        else:
            QMessageBox.information(
                self,
                "Squad Roster Synchronized",
                f"All 287+ Agency Squads are already present in your Roster!\nTotal squads: {total}"
            )

    def on_division_filter_changed(self, idx: int):
        self.display_limit = 60
        self.render_squads_list()

    def on_squad_search_changed(self, text: str):
        self.display_limit = 60
        self.render_squads_list()

    def on_show_more_squads(self):
        self.display_limit += 60
        self.render_squads_list()

    def on_auto_synthesize(self):
        goal = self.auto_goal_edit.text().strip()
        if not goal:
            QMessageBox.warning(self, "Missing Scope", "Please enter a project domain / scope.")
            return

        goal_lower = goal.lower()
        selected_ai = ["gemini"]
        if any(k in goal_lower for k in ["code", "web", "dev", "app", "game", "software", "api", "tech", "crypto"]):
            selected_ai.append("deepseek")
        if any(k in goal_lower for k in ["security", "audit", "review", "test", "qa", "safe"]):
            selected_ai.append("claude")
        if any(k in goal_lower for k in ["search", "fact", "research", "medical", "citation", "live", "news"]):
            selected_ai.append("perplexity")
        if any(k in goal_lower for k in ["design", "image", "ui", "ux", "visual", "art", "graphic"]):
            selected_ai.append("dalle")
        if any(k in goal_lower for k in ["social", "viral", "marketing", "post", "video", "trend"]):
            selected_ai.append("meta_ai")
        if any(k in goal_lower for k in ["performance", "gpu", "speed", "fast", "math", "cuda"]):
            selected_ai.append("nvidia_ai")
        if any(k in goal_lower for k in ["translate", "language", "europe", "french", "german", "spanish"]):
            selected_ai.append("mistral")
        if any(k in goal_lower for k in ["office", "excel", "sheet", "doc", "enterprise", "workflow"]):
            selected_ai.append("copilot")
        if "chatgpt" not in selected_ai and len(selected_ai) < 4:
            selected_ai.append("chatgpt")

        new_squad = {
            "name": f"{goal.title()[:35]} Strike Team",
            "task": f"Execute end-to-end multi-agent mission for: {goal}",
            "desc": f"Specialized AI team configured for {goal}",
            "agents": list(dict.fromkeys(selected_ai)),
            "created": time.strftime("%Y-%m-%d %H:%M")
        }
        self.subagents.insert(0, new_squad)
        self.save_squads_to_file()
        self.auto_goal_edit.clear()
        self.tab_widget.setCurrentIndex(0)  # Switch to roster
        QMessageBox.information(
            self,
            "Squad Created",
            f"Registered squad '{new_squad['name']}' with {len(new_squad['agents'])} specialist agents!"
        )

    def on_add_preset(self):
        idx = self.preset_combo.currentIndex()
        if 0 <= idx < len(AUTOGEN_TEMPLATES):
            chosen = AUTOGEN_TEMPLATES[idx]
            if not any(s["name"] == chosen["name"] for s in self.subagents):
                new_sq = chosen.copy()
                new_sq["created"] = time.strftime("%Y-%m-%d %H:%M")
                self.subagents.insert(0, new_sq)
                self.save_squads_to_file()
                self.tab_widget.setCurrentIndex(0)
                QMessageBox.information(self, "Preset Added", f"Added '{chosen['name']}' to squad roster!")
            else:
                QMessageBox.information(self, "Already Exists", "This squad preset is already in your roster.")

    def on_save_manual_squad(self):
        name = self.squad_name_edit.text().strip()
        task = self.squad_task_edit.toPlainText().strip()
        desc = self.squad_desc_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing Name", "Please enter a squad codename.")
            return

        agents = ["gemini"]
        for aid, cb in self.create_agent_boxes.items():
            if cb.isChecked():
                agents.append(aid)

        if len(agents) < 2:
            QMessageBox.warning(self, "No Specialist Selected", "Please assign at least one specialist.")
            return

        new_sq = {
            "name": name,
            "task": task,
            "desc": desc,
            "agents": agents,
            "created": time.strftime("%Y-%m-%d %H:%M")
        }
        self.subagents.insert(0, new_sq)
        self.save_squads_to_file()

        self.squad_name_edit.clear()
        self.squad_task_edit.clear()
        self.squad_desc_edit.clear()
        for cb in self.create_agent_boxes.values():
            cb.setChecked(False)

        self.tab_widget.setCurrentIndex(0)
        QMessageBox.information(self, "Squad Registered", f"Squad '{name}' registered successfully!")

    def on_scan_learner(self):
        new_sqs = detect_and_create_repeated_pattern_squads(min_repetition_threshold=1)
        if new_sqs:
            self.load_squads_from_file()
            QMessageBox.information(
                self,
                "Learner Success",
                f"Autonomously created and registered {len(new_sqs)} squads based on your repeated mission patterns!"
            )
        else:
            QMessageBox.information(
                self,
                "Pattern Scan Complete",
                "All repeated task patterns already have dedicated squads registered."
            )

    def load_squads_from_file(self):
        if os.path.exists(SUBAGENTS_FILE):
            try:
                with open(SUBAGENTS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.subagents = data
            except Exception:
                self.subagents = []
        else:
            self.subagents = []
        self.render_squads_list()

    def save_squads_to_file(self):
        os.makedirs("json", exist_ok=True)
        with open(SUBAGENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.subagents, f, indent=2)
        self.render_squads_list()
        self.squads_updated.emit()

    def render_squads_list(self):
        while self.squads_list_layout.count():
            item = self.squads_list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        total_count = len(self.subagents)
        search_q = self.squad_search_edit.text().strip().lower() if hasattr(self, "squad_search_edit") else ""
        selected_div = self.div_filter_combo.currentData() if hasattr(self, "div_filter_combo") else "all"

        filtered_squads = []
        for idx, sq in enumerate(self.subagents):
            sq_div = (sq.get("division") or "").lower()
            if selected_div and selected_div != "all" and sq_div != selected_div:
                continue

            if not search_q:
                filtered_squads.append((idx, sq))
                continue

            name = sq.get("name", "").lower()
            desc = sq.get("desc", "").lower()
            task = sq.get("task", "").lower()
            agents = " ".join(sq.get("agents", [])).lower()
            if search_q in name or search_q in desc or search_q in task or search_q in agents or search_q in sq_div:
                filtered_squads.append((idx, sq))

        if hasattr(self, "roster_count_badge"):
            if search_q or (selected_div and selected_div != "all"):
                self.roster_count_badge.setText(f"{len(filtered_squads)} / {total_count} Squads")
            else:
                self.roster_count_badge.setText(f"{total_count} Squads Ready")

        if not filtered_squads:
            msg = "No squads match your search filter." if (search_q or selected_div != "all") else "No squads registered yet. Assemble your first squad or use the Auto-Generator."
            no_squads_lbl = QLabel(msg)
            no_squads_lbl.setStyleSheet("color: #64748b; font-size: 13px; padding: 24px;")
            self.squads_list_layout.addWidget(no_squads_lbl)
            return

        display_items = filtered_squads[:self.display_limit]

        for orig_idx, sq in display_items:
            card = self.create_squad_card(sq, orig_idx)
            self.squads_list_layout.addWidget(card)

        if len(filtered_squads) > self.display_limit:
            rem = len(filtered_squads) - self.display_limit
            more_btn = QPushButton(f"▼ Show More ({rem} remaining squads)...")
            more_btn.setProperty("class", "btn-secondary")
            more_btn.setFixedHeight(34)
            more_btn.clicked.connect(self.on_show_more_squads)
            self.squads_list_layout.addWidget(more_btn)

    def create_squad_card(self, sq: dict, orig_idx: int) -> QFrame:
        card = QFrame()
        is_auto = sq.get("auto_learned", False)
        is_agency = sq.get("agency_agent", False)
        div = sq.get("division", "general")

        div_color = "#38bdf8"
        if div in ["engineering", "testing"]:
            div_color = "#3b82f6"
        elif div in ["security"]:
            div_color = "#ef4444"
        elif div in ["design", "spatial-computing"]:
            div_color = "#ec4899"
        elif div in ["marketing", "sales", "paid-media"]:
            div_color = "#8b5cf6"
        elif div in ["research", "academic", "healthcare"]:
            div_color = "#06b6d4"

        # Safe RGBA parsing for Qt QSS (prevents 8-digit hex color inversion bug)
        div_bg = "rgba(56, 189, 248, 0.12)"
        div_border = "rgba(56, 189, 248, 0.35)"
        h = div_color.lstrip("#")
        if len(h) == 6:
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            div_bg = f"rgba({r}, {g}, {b}, 0.12)"
            div_border = f"rgba({r}, {g}, {b}, 0.35)"

        card.setStyleSheet(f"""
            QFrame {{
                background-color: #141c2e;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-left: 4px solid {div_color};
                border-radius: 8px;
                padding: 10px;
            }}
            QFrame:hover {{
                background-color: #1a253c;
                border: 1px solid #38bdf8;
            }}
        """)

        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(8, 8, 8, 8)
        c_layout.setSpacing(6)

        # Top Tag Row (Placed on top of the title)
        tag_row = QHBoxLayout()
        tag_row.setContentsMargins(0, 0, 0, 0)
        tag_row.setSpacing(6)

        if div and div != "general":
            div_badge = QLabel(div.upper())
            div_badge.setStyleSheet(
                f"background: {div_bg}; color: {div_color}; "
                f"border: 1px solid {div_border}; border-radius: 4px; "
                f"padding: 2px 8px; font-size: 9.5px; font-weight: 700;"
            )
            tag_row.addWidget(div_badge)

        if is_auto:
            badge = QLabel("AUTO-LEARNED")
            badge.setStyleSheet(
                "background: rgba(16, 185, 129, 0.15); color: #10b981; "
                "border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 4px; "
                "padding: 2px 6px; font-size: 9.5px; font-weight: 700;"
            )
            tag_row.addWidget(badge)
        elif is_agency:
            badge = QLabel("AGENCY SPECIALIST")
            badge.setStyleSheet(
                "background: rgba(56, 189, 248, 0.15); color: #38bdf8; "
                "border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 4px; "
                "padding: 2px 6px; font-size: 9.5px; font-weight: 700;"
            )
            tag_row.addWidget(badge)

        tag_row.addStretch()

        if sq.get("created"):
            created_lbl = QLabel(sq["created"])
            created_lbl.setStyleSheet("font-size: 10.5px; color: #64748b;")
            tag_row.addWidget(created_lbl)

        c_layout.addLayout(tag_row)

        # Title Row
        name_lbl = QLabel(sq.get('name', 'Squad'))
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #f8fafc;")
        c_layout.addWidget(name_lbl)

        # Description / vibe
        if sq.get("desc"):
            desc_lbl = QLabel(sq["desc"])
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("font-size: 11.5px; color: #94a3b8;")
            c_layout.addWidget(desc_lbl)

        # Assigned Agents Chips
        agents_list = sq.get("agents", [])
        if agents_list:
            chips_row = QHBoxLayout()
            chips_row.setSpacing(6)
            chips_row.addWidget(QLabel("<span style='font-size: 11px; color: #64748b;'>Roster:</span>"))
            for aid in agents_list:
                chip_name, chip_color = AGENT_DISPLAY_MAP.get(aid, (aid.title(), "#94a3b8"))
                chip_lbl = QLabel(chip_name)
                chip_lbl.setStyleSheet(
                    f"background: #0b1120; color: {chip_color}; "
                    f"border: 1px solid #1e293b; border-radius: 4px; "
                    f"padding: 2px 6px; font-size: 10.5px; font-weight: 600;"
                )
                chips_row.addWidget(chip_lbl)
            chips_row.addStretch()
            c_layout.addLayout(chips_row)

        # Preset Task snippet
        task_snippet = sq.get("task", "")
        if task_snippet:
            task_lbl = QLabel(f"<b>Directive:</b> {task_snippet[:100]}...")
            task_lbl.setWordWrap(True)
            task_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
            c_layout.addWidget(task_lbl)

        # Action Buttons Row (aligned neatly to right or fixed widths)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 4, 0, 0)
        btn_row.setSpacing(8)

        btn_deploy = QPushButton("🚀 Deploy Squad")
        btn_deploy.setProperty("class", "btn-primary")
        btn_deploy.setFixedWidth(140)
        btn_deploy.setFixedHeight(30)
        btn_deploy.clicked.connect(lambda _, s=sq: self.deploy_squad(s))
        btn_row.addWidget(btn_deploy)

        btn_del = QPushButton("🗑 Decommission")
        btn_del.setProperty("class", "btn-secondary")
        btn_del.setFixedWidth(130)
        btn_del.setFixedHeight(30)
        btn_del.clicked.connect(lambda _, i=orig_idx: self.delete_squad(i))
        btn_row.addWidget(btn_del)

        btn_row.addStretch()
        c_layout.addLayout(btn_row)

        return card

    def deploy_squad(self, squad_dict: dict):
        agents_str = ",".join(squad_dict.get("agents", ["gemini"]))
        task_str = squad_dict.get("task", "Execute multi-agent mission")
        label_str = f"{squad_dict.get('name', 'Squad')} @ {time.strftime('%H:%M:%S')}"
        self.launch_squad_requested.emit(task_str, agents_str, label_str)

    def delete_squad(self, index: int):
        if 0 <= index < len(self.subagents):
            self.subagents.pop(index)
            self.save_squads_to_file()
