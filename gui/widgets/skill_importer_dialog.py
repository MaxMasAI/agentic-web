"""
gui/widgets/skill_importer_dialog.py -Claude AI-Style Dynamic Skills Vault & Importer
Conforms strictly to design_system_ui_theme_documentation.md
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QTabWidget, QWidget, QScrollArea, QFrame, QMessageBox,
    QFileDialog, QSplitter, QComboBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QCursor

from core.skills_manager import skills_manager


class GitHubImportWorker(QThread):
    finished_signal = Signal(bool, str, int)

    def __init__(self, repo_url: str, subpath: str = ""):
        super().__init__()
        self.repo_url = repo_url
        self.subpath = subpath

    def run(self):
        try:
            skills = skills_manager.import_from_github(self.repo_url, subpath=self.subpath if self.subpath else None)
            self.finished_signal.emit(True, f"Successfully imported skills from {self.repo_url}!", len(skills))
        except Exception as e:
            self.finished_signal.emit(False, str(e), 0)


class SkillImporterDialog(QDialog):
    """Full-featured  AI-grade Skills Manager & Ingestor Dialog."""
    skills_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(" AI Skills Vault & Dynamic Ingestor")
        self.resize(1120, 720)
        self.setMinimumSize(920, 580)
        self.worker = None
        self.selected_skill_id = None
        self.cards_map = {}
        self.init_ui()
        self.refresh_installed_skills()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        # Header
        hdr = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("AI SKILLS VAULT & DYNAMIC INGESTOR")
        title.setProperty("class", "metric-value")
        sub = QLabel("Ingest, learn, and auto-inject skills from any GitHub Repo or local Markdown file (*.md / SKILL.md)")
        sub.setProperty("class", "metric-label")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        hdr.addLayout(title_box)
        hdr.addStretch()

        self.lbl_stats = QLabel("0 Skills in skills/")
        self.lbl_stats.setProperty("class", "badge-idle")
        hdr.addWidget(self.lbl_stats)
        main_layout.addLayout(hdr)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_installed_tab(), "Installed Skills Roster")
        self.tabs.addTab(self.create_github_import_tab(), "Ingest from GitHub Repository")
        self.tabs.addTab(self.create_local_import_tab(), "Import Local Markdown File")
        self.tabs.addTab(self.create_editor_tab(), "Create New SKILL.md")

        main_layout.addWidget(self.tabs, stretch=1)

    # ────────────────────────────────────────────────────────
    # Tab 1: Installed Skills Explorer
    # ────────────────────────────────────────────────────────
    def create_installed_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Filter bar
        f_row = QHBoxLayout()
        f_row.setSpacing(10)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search installed skills by name, tag, or trigger keyword...")
        self.search_edit.textChanged.connect(self.refresh_installed_skills)
        f_row.addWidget(self.search_edit, stretch=1)

        btn_rescan = QPushButton("Refresh Index")
        btn_rescan.setProperty("class", "btn-secondary")
        btn_rescan.clicked.connect(lambda: (skills_manager.scan_and_index_skills(), self.refresh_installed_skills()))
        f_row.addWidget(btn_rescan)
        layout.addLayout(f_row)

        # Splitter: List on Left, Preview/Editor on Right
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: Scrollable Skills List
        left_widget = QWidget()
        left_widget.setMinimumWidth(340)
        left_lay = QVBoxLayout(left_widget)
        left_lay.setContentsMargins(0, 0, 8, 0)
        left_lay.setSpacing(6)

        self.scroll_skills = QScrollArea()
        self.scroll_skills.setWidgetResizable(True)
        self.scroll_skills.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_skills.setProperty("class", "card")

        self.skills_list_container = QWidget()
        self.skills_list_lay = QVBoxLayout(self.skills_list_container)
        self.skills_list_lay.setContentsMargins(6, 6, 6, 6)
        self.skills_list_lay.setSpacing(8)
        self.scroll_skills.setWidget(self.skills_list_container)
        left_lay.addWidget(self.scroll_skills)
        splitter.addWidget(left_widget)

        # Right: Detail Inspector
        right_widget = QWidget()
        right_widget.setMinimumWidth(440)
        right_lay = QVBoxLayout(right_widget)
        right_lay.setContentsMargins(8, 0, 0, 0)
        right_lay.setSpacing(8)

        self.detail_title = QLabel("Select a skill to inspect")
        self.detail_title.setProperty("class", "metric-value")
        right_lay.addWidget(self.detail_title)

        self.detail_meta = QLabel("")
        self.detail_meta.setProperty("class", "metric-label")
        right_lay.addWidget(self.detail_meta)

        self.detail_editor = QTextEdit()
        self.detail_editor.setPlaceholderText("Skill markdown instructions and prompt definitions...")
        right_lay.addWidget(self.detail_editor, stretch=1)

        # Action Buttons
        btn_act_row = QHBoxLayout()
        btn_act_row.setSpacing(10)
        self.btn_save_edit = QPushButton("Save Changes")
        self.btn_save_edit.setProperty("class", "btn-primary")
        self.btn_save_edit.setFixedHeight(34)
        self.btn_save_edit.clicked.connect(self.on_save_skill_edit)
        btn_act_row.addWidget(self.btn_save_edit, stretch=2)

        self.btn_delete_skill = QPushButton("Delete Skill")
        self.btn_delete_skill.setProperty("class", "btn-secondary")
        self.btn_delete_skill.setFixedHeight(34)
        self.btn_delete_skill.clicked.connect(self.on_delete_selected_skill)
        btn_act_row.addWidget(self.btn_delete_skill, stretch=1)

        right_lay.addLayout(btn_act_row)
        splitter.addWidget(right_widget)

        splitter.setSizes([380, 620])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter, stretch=1)
        return tab

    def refresh_installed_skills(self):
        self.cards_map.clear()
        while self.skills_list_lay.count():
            item = self.skills_list_lay.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        query = self.search_edit.text().lower().strip()
        all_skills = skills_manager.list_all_skills()
        self.lbl_stats.setText(f"{len(all_skills)} Skills in skills/")

        filtered = [
            s for s in all_skills
            if not query or (
                query in s.get("name", "").lower() or
                query in s.get("description", "").lower() or
                any(query in t.lower() for t in s.get("triggers", [])) or
                any(query in tg.lower() for tg in s.get("tags", []))
            )
        ]

        if not filtered:
            lbl_empty = QLabel("No skills found. Ingest from GitHub or import a local markdown file.")
            lbl_empty.setProperty("class", "metric-label")
            lbl_empty.setWordWrap(True)
            self.skills_list_lay.addWidget(lbl_empty)
            return

        for skill in filtered:
            card = self.create_skill_card(skill)
            self.cards_map[skill.get("id")] = card
            self.skills_list_lay.addWidget(card)

        self.skills_list_lay.addStretch()

        if self.selected_skill_id:
            s_obj = skills_manager.get_skill_by_id(self.selected_skill_id)
            if s_obj:
                self.inspect_skill(s_obj)

    def create_skill_card(self, skill: dict) -> QFrame:
        card = QFrame()
        is_selected = (skill.get("id") == self.selected_skill_id)
        card.setProperty("class", "card-featured" if is_selected else "card")
        card.setCursor(QCursor(Qt.PointingHandCursor))

        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        # Top Tag Row (Placed on top of the title)
        tag_row = QHBoxLayout()
        tag_row.setContentsMargins(0, 0, 0, 0)
        cat_badge = QLabel(skill.get("category", "engineering").upper())
        cat_badge.setProperty("class", "badge-idle")
        tag_row.addWidget(cat_badge)
        tag_row.addStretch()
        lay.addLayout(tag_row)

        # Title
        name_lbl = QLabel(skill.get('name', 'Skill'))
        name_lbl.setProperty("class", "metric-value")
        lay.addWidget(name_lbl)

        # Description
        if skill.get("description"):
            desc_lbl = QLabel(skill["description"])
            desc_lbl.setProperty("class", "metric-label")
            desc_lbl.setWordWrap(True)
            lay.addWidget(desc_lbl)

        card.mousePressEvent = lambda ev, s=skill: self.inspect_skill(s)
        return card

    def inspect_skill(self, skill: dict):
        self.selected_skill_id = skill.get("id")
        for sid, card in self.cards_map.items():
            card.setProperty("class", "card-featured" if sid == self.selected_skill_id else "card")
            card.style().unpolish(card)
            card.style().polish(card)

        self.detail_title.setText(skill.get('name', 'Skill Details'))
        triggers_str = ", ".join(skill.get("triggers", [])) or "Auto-matched"
        self.detail_meta.setText(f"File: {skill.get('file_rel_path')} | Triggers: {triggers_str}")
        
        content = skills_manager.get_skill_content(self.selected_skill_id) or ""
        self.detail_editor.setPlainText(content)

    def on_save_skill_edit(self):
        if not self.selected_skill_id:
            QMessageBox.warning(self, "No Skill Selected", "Please select a skill from the list to edit.")
            return
        skill = skills_manager.get_skill_by_id(self.selected_skill_id)
        if not skill:
            return

        new_content = self.detail_editor.toPlainText()
        try:
            with open(skill["full_path"], "w", encoding="utf-8") as f:
                f.write(new_content)
            skills_manager.scan_and_index_skills()
            self.refresh_installed_skills()
            QMessageBox.information(self, "Saved", "Skill instructions updated successfully!")
            self.skills_updated.emit()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save skill: {e}")

    def on_delete_selected_skill(self):
        if not self.selected_skill_id:
            return
        res = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete skill '{self.selected_skill_id}' from the skills/ folder?",
            QMessageBox.Yes | QMessageBox.No
        )
        if res == QMessageBox.Yes:
            skills_manager.delete_skill(self.selected_skill_id)
            self.selected_skill_id = None
            self.detail_title.setText("Select a skill to inspect")
            self.detail_meta.setText("")
            self.detail_editor.clear()
            self.refresh_installed_skills()
            self.skills_updated.emit()

    # ────────────────────────────────────────────────────────
    # Tab 2: Ingest from GitHub
    # ────────────────────────────────────────────────────────
    def create_github_import_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        lbl_hdr = QLabel("INGEST SKILLS FROM GITHUB REPOSITORY")
        lbl_hdr.setProperty("class", "sidebar-group-label")
        lay.addWidget(lbl_hdr)

        desc = QLabel(
            "Enter any public or accessible repository URL containing SKILL.md or markdown runbooks "
            "(e.g. Addy Osmani Agent Skills or specialized engineering prompt libraries). "
            "All detected skill files will be automatically cloned, indexed, and stored inside the skills/ folder."
        )
        desc.setProperty("class", "metric-label")
        desc.setWordWrap(True)
        lay.addWidget(desc)

        lbl_url = QLabel("GitHub Repository URL:")
        lbl_url.setProperty("class", "metric-label")
        lay.addWidget(lbl_url)
        self.gh_url_edit = QLineEdit()
        self.gh_url_edit.setPlaceholderText("e.g. https://github.com/addyosmani/agent-skills.git")
        self.gh_url_edit.setText("https://github.com/addyosmani/agent-skills.git")
        lay.addWidget(self.gh_url_edit)

        lbl_sub = QLabel("Target Subdirectory (Optional):")
        lbl_sub.setProperty("class", "metric-label")
        lay.addWidget(lbl_sub)
        self.gh_subpath_edit = QLineEdit()
        self.gh_subpath_edit.setPlaceholderText("e.g. skills or leave blank to scan entire repository")
        lay.addWidget(self.gh_subpath_edit)

        self.btn_gh_import = QPushButton("Clone & Ingest Skills into skills/")
        self.btn_gh_import.setProperty("class", "btn-primary")
        self.btn_gh_import.setFixedHeight(40)
        self.btn_gh_import.clicked.connect(self.on_run_github_import)
        lay.addWidget(self.btn_gh_import)

        self.gh_status_lbl = QLabel("")
        self.gh_status_lbl.setProperty("class", "metric-label")
        lay.addWidget(self.gh_status_lbl)

        lay.addStretch()
        return tab

    def on_run_github_import(self):
        url = self.gh_url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter a valid GitHub repository URL.")
            return

        self.btn_gh_import.setEnabled(False)
        self.gh_status_lbl.setText("Cloning repository and scanning for skill files...")

        self.worker = GitHubImportWorker(url, self.gh_subpath_edit.text().strip())
        self.worker.finished_signal.connect(self.on_github_import_finished)
        self.worker.start()

    def on_github_import_finished(self, success: bool, msg: str, count: int):
        self.btn_gh_import.setEnabled(True)
        if success:
            self.gh_status_lbl.setText(f"{msg}")
            QMessageBox.information(self, "Import Successful", f"{msg}\nTotal Skills Indexed: {count}")
            self.refresh_installed_skills()
            self.skills_updated.emit()
            self.tabs.setCurrentIndex(0)
        else:
            self.gh_status_lbl.setText(f"Error: {msg}")
            QMessageBox.critical(self, "Import Error", f"Failed to ingest from GitHub:\n{msg}")

    # ────────────────────────────────────────────────────────
    # Tab 3: Ingest Local File
    # ────────────────────────────────────────────────────────
    def create_local_import_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        lbl_hdr = QLabel("IMPORT LOCAL MARKDOWN FILE (*.MD / SKILL.MD)")
        lbl_hdr.setProperty("class", "sidebar-group-label")
        lay.addWidget(lbl_hdr)

        desc = QLabel("Select any markdown file from your disk to import it permanently into the skills/ folder.")
        desc.setProperty("class", "metric-label")
        lay.addWidget(desc)

        f_row = QHBoxLayout()
        self.local_file_edit = QLineEdit()
        self.local_file_edit.setPlaceholderText("Click browse to select a .md file...")
        f_row.addWidget(self.local_file_edit, stretch=1)

        btn_browse = QPushButton("Browse...")
        btn_browse.setProperty("class", "btn-secondary")
        btn_browse.clicked.connect(self.on_browse_local_file)
        f_row.addWidget(btn_browse)
        lay.addLayout(f_row)

        btn_import_local = QPushButton("Import Selected File into skills/")
        btn_import_local.setProperty("class", "btn-primary")
        btn_import_local.setFixedHeight(38)
        btn_import_local.clicked.connect(self.on_import_local_file)
        lay.addWidget(btn_import_local)

        lay.addStretch()
        return tab

    def on_browse_local_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Skill Markdown File",
            "",
            "Markdown Files (*.md *.markdown);;All Files (*.*)"
        )
        if file_path:
            self.local_file_edit.setText(file_path)

    def on_import_local_file(self):
        path = self.local_file_edit.text().strip()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Invalid Path", "Please select an existing markdown file.")
            return

        try:
            skill = skills_manager.import_from_file(path)
            QMessageBox.information(self, "Imported", f"Successfully imported '{skill.get('name')}' into skills/!")
            self.refresh_installed_skills()
            self.skills_updated.emit()
            self.tabs.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to import file: {e}")

    # ────────────────────────────────────────────────────────
    # Tab 4: Create New SKILL.md
    # ────────────────────────────────────────────────────────
    def create_editor_tab(self):
        tab = QWidget()
        lay = QVBoxLayout(tab)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(10)

        # Header fields
        r1 = QHBoxLayout()
        r1.setSpacing(10)
        lbl_n = QLabel("Skill Name:")
        lbl_n.setProperty("class", "metric-label")
        r1.addWidget(lbl_n)
        self.new_skill_name = QLineEdit()
        self.new_skill_name.setPlaceholderText("e.g. Next.js Performance Optimizer, Rust Memory Safety")
        r1.addWidget(self.new_skill_name, stretch=2)

        lbl_c = QLabel("Category:")
        lbl_c.setProperty("class", "metric-label")
        r1.addWidget(lbl_c)
        self.new_skill_cat = QComboBox()
        self.new_skill_cat.addItems(["engineering", "security", "design", "testing", "research", "architecture", "custom"])
        r1.addWidget(self.new_skill_cat, stretch=1)
        lay.addLayout(r1)

        lbl_trig = QLabel("Trigger Keywords (comma-separated):")
        lbl_trig.setProperty("class", "metric-label")
        lay.addWidget(lbl_trig)
        self.new_skill_triggers = QLineEdit()
        self.new_skill_triggers.setPlaceholderText("e.g. nextjs, react, server components, bundle size")
        lay.addWidget(self.new_skill_triggers)

        lbl_body = QLabel("Skill Markdown Instructions & Rules:")
        lbl_body.setProperty("class", "metric-label")
        lay.addWidget(lbl_body)
        self.new_skill_body = QTextEdit()
        self.new_skill_body.setPlaceholderText(
            "# Skill Name\n\n"
            "## Objective\n"
            "Define the core mission...\n\n"
            "## Critical Rules\n"
            "- Enforce rule 1...\n"
            "- Enforce rule 2...\n\n"
            "## Code Deliverables\n"
            "Provide template deliverables..."
        )
        lay.addWidget(self.new_skill_body, stretch=1)

        btn_create = QPushButton("Save New Skill to skills/ folder")
        btn_create.setProperty("class", "btn-primary")
        btn_create.setFixedHeight(38)
        btn_create.clicked.connect(self.on_create_new_skill)
        lay.addWidget(btn_create)
        return tab

    def on_create_new_skill(self):
        name = self.new_skill_name.text().strip()
        body = self.new_skill_body.toPlainText().strip()
        cat = self.new_skill_cat.currentText()
        triggers = self.new_skill_triggers.text().strip()

        if not name or not body:
            QMessageBox.warning(self, "Missing Fields", "Please provide a Skill Name and Markdown Instructions.")
            return

        # Build clean frontmatter
        frontmatter = (
            f"---\n"
            f"name: {name}\n"
            f"category: {cat}\n"
            f"triggers: [{triggers}]\n"
            f"---\n\n"
        )
        full_content = frontmatter + body

        try:
            skill = skills_manager.import_from_markdown_text(name, full_content, category=cat)
            QMessageBox.information(self, "Skill Created", f"Successfully saved '{skill.get('name')}' in skills/!")
            self.new_skill_name.clear()
            self.new_skill_triggers.clear()
            self.new_skill_body.clear()
            self.refresh_installed_skills()
            self.skills_updated.emit()
            self.tabs.setCurrentIndex(0)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create skill: {e}")
