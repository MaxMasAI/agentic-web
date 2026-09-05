"""
gui/pages/squad_roster.py - Autonomous AI Squad Generation & Roster Management
"""

import os
import json
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QCheckBox, QComboBox, QFrame, QScrollArea,
    QMessageBox, QGroupBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from core.squad_learner import detect_and_create_repeated_pattern_squads

SUBAGENTS_FILE = os.path.join("json", "subagents.json")

AUTOGEN_TEMPLATES = [
    {
        "name": "⚡ Full-Stack Web & E-Commerce Prototypers",
        "desc": "High-velocity web development, responsive CSS, API architecture & visual assets",
        "task": "Develop a production-ready responsive e-commerce web application with animated product cards and interactive checkout",
        "agents": ["gemini", "deepseek", "chatgpt", "dalle"]
    },
    {
        "name": "🛡️ Architecture, Security & QA Red Team",
        "desc": "Deep technical analysis, zero-trust security audit, accessibility compliance & unit testing",
        "task": "Perform a comprehensive security audit, architecture review, and defensive programming verification",
        "agents": ["gemini", "claude", "deepseek", "perplexity"]
    },
    {
        "name": "📈 Viral Growth, Content & Social Strategy",
        "desc": "Audience hooks, platform-tailored copy, trend citations & graphic design",
        "task": "Create a multi-channel viral product launch campaign with social copy, hashtags, and hero visual assets",
        "agents": ["gemini", "chatgpt", "meta_ai", "dalle"]
    },
    {
        "name": "🏎️ High-Performance Compute & Scientific Reasoning",
        "desc": "GPU optimization, algorithmic complexity analysis & live technical search",
        "task": "Benchmark computational efficiency, optimize algorithm latency, and verify live scientific citations",
        "agents": ["gemini", "nvidia_ai", "deepseek", "perplexity"]
    },
    {
        "name": "🌐 Enterprise Multilingual & Logistics Hub",
        "desc": "Cross-language localization, enterprise spreadsheets & structured documentation",
        "task": "Translate and localize software documentation across European languages with formatted enterprise sheets",
        "agents": ["gemini", "mistral", "copilot", "chatgpt"]
    }
]


