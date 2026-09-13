"""
plugins/plugin_installer.py - Git Repository Plugin Cloner, Validator & Installer
Handles background Git cloning, manifest verification, and direct registration into AgenticWeb.
"""

import os
import re
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QFrame,
    QMessageBox,
    QWidget,
)

from core.plugin_base import get_plugin_manager, PluginManager


class GitCloneWorker(QThread):
    """
    Background worker thread handling Git clone, manifest validation,
    and filesystem isolation without freezing the Qt GUI thread.
    """
    progress = Signal(str)
    success = Signal(dict)
    error = Signal(str)

    REQUIRED_MANIFEST_FIELDS = {"id", "name", "version", "description", "entrypoint"}

    def __init__(
        self,
        git_url: str,
        branch: str,
        plugins_dir: Path,
        plugin_manager: PluginManager,
        overwrite: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.git_url = git_url.strip()
        self.branch = branch.strip() or "main"
        self.plugins_dir = Path(plugins_dir)
        self.plugin_manager = plugin_manager
        self.overwrite = overwrite
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        temp_dir: Optional[str] = None
        try:
            # 1. Check Git CLI Availability
            self.progress.emit("Checking git executable on system PATH...")
            if not shutil.which("git"):
                self.error.emit(
                    "Git executable was not found on your system PATH.\n"
                    "Please install Git (https://git-scm.com/) and verify 'git --version' works."
                )
                return

            # 2. URL Sanitization
            if not self._is_valid_git_url(self.git_url):
                self.error.emit(
                    f"Invalid or unsupported Git URL format:\n'{self.git_url}'\n\n"
                    "Supported formats:\n"
                    "• https://github.com/user/repo.git\n"
                    "• https://gitlab.com/user/repo\n"
                    "• git@github.com:user/repo.git"
                )
                return

            # 3. Create Temporary Working Directory
            temp_dir = tempfile.mkdtemp(prefix="agentic_plugin_clone_")
            self.progress.emit(f"Cloning repository (branch: {self.branch})...")

            # 4. Clone repository via subprocess without shell=True
            clone_cmd = [
                "git",
                "clone",
                "--depth", "1",
                "--branch", self.branch,
                "--single-branch",
                self.git_url,
                temp_dir,
            ]

            process = subprocess.run(
                clone_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
                check=False,
                shell=False,
            )

            if process.returncode != 0:
                err_msg = process.stderr.strip() or "Unknown Git clone error."
                self.error.emit(f"Git Clone Failed:\n{err_msg}")
                return

            if self._is_cancelled:
                self.error.emit("Installation was cancelled by the user.")
                return

            # 5. Validate plugin.json Manifest
            self.progress.emit("Validating plugin.json manifest...")
            manifest_path = Path(temp_dir) / "plugin.json"
            if not manifest_path.is_file():
                self.error.emit(
                    "Missing 'plugin.json' manifest in the repository root directory.\n"
                    "Every compatible plugin repository must include a root 'plugin.json'."
                )
                return

            import json
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest: Dict[str, Any] = json.load(f)
            except Exception as e:
                self.error.emit(f"Malformed 'plugin.json': Unable to parse JSON.\nDetails: {e}")
                return

            missing_fields = self.REQUIRED_MANIFEST_FIELDS - set(manifest.keys())
            if missing_fields:
                self.error.emit(
                    f"Invalid 'plugin.json': Missing required field(s): {', '.join(sorted(missing_fields))}"
                )
                return

            plugin_id = re.sub(r"[^a-zA-Z0-9_\-]", "", str(manifest["id"])).strip()
            if not plugin_id:
                self.error.emit("Invalid plugin 'id' specified in manifest.")
                return

            entrypoint_rel = manifest.get("entrypoint", "plugin.py")
            entrypoint_file = Path(temp_dir) / entrypoint_rel
            if not entrypoint_file.is_file():
                self.error.emit(
                    f"Declared entrypoint '{entrypoint_rel}' was not found in the plugin repository."
                )
                return

            # 6. Collision Check
            target_plugin_dir = self.plugins_dir / plugin_id
            if target_plugin_dir.exists():
                if not self.overwrite:
                    self.error.emit(
                        f"COLLISION:{plugin_id}:{manifest.get('name', plugin_id)}"
                    )
                    return
                else:
                    self.progress.emit("Overwriting existing plugin files...")
                    shutil.rmtree(target_plugin_dir, ignore_errors=True)

            # 7. Move to Isolated Plugins Directory
            self.progress.emit("Installing plugin into agentic-web plugins folder...")
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            
            git_meta_dir = Path(temp_dir) / ".git"
            if git_meta_dir.exists():
                shutil.rmtree(git_meta_dir, ignore_errors=True)

            shutil.move(temp_dir, str(target_plugin_dir))
            temp_dir = None

            # 8. Dynamic Registration
            self.progress.emit("Registering and activating plugin in runtime registry...")
            success, message = self.plugin_manager.load_single_plugin(target_plugin_dir)
            if not success:
                self.error.emit(f"Plugin failed to initialize:\n{message}")
                return

            self.progress.emit("Plugin successfully installed and active!")
            manifest["install_path"] = str(target_plugin_dir)
            self.success.emit(manifest)

        except subprocess.TimeoutExpired:
            self.error.emit("Git clone timed out after 60 seconds. Please check your network connection.")
        except Exception as e:
            self.error.emit(f"Unexpected error during plugin installation:\n{str(e)}")
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

    @staticmethod
    def _is_valid_git_url(url: str) -> bool:
        if not url or len(url) > 500:
            return False
        patterns = [
            r"^https?://[a-zA-Z0-9.\-_~%]+(/[a-zA-Z0-9.\-_~%]+)+(\.git)?/?$",
            r"^git@[a-zA-Z0-9.\-_~]+:[a-zA-Z0-9.\-_~]+/[a-zA-Z0-9.\-_~]+(\.git)?$",
        ]
        return any(re.match(p, url) for p in patterns)


class PluginInstallerDialog(QDialog):
    """
    Modern PySide6 Dialog allowing users to input any public Git URL,
    track download & verification in real-time, and register the extension.
    """
    plugin_installed = Signal(dict)

    def __init__(self, plugin_manager: Optional[PluginManager] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager or get_plugin_manager()
        self.worker: Optional[GitCloneWorker] = None

        self.setWindowTitle("🧩 Install Plugin from Git Repository")
        self.resize(540, 310)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header Title
        header_layout = QVBoxLayout()
        header_layout.setSpacing(3)
        header_title = QLabel("<b>Install Extension from Remote Git URL</b>")
        header_title.setStyleSheet("font-size: 15px; color: #38bdf8; font-weight: bold;")
        header_sub = QLabel("Provide a public GitHub, GitLab, or HTTPS Git link with a root 'plugin.json':")
        header_sub.setStyleSheet("color: #94a3b8; font-size: 11.5px;")
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_sub)
        layout.addLayout(header_layout)

        # Git URL Input Field
        url_box = QVBoxLayout()
        url_box.setSpacing(4)
        url_lbl = QLabel("Repository URL:")
        url_lbl.setStyleSheet("font-weight: bold; font-size: 11.5px; color: #cbd5e1;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://github.com/username/my-agent-extension.git")
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 10px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
            }
        """)
        self.url_input.textChanged.connect(self._clear_error)
        url_box.addWidget(url_lbl)
        url_box.addWidget(self.url_input)
        layout.addLayout(url_box)

        # Branch / Tag Input
        branch_box = QHBoxLayout()
        branch_box.setSpacing(10)
        branch_lbl = QLabel("Branch / Tag:")
        branch_lbl.setStyleSheet("font-size: 11.5px; color: #94a3b8;")
        self.branch_input = QLineEdit("main")
        self.branch_input.setPlaceholderText("main")
        self.branch_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 5px 8px;
                font-size: 12px;
            }
        """)
        branch_box.addWidget(branch_lbl)
        branch_box.addWidget(self.branch_input)
        layout.addLayout(branch_box)

        # Error Banner
        self.error_frame = QFrame()
        self.error_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(239, 68, 68, 0.12);
                border: 1px solid #ef4444;
                border-radius: 6px;
                padding: 6px;
            }
        """)
        error_layout = QVBoxLayout(self.error_frame)
        error_layout.setContentsMargins(8, 4, 8, 4)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #fca5a5; font-size: 11px;")
        self.error_label.setWordWrap(True)
        error_layout.addWidget(self.error_label)
        self.error_frame.hide()
        layout.addWidget(self.error_frame)

        # Progress Section
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(5)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1e293b;
                border: none;
                border-radius: 2px;
            }
            QProgressBar::chunk {
                background-color: #38bdf8;
                border-radius: 2px;
            }
        """)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #38bdf8; font-size: 11.5px; font-weight: 500;")
        self.status_label.hide()
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                padding: 7px 16px;
                border-radius: 5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #334155;
                color: #f8fafc;
            }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.install_btn = QPushButton("📥 Clone & Install")
        self.install_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                padding: 7px 18px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.install_btn.clicked.connect(lambda: self._start_installation(overwrite=False))
        button_layout.addWidget(self.install_btn)

        layout.addLayout(button_layout)

    def _start_installation(self, overwrite: bool = False):
        url = self.url_input.text().strip()
        branch = self.branch_input.text().strip() or "main"

        if not url:
            self._show_error("Please enter a valid Git repository URL.")
            return

        self._clear_error()
        self._set_ui_busy(True)

        self.worker = GitCloneWorker(
            git_url=url,
            branch=branch,
            plugins_dir=self.plugin_manager.plugins_dir,
            plugin_manager=self.plugin_manager,
            overwrite=overwrite,
            parent=self,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.success.connect(self._on_success)
        self.worker.error.connect(self._on_error)
        self.worker.start()

    @Slot(str)
    def _on_progress(self, message: str):
        self.status_label.show()
        self.status_label.setText(message)

    @Slot(dict)
    def _on_success(self, manifest: dict):
        self._set_ui_busy(False)
        self.plugin_installed.emit(manifest)
        QMessageBox.information(
            self,
            "Installation Complete",
            f"Plugin '{manifest.get('name', 'Extension')}' (v{manifest.get('version', '1.0.0')}) "
            "has been successfully cloned, verified, and activated in AgenticWeb!",
        )
        self.accept()

    @Slot(str)
    def _on_error(self, message: str):
        self._set_ui_busy(False)

        if message.startswith("COLLISION:"):
            _, plugin_id, plugin_name = message.split(":", 2)
            reply = QMessageBox.question(
                self,
                "Plugin Already Exists",
                f"A plugin with ID '{plugin_id}' ({plugin_name}) is already installed.\n\n"
                "Would you like to overwrite it with this repository version?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._start_installation(overwrite=True)
            return

        self._show_error(message)

    def _show_error(self, text: str):
        self.error_label.setText(text)
        self.error_frame.show()
        self.status_label.hide()

    def _clear_error(self):
        self.error_frame.hide()
        self.error_label.setText("")

    def _set_ui_busy(self, busy: bool):
        self.url_input.setEnabled(not busy)
        self.branch_input.setEnabled(not busy)
        self.install_btn.setEnabled(not busy)
        if busy:
            self.progress_bar.show()
            self.status_label.show()
        else:
            self.progress_bar.hide()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(2000)
        super().closeEvent(event)