class SquadRosterPage(QWidget):
    launch_squad_requested = Signal(str, str, str)
    squads_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.subagents = []
        self.create_agent_boxes = {}
        self.init_ui()

    def init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        self.layout = QVBoxLayout(container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(16)

        # Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🤖 AGENT SQUAD ROSTER")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Design Specialized Sub-Agent Teams & Trigger Instant Deployments")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        self.layout.addLayout(t_box)

        # Autonomous AI Squad Generation Box
        auto_grp = QGroupBox("✨ Autonomous AI Squad Generator (Auto-Create for Future Usage)")
        auto_layout = QVBoxLayout(auto_grp)
        auto_layout.setSpacing(10)

        auto_desc = QLabel("Let the AI orchestrator analyze your project scope and automatically assemble synergy-matched specialist teams.")
        auto_desc.setStyleSheet("font-size: 12px; color: #cbd5e1;")
        auto_layout.addWidget(auto_desc)

        row_auto = QHBoxLayout()
        row_auto.setSpacing(16)

        # Custom Auto-Synthesizer
        v_syn = QVBoxLayout()
        v_syn.addWidget(QLabel("<b>🤖 Auto-Synthesize from Any Custom Goal:</b>"))
        self.auto_goal_edit = QLineEdit()
        self.auto_goal_edit.setPlaceholderText("e.g. AI-Powered Medical Fact Checker, Crypto Trading Dashboard, 3D Game UI...")
        v_syn.addWidget(self.auto_goal_edit)

        self.btn_auto_create = QPushButton("✨ Auto-Generate & Register Custom Squad")
        self.btn_auto_create.setProperty("class", "primary-btn")
        self.btn_auto_create.clicked.connect(self.on_auto_synthesize)
        v_syn.addWidget(self.btn_auto_create)
        row_auto.addLayout(v_syn, stretch=1)

        # 1-Click Fast Presets
        v_pre = QVBoxLayout()
        v_pre.addWidget(QLabel("<b>⚡ 1-Click Fast Squad Presets:</b>"))
        self.preset_combo = QComboBox()
        for p in AUTOGEN_TEMPLATES:
            self.preset_combo.addItem(p["name"])
        v_pre.addWidget(self.preset_combo)

        self.btn_add_preset = QPushButton("➕ Add Selected Preset to Roster")
        self.btn_add_preset.clicked.connect(self.on_add_preset)
        v_pre.addWidget(self.btn_add_preset)
        row_auto.addLayout(v_pre, stretch=1)

        auto_layout.addLayout(row_auto)
        self.layout.addWidget(auto_grp)

        # Split 2 Columns: Manual Create vs Registered List
        split = QHBoxLayout()
        split.setSpacing(20)

        # Left: Manual Assemble Form
        left_v = QVBoxLayout()
        left_v.setSpacing(10)

        sec_create = QLabel("➕ Assemble New Squad")
        sec_create.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 4px;")
        left_v.addWidget(sec_create)

        left_v.addWidget(QLabel("<b>Squad Codename:</b>"))
        self.squad_name_edit = QLineEdit()
        self.squad_name_edit.setPlaceholderText("e.g. Web Dev Strike Team, Research & Fact Checking")
        left_v.addWidget(self.squad_name_edit)

        left_v.addWidget(QLabel("<b>Preset Mission Goal:</b>"))
        self.squad_task_edit = QTextEdit()
        self.squad_task_edit.setPlaceholderText("Default task assigned when launching this squad...")
        self.squad_task_edit.setFixedHeight(90)
        left_v.addWidget(self.squad_task_edit)

        left_v.addWidget(QLabel("<b>Specialization / Scope:</b>"))
        self.squad_desc_edit = QLineEdit()
        self.squad_desc_edit.setPlaceholderText("Brief scope summary")
        left_v.addWidget(self.squad_desc_edit)

        left_v.addWidget(QLabel("<b>Assign Specialists to Squad:</b> (Gemini Master Leader always included)"))
        
        agent_options = [
            ("deepseek", "DeepSeek (Creative & Coder)"),
            ("chatgpt", "ChatGPT (Copy & Synthesis)"),
            ("claude", "Claude (Critique & Review)"),
            ("perplexity", "Perplexity AI (Live Web Search)"),
            ("copilot", "Microsoft Copilot (Workflow Specialist)"),
            ("meta_ai", "Meta AI (Social & Engagement)"),
            ("mistral", "Mistral Le Chat (Multilingual Logic)"),
            ("dalle", "DALL-E 3 (Visual Designer)"),
            ("nvidia_ai", "Nvidia NIM (High-Performance Compute)"),
        ]
        for aid, label in agent_options:
            cb = QCheckBox(label)
            self.create_agent_boxes[aid] = cb
            left_v.addWidget(cb)

        self.btn_save_squad = QPushButton("💾 Register Squad in Roster")
        self.btn_save_squad.setProperty("class", "primary-btn")
        self.btn_save_squad.setFixedHeight(38)
        self.btn_save_squad.clicked.connect(self.on_save_manual_squad)
        left_v.addWidget(self.btn_save_squad)

        split.addLayout(left_v, stretch=1)

        # Right: Registered Roster List
        right_v = QVBoxLayout()
        right_v.setSpacing(10)

        top_r = QHBoxLayout()
        sec_roster = QLabel("📦 Registered Squad Roster")
        sec_roster.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        top_r.addWidget(sec_roster)
        top_r.addStretch()

        self.btn_scan_learner = QPushButton("🧠 Scan History & Auto-Create Squads")
        self.btn_scan_learner.setStyleSheet("font-size: 11px; padding: 4px 10px; border-radius: 6px;")
        self.btn_scan_learner.clicked.connect(self.on_scan_learner)
        top_r.addWidget(self.btn_scan_learner)
        right_v.addLayout(top_r)

        self.squads_list_container = QWidget()
        self.squads_list_layout = QVBoxLayout(self.squads_list_container)
        self.squads_list_layout.setContentsMargins(0, 0, 0, 0)
        self.squads_list_layout.setSpacing(10)
        right_v.addWidget(self.squads_list_container)

        split.addLayout(right_v, stretch=1)
        self.layout.addLayout(split)

        self.layout.addStretch()
        scroll.setWidget(container)

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.addWidget(scroll)

        self.load_squads_from_file()

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
            "name": f"🎯 {goal.title()[:35]} Strike Team",
            "task": f"Execute end-to-end multi-agent mission for: {goal}",
            "desc": f"Specialized AI team configured for {goal}",
            "agents": list(dict.fromkeys(selected_ai)),
            "created": time.strftime("%Y-%m-%d %H:%M")
        }
        self.subagents.append(new_squad)
        self.save_squads_to_file()
        self.auto_goal_edit.clear()
        QMessageBox.information(self, "Squad Created", f"Registered squad '{new_squad['name']}' with {len(new_squad['agents'])} specialist agents!")

    def on_add_preset(self):
        idx = self.preset_combo.currentIndex()
        if 0 <= idx < len(AUTOGEN_TEMPLATES):
            chosen = AUTOGEN_TEMPLATES[idx]
            if not any(s["name"] == chosen["name"] for s in self.subagents):
                new_sq = chosen.copy()
                new_sq["created"] = time.strftime("%Y-%m-%d %H:%M")
                self.subagents.append(new_sq)
                self.save_squads_to_file()
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
        self.subagents.append(new_sq)
        self.save_squads_to_file()

        self.squad_name_edit.clear()
        self.squad_task_edit.clear()
        self.squad_desc_edit.clear()
        for cb in self.create_agent_boxes.values():
            cb.setChecked(False)

        QMessageBox.information(self, "Squad Registered", f"Squad '{name}' registered successfully!")

    def on_scan_learner(self):
        new_sqs = detect_and_create_repeated_pattern_squads(min_repetition_threshold=1)
        if new_sqs:
            self.load_squads_from_file()
            QMessageBox.information(self, "Learner Success", f"Autonomously created and registered {len(new_sqs)} squads based on your repeated mission patterns!")
        else:
            QMessageBox.information(self, "Pattern Scan Complete", "All repeated task patterns already have dedicated squads registered.")

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

        if not self.subagents:
            no_squads_lbl = QLabel("No squads registered yet. Assemble your first squad or use the Auto-Generator.")
            no_squads_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 12px;")
            self.squads_list_layout.addWidget(no_squads_lbl)
            return

        for idx, sq in enumerate(self.subagents):
            card = QFrame()
            is_auto = sq.get("auto_learned", False)
            border_col = "#34d399" if is_auto else "#818cf8"

            card.setStyleSheet(f"""
                QFrame {{
                    background: rgba(15, 23, 42, 0.75);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-left: 4px solid {border_col};
                    border-radius: 10px;
                    padding: 10px;
                }}
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(8, 8, 8, 8)
            c_layout.setSpacing(6)

            # Header
            hdr = QHBoxLayout()
            name_lbl = QLabel(f"<b>{sq.get('name', 'Squad')}</b>")
            name_lbl.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #f8fafc;")
            hdr.addWidget(name_lbl)

            if is_auto:
                badge = QLabel("BRAIN AUTO-LEARNED")
                badge.setStyleSheet("background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid #10b98155; border-radius: 10px; padding: 2px 8px; font-size: 9px; font-weight: 800;")
                hdr.addWidget(badge)

            hdr.addStretch()
            created_lbl = QLabel(sq.get("created", ""))
            created_lbl.setStyleSheet("font-size: 10px; color: #64748b; font-family: monospace;")
            hdr.addWidget(created_lbl)
            c_layout.addLayout(hdr)

            if sq.get("desc"):
                desc_lbl = QLabel(sq["desc"])
                desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
                c_layout.addWidget(desc_lbl)

            roster_lbl = QLabel(f"<b>Roster:</b> <code>{', '.join(sq.get('agents', []))}</code>")
            roster_lbl.setStyleSheet("font-size: 11px; color: #38bdf8;")
            c_layout.addWidget(roster_lbl)

            task_snippet = sq.get("task", "")
            task_lbl = QLabel(f"<b>Preset Task:</b> {task_snippet[:90]}...")
            task_lbl.setStyleSheet("font-size: 11.5px; color: #cbd5e1;")
            c_layout.addWidget(task_lbl)

            # Action Buttons
            btn_row = QHBoxLayout()
            btn_deploy = QPushButton("🚀 Deploy Squad")
            btn_deploy.setProperty("class", "primary-btn")
            btn_deploy.setFixedHeight(28)
            btn_deploy.clicked.connect(lambda _, s=sq: self.deploy_squad(s))
            btn_row.addWidget(btn_deploy)

            btn_del = QPushButton("🗑 Decommission")
            btn_del.setProperty("class", "danger-btn")
            btn_del.setFixedHeight(28)
            btn_del.clicked.connect(lambda _, i=idx: self.delete_squad(i))
            btn_row.addWidget(btn_del)

            c_layout.addLayout(btn_row)
            self.squads_list_layout.addWidget(card)

    def deploy_squad(self, squad_dict: dict):
        agents_str = ",".join(squad_dict.get("agents", ["gemini"]))
        task_str = squad_dict.get("task", "Execute multi-agent mission")
        label_str = f"{squad_dict.get('name', 'Squad')} @ {time.strftime('%H:%M:%S')}"
        self.launch_squad_requested.emit(task_str, agents_str, label_str)

    def delete_squad(self, index: int):
        if 0 <= index < len(self.subagents):
            self.subagents.pop(index)
            self.save_squads_to_file()
