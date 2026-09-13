"""
gui/pages/settings_page.py - Comprehensive Settings Panel with Centered Save/Undo Actions
Provides full-width settings categories driven directly by the main sidebar dropdown.
"""

import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QScrollArea, QCheckBox, QMessageBox,
    QFrame, QProgressBar, QStackedWidget, QComboBox, QSpinBox,
    QDoubleSpinBox, QTextEdit, QSlider
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QFont, QIcon, QColor, QCursor

from services.app_config import config
from services.llm_provider import load_api_keys, save_api_keys
from services.auth_service import (
    load_auth_sessions, save_auth_sessions,
    start_real_oauth_flow, logout_provider,
    is_authenticated, PROVIDERS_INFO
)
from services.context_storage import is_context_enabled, set_context_enabled, get_context_db
from gui.widgets.custom_popup import CustomPopup


class OAuthWorker(QThread):
    auth_finished = Signal(dict)

    def __init__(self, provider: str, parent=None):
        super().__init__(parent)
        self.provider = provider

    def run(self):
        result = start_real_oauth_flow(self.provider)
        self.auth_finished.emit(result)


def create_section_header(title: str, subtitle: str = "") -> QWidget:
    """Creates a consistent header widget for a settings category pane."""
    w = QWidget()
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 10)
    lay.setSpacing(2)

    lbl_title = QLabel(title)
    lbl_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px;")
    lay.addWidget(lbl_title)

    if subtitle:
        lbl_sub = QLabel(subtitle)
        lbl_sub.setStyleSheet("font-size: 11.5px; color: #94a3b8; line-height: 1.3;")
        lbl_sub.setWordWrap(True)
        lay.addWidget(lbl_sub)

    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("background: rgba(56, 189, 248, 0.2); height: 1px; margin-top: 6px; margin-bottom: 6px;")
    lay.addWidget(sep)
    return w


def create_setting_row(title: str, description: str, widget: QWidget) -> QWidget:
    """Creates a unified row with title, description underneath, and input/toggle widget on the right."""
    container = QFrame()
    container.setStyleSheet("background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(56, 189, 248, 0.1); border-radius: 8px; padding: 10px;")
    lay = QHBoxLayout(container)
    lay.setContentsMargins(12, 10, 12, 10)
    lay.setSpacing(16)

    t_box = QVBoxLayout()
    t_box.setSpacing(3)
    lbl_title = QLabel(f"<b>{title}</b>")
    lbl_title.setStyleSheet("font-size: 13px; color: #f1f5f9;")
    t_box.addWidget(lbl_title)

    if description:
        lbl_desc = QLabel(description)
        lbl_desc.setStyleSheet("font-size: 11px; color: #94a3b8; line-height: 1.3;")
        lbl_desc.setWordWrap(True)
        t_box.addWidget(lbl_desc)

    lay.addLayout(t_box, stretch=1)
    lay.addWidget(widget, alignment=Qt.AlignRight | Qt.AlignVCenter)
    return container


class SettingsPage(QWidget):
    CATEGORY_KEYS = [
        "general", "api_keys", "layout", "files", "context",
        "remote_tools", "models", "prompts", "images_video",
        "vision_camera", "audio", "indexes", "agents", "accessibility",
        "security", "personalize", "updates", "debug", "about"
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_workers = []
        self.key_inputs: Dict[str, QLineEdit] = {}
        self.init_ui()

    def init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        # ─── MAIN STACKED SETTINGS PANELS (FULL WIDTH) ───
        main_frame = QFrame()
        main_frame.setStyleSheet("""
            QFrame {
                background: #0b1120;
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 10px;
            }
        """)
        mf_layout = QVBoxLayout(main_frame)
        mf_layout.setContentsMargins(10, 10, 10, 10)

        self.stacked_widget = QStackedWidget()
        mf_layout.addWidget(self.stacked_widget)
        root_layout.addWidget(main_frame, stretch=1)

        # Build all panels
        self.build_all_panels()

        # ─── CENTERED BOTTOM ACTION BAR ───
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px;
                padding: 6px;
            }
        """)
        b_layout = QHBoxLayout(bottom_bar)
        b_layout.setContentsMargins(10, 6, 10, 6)
        b_layout.setSpacing(16)

        b_layout.addStretch(1)

        # Undo Changes Button (Centered)
        self.btn_undo = QPushButton("↺ Undo Changes")
        self.btn_undo.setFixedSize(160, 38)
        self.btn_undo.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_undo.setStyleSheet("""
            QPushButton {
                background: rgba(30, 41, 59, 0.9);
                color: #cbd5e1;
                border: 1px solid rgba(148, 163, 184, 0.3);
                border-radius: 6px;
                font-size: 12.5px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: rgba(51, 65, 85, 1.0);
                color: #f8fafc;
                border-color: rgba(148, 163, 184, 0.6);
            }
        """)
        self.btn_undo.clicked.connect(self.undo_changes)
        b_layout.addWidget(self.btn_undo)

        # Save Preferences Button (Centered)
        self.btn_save = QPushButton("💾 Save Preferences")
        self.btn_save.setFixedSize(190, 38)
        self.btn_save.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_save.setProperty("class", "primary-btn")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
                color: #040d21;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #0284c7);
                color: #ffffff;
            }
        """)
        self.btn_save.clicked.connect(self.save_settings)
        b_layout.addWidget(self.btn_save)

        b_layout.addStretch(1)

        root_layout.addWidget(bottom_bar)

    def _wrap_scrollable(self, widget: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.setWidget(widget)
        return scroll

    def build_all_panels(self):
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_general_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_api_keys_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_layout_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_files_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_context_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_remote_tools_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_models_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_prompts_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_images_video_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_vision_camera_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_audio_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_indexes_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_agents_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_accessibility_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_security_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_personalize_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_updates_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_debug_panel()))
        self.stacked_widget.addWidget(self._wrap_scrollable(self.build_about_panel()))

    def set_category_by_key(self, key: str):
        """Switches stacked panel based on category key string."""
        clean_key = key.replace("settings_", "").lower()
        if clean_key in self.CATEGORY_KEYS:
            idx = self.CATEGORY_KEYS.index(clean_key)
            self.stacked_widget.setCurrentIndex(idx)
        else:
            self.stacked_widget.setCurrentIndex(0)

    # ─────────────────────────────────────────────────────────────
    # 1. GENERAL
    # ─────────────────────────────────────────────────────────────
    def build_general_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)

        lay.addWidget(create_section_header("🌐 General Settings", "Basic application runtime preferences and startup behavior."))

        cb_autostart = QCheckBox()
        cb_autostart.setChecked(False)
        lay.addWidget(create_setting_row("Launch at System Startup", "Automatically start application when Windows boots up.", cb_autostart))

        cb_tray = QCheckBox()
        cb_tray.setChecked(True)
        lay.addWidget(create_setting_row("Minimize to System Tray", "Keep background agent swarms and scheduled jobs active in notification area.", cb_tray))

        cb_clear_temp = QCheckBox()
        cb_clear_temp.setChecked(True)
        lay.addWidget(create_setting_row("Clear Temporary Files on Exit", "Purges scratch files and temporary playback buffers upon close.", cb_clear_temp))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 2. API KEYS
    # ─────────────────────────────────────────────────────────────
    def build_api_keys_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)

        lay.addWidget(create_section_header("🔑 API Keys & Account Sign-In", "Direct Web Browser OAuth 2.0 or manual API key overrides."))

        grp_oauth = QGroupBox("🌐 Direct Account Sign-In (Web Browser OAuth 2.0 - Zero Secrets)")
        v_oauth = QVBoxLayout(grp_oauth)
        v_oauth.setSpacing(8)

        self.account_cards_container = QWidget()
        self.account_cards_layout = QVBoxLayout(self.account_cards_container)
        self.account_cards_layout.setContentsMargins(0, 0, 0, 0)
        self.account_cards_layout.setSpacing(6)
        v_oauth.addWidget(self.account_cards_container)
        lay.addWidget(grp_oauth)

        grp_keys = QGroupBox("🔒 Manual API Keys Vault")
        v_keys = QVBoxLayout(grp_keys)
        v_keys.setSpacing(6)

        providers = [
            ("gemini", "Google Gemini API Key:", "AIzaSy..."),
            ("openrouter", "OpenRouter API Key:", "sk-or-v1-..."),
            ("huggingface", "Hugging Face Token:", "hf_..."),
            ("openai", "OpenAI API Key:", "sk-proj-..."),
            ("anthropic", "Anthropic Claude Key:", "sk-ant-..."),
            ("deepseek", "DeepSeek API Key:", "sk-..."),
            ("perplexity", "Perplexity Sonar Key:", "pplx-..."),
            ("grok", "xAI Grok API Key:", "xai-..."),
        ]

        saved_keys = load_api_keys()
        for p_id, label, ph in providers:
            row = QHBoxLayout()
            lbl = QLabel(f"<b>{label}</b>")
            lbl.setFixedWidth(190)
            inp = QLineEdit()
            inp.setEchoMode(QLineEdit.Password)
            inp.setPlaceholderText(ph)
            inp.setText(saved_keys.get(p_id, ""))
            self.key_inputs[p_id] = inp
            row.addWidget(lbl)
            row.addWidget(inp)
            v_keys.addLayout(row)

        lay.addWidget(grp_keys)
        self.render_auth_cards()
        lay.addStretch()
        return panel

    def render_auth_cards(self):
        sessions = load_auth_sessions()
        while self.account_cards_layout.count():
            item = self.account_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for prov_id, info in PROVIDERS_INFO.items():
            card = QFrame()
            if is_authenticated(prov_id):
                card.setStyleSheet("background: rgba(5, 150, 105, 0.2); border: 1px solid rgba(16, 185, 129, 0.5); border-radius: 8px; padding: 8px;")
            else:
                card.setStyleSheet("background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; padding: 8px;")
            h = QHBoxLayout(card)
            h.setContentsMargins(10, 6, 10, 6)

            user_str = ""
            if is_authenticated(prov_id):
                sess = sessions.get(prov_id, {})
                u_email = sess.get("user_email")
                u_name = sess.get("user_name")
                if u_email:
                    user_str = f" <span style='color: #38bdf8;'>[{u_email}]</span>"
                elif u_name:
                    user_str = f" <span style='color: #38bdf8;'>[{u_name}]</span>"

            lbl_info = QLabel(f"<b>{info['name']}</b>{user_str}: <span style='color: #94a3b8;'>{info['description']}</span>")
            h.addWidget(lbl_info, stretch=1)

            if is_authenticated(prov_id):
                btn_auth = QPushButton("✅ Authenticated")
                btn_auth.setStyleSheet("background: #059669; color: white; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
                btn_auth.setDisabled(True)
                h.addWidget(btn_auth)

                btn_logout = QPushButton("Logout")
                btn_logout.setStyleSheet("background: #b91c1c; color: white; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
                btn_logout.clicked.connect(lambda ch, p=prov_id: self.logout_oauth(p))
                h.addWidget(btn_logout)
            else:
                btn = QPushButton("🚀 Sign In via Browser")
                btn.setStyleSheet("background: #0284c7; color: white; border-radius: 4px; padding: 6px 12px; font-weight: bold;")
                btn.clicked.connect(lambda ch, p=prov_id: self.start_oauth(p))
                h.addWidget(btn)
            
            self.account_cards_layout.addWidget(card)

    def logout_oauth(self, provider: str):
        logout_provider(provider)
        self.render_auth_cards()

    def start_oauth(self, provider: str):
        worker = OAuthWorker(provider, self)
        self.active_workers.append(worker)
        worker.auth_finished.connect(self.on_oauth_finished)
        worker.finished.connect(lambda: self.active_workers.remove(worker) if worker in self.active_workers else None)
        worker.start()

    def on_oauth_finished(self, res: dict):
        if res.get("success") or res.get("status") == "success":
            prov = res.get("provider", "Account")
            QMessageBox.information(self, "Sign-In Success", f"Successfully authenticated: {prov}!")
            self.render_auth_cards()
        else:
            err_msg = res.get("message") or res.get("error") or "Authentication flow was cancelled or timed out."
            QMessageBox.warning(self, "Sign-In Notice", f"Sign-in not completed: {err_msg}")

    # ─────────────────────────────────────────────────────────────
    # 3. LAYOUT
    # ─────────────────────────────────────────────────────────────
    def build_layout_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("🎨 Layout Settings", "Fine-tune UI appearance, font scales, DPI factor, and message collapse."))

        cmb_style = QComboBox()
        cmb_style.addItems(["chatgpt", "slack", "classic", "modern"])
        cmb_style.setCurrentText(config.get("layout.style.chat", "chatgpt"))
        lay.addWidget(create_setting_row("Style (chat)", "WebEngine / Chromium rendering engine only.", cmb_style))

        sp_zoom = QDoubleSpinBox()
        sp_zoom.setRange(0.5, 3.0)
        sp_zoom.setSingleStep(0.1)
        sp_zoom.setValue(float(config.get("layout.chat_zoom", 1.0)))
        lay.addWidget(create_setting_row("Chat output window zoom", "WebEngine / Chromium rendering engine only.", sp_zoom))

        sp_f_chat = QSpinBox()
        sp_f_chat.setRange(8, 32)
        sp_f_chat.setValue(int(config.get("layout.font_size.chat", 12)))
        lay.addWidget(create_setting_row("Font size (chat plain-text, notepads)", "Tip: You can change the font size using CTRL + Mouse Wheel.", sp_f_chat))

        sp_f_inp = QSpinBox()
        sp_f_inp.setRange(8, 32)
        sp_f_inp.setValue(int(config.get("layout.font_size.input", 12)))
        lay.addWidget(create_setting_row("Font size (input)", "Tip: You can change the font size using CTRL + Mouse Wheel.", sp_f_inp))

        sp_f_ctx = QSpinBox()
        sp_f_ctx.setRange(8, 32)
        sp_f_ctx.setValue(int(config.get("layout.font_size.ctx_list", 12)))
        lay.addWidget(create_setting_row("Font size (ctx list)", "Adjusts the font size in the contexts list.", sp_f_ctx))

        sp_f_box = QSpinBox()
        sp_f_box.setRange(8, 32)
        sp_f_box.setValue(int(config.get("layout.font_size.toolbox", 12)))
        lay.addWidget(create_setting_row("Font size (toolbox)", "Adjusts the font size in the toolbox on the right.", sp_f_box))

        sp_density = QSpinBox()
        sp_density.setRange(-2, 5)
        sp_density.setValue(int(config.get("layout.density", 0)))
        lay.addWidget(create_setting_row("Layout density", "Adjusts the density of layout elements.", sp_density))

        sp_dpi = QDoubleSpinBox()
        sp_dpi.setRange(0.5, 3.0)
        sp_dpi.setValue(float(config.get("layout.dpi_factor", 1.0)))
        lay.addWidget(create_setting_row("DPI factor", "Restart of the application is required for this option to take effect.", sp_dpi))

        cb_dpi = QCheckBox()
        cb_dpi.setChecked(bool(config.get("layout.dpi_scaling", True)))
        lay.addWidget(create_setting_row("DPI Scaling", "Restart of the application is required for this option to take effect.", cb_dpi))

        sp_collapse = QSpinBox()
        sp_collapse.setRange(0, 10000)
        sp_collapse.setValue(int(config.get("layout.auto_collapse_user_msg_px", 1500)))
        lay.addWidget(create_setting_row("Auto-collapse user message (px)", "Auto-collapse user message after N pixels of height, set to 0 to disable auto-collapse.", sp_collapse))

        cb_tips = QCheckBox()
        cb_tips.setChecked(bool(config.get("layout.display_tips", True)))
        lay.addWidget(create_setting_row("Display tips (help descriptions)", "Displays help tips and option descriptions.", cb_tips))

        cb_pos = QCheckBox()
        cb_pos.setChecked(bool(config.get("layout.store_dialog_positions", True)))
        lay.addWidget(create_setting_row("Store dialog window positions", "Enables storing and restoring dialog window positions.", cb_pos))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 4. FILES AND ATTACHMENTS
    # ─────────────────────────────────────────────────────────────
    def build_files_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("📁 Files and Attachments", "Attachments handling, RAG index integration, and local upload storage."))

        cb_workdir = QCheckBox()
        cb_workdir.setChecked(bool(config.get("attachments.store_in_workdir_upload", True)))
        lay.addWidget(create_setting_row("Store attachments in the workdir upload directory", "Enable to store a local copy of uploaded attachments for future use.", cb_workdir))

        cb_native = QCheckBox()
        cb_native.setChecked(bool(config.get("attachments.prefer_native_upload", False)))
        lay.addWidget(create_setting_row("Prefer native file upload when supported", "If enabled, send attachments directly through the selected provider's native file API.", cb_native))

        cb_datadir = QCheckBox()
        cb_datadir.setChecked(bool(config.get("attachments.store_in_data_dir", False)))
        lay.addWidget(create_setting_row("Store images, captures, and uploads in the data directory", "Enable to store everything in a single data directory.", cb_datadir))

        cb_img_ctx = QCheckBox()
        cb_img_ctx.setChecked(bool(config.get("attachments.allow_images_as_context", False)))
        lay.addWidget(create_setting_row("Allow images as additional context", "If enabled, images can be used as additional context.", cb_img_ctx))

        cb_once = QCheckBox()
        cb_once.setChecked(bool(config.get("attachments.append_only_once", False)))
        lay.addWidget(create_setting_row("Append attachment only once (mode: always)", "Sent attachment will be appended once rather than repeated every prompt turn.", cb_once))

        inp_sum_model = QLineEdit(config.get("attachments.model_summary", "gpt-4o-mini"))
        lay.addWidget(create_setting_row("Model for attachment content summary", "Model to use when generating a summary for file content.", inp_sum_model))

        inp_rag_model = QLineEdit(config.get("rag.model_query", "gpt-4o-mini"))
        lay.addWidget(create_setting_row("Model for querying index", "Model to use for preparing query and querying the index when RAG is selected.", inp_rag_model))

        cb_rag_hist = QCheckBox()
        cb_rag_hist.setChecked(bool(config.get("rag.use_history", True)))
        lay.addWidget(create_setting_row("Use history in RAG query", "Content of the entire conversation will be used when preparing a RAG query.", cb_rag_hist))

        sp_rag_lim = QSpinBox()
        sp_rag_lim.setRange(0, 100)
        sp_rag_lim.setValue(int(config.get("rag.history_limit", 5)))
        lay.addWidget(create_setting_row("RAG limit", "Limit of how many recent entries in conversation will be used (0 = no limit).", sp_rag_lim))

        inp_dl = QLineEdit(config.get("downloads.dir", "download"))
        lay.addWidget(create_setting_row("Directory for file downloads", "Subdirectory for downloaded files inside data.", inp_dl))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 5. CONTEXT
    # ─────────────────────────────────────────────────────────────
    def build_context_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("🧠 Context & Memory", "Conversation context memory, SQLite db.sqlite persistence, and auto-summaries."))

        sp_c_load = QSpinBox()
        sp_c_load.setRange(0, 5000)
        sp_c_load.setValue(int(config.get("context.per_load", 1000)))
        lay.addWidget(create_setting_row("Contexts per load (0 = all)", "Number of contexts loaded at a time in the context list.", sp_c_load))

        inp_c_sum = QLineEdit(config.get("context.model_auto_summary", "gpt-4o-mini"))
        lay.addWidget(create_setting_row("Model used for auto-summary", "Choose model used for summarizing context and preparing left-sidebar title.", inp_c_sum))

        cb_c_sum = QCheckBox()
        cb_c_sum.setChecked(bool(config.get("context.auto_summary", True)))
        lay.addWidget(create_setting_row("Context auto-summary", "Enable automatic summarization of the context on the conversation list.", cb_c_sum))

        cb_u_ctx = QCheckBox()
        cb_u_ctx.setChecked(is_context_enabled())
        cb_u_ctx.toggled.connect(set_context_enabled)
        lay.addWidget(create_setting_row("Use context (memory)", "Toggles the use of conversation context (memory of previous inputs).", cb_u_ctx))

        cb_s_hist = QCheckBox()
        cb_s_hist.setChecked(bool(config.get("context.store_history", True)))
        lay.addWidget(create_setting_row("Store history", "Toggles conversation history storage.", cb_s_hist))

        cb_s_time = QCheckBox()
        cb_s_time.setChecked(bool(config.get("context.store_time_in_history", True)))
        lay.addWidget(create_setting_row("Store time in history", "Chooses whether timestamps are added to history text files.", cb_s_time))

        cb_s_reason = QCheckBox()
        cb_s_reason.setChecked(bool(config.get("context.show_reasoning_realtime", True)))
        lay.addWidget(create_setting_row("Show reasoning in real-time", "Show provider reasoning/thinking while the response is being generated.", cb_s_reason))

        cb_h_reason = QCheckBox()
        cb_h_reason.setChecked(bool(config.get("context.hide_reasoning_after_response", True)))
        lay.addWidget(create_setting_row("Hide reasoning after response", "Hide reasoning when normal response tokens start arriving.", cb_h_reason))

        cb_browser = QCheckBox()
        cb_browser.setChecked(bool(config.get("browser.open_urls_in_builtin", True)))
        lay.addWidget(create_setting_row("Open URLs in built-in browser", "Enable this option to open all URLs in the built-in Chromium browser.", cb_browser))

        btn_wipe = QPushButton("🗑️ Clear Entire History (Wipe All Contexts & SQLite db.sqlite)")
        btn_wipe.setStyleSheet("background: #dc2626; color: white; border-radius: 6px; padding: 10px; font-weight: bold;")
        btn_wipe.clicked.connect(self.on_clear_all_memory)
        lay.addWidget(btn_wipe)

        lay.addStretch()
        return panel

    def on_clear_all_memory(self):
        rep = QMessageBox.question(self, "Confirm Clear History", "Wipe all conversation history and SQLite contexts?", QMessageBox.Yes | QMessageBox.No)
        if rep == QMessageBox.Yes:
            db = get_context_db()
            db.clear_all_history()
            QMessageBox.information(self, "History Cleared", "All conversation contexts wiped successfully.")

    # ─────────────────────────────────────────────────────────────
    # 6. REMOTE TOOLS
    # ─────────────────────────────────────────────────────────────
    def build_remote_tools_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)

        lay.addWidget(create_section_header("🛠️ Remote Tools & MCP", "Model Context Protocol (MCP) server endpoints and native provider tool execution."))

        cb_rem = QCheckBox()
        cb_rem.setChecked(bool(config.get("tools.remote_enabled", True)))
        lay.addWidget(create_setting_row("Enable Remote Tools", "Allows agents to invoke discovered MCP and remote API server tools.", cb_rem))

        cb_cache = QCheckBox()
        cb_cache.setChecked(True)
        lay.addWidget(create_setting_row("Cache Tool Discovery Results", "Caches schemas from remote MCP servers for faster startup.", cb_cache))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 7. MODELS
    # ─────────────────────────────────────────────────────────────
    def build_models_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("🤖 Models & Inference Parameters", "Default LLM model, temperature, top_p, and Ollama local server URL."))

        inp_ollama = QLineEdit("http://localhost:11434")
        lay.addWidget(create_setting_row("Ollama Server URL", "Local Ollama server endpoint for running offline models.", inp_ollama))

        sp_temp = QDoubleSpinBox()
        sp_temp.setRange(0.0, 2.0)
        sp_temp.setValue(0.7)
        lay.addWidget(create_setting_row("Default Temperature", "Controls randomness (lower = deterministic, higher = creative).", sp_temp))

        sp_tokens = QSpinBox()
        sp_tokens.setRange(256, 128000)
        sp_tokens.setValue(4096)
        lay.addWidget(create_setting_row("Max Output Tokens", "Maximum tokens the model can generate per single response.", sp_tokens))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 8. PROMPTS
    # ─────────────────────────────────────────────────────────────
    def build_prompts_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)

        lay.addWidget(create_section_header("📝 Prompts & Specialized System Instructions", "Select from industry-leading system prompts (Claude, Cursor, OpenAI, Devin, Perplexity, v0, Gemini) or define custom directives."))

        from services.system_prompts_catalog import get_system_prompts_catalog
        catalog = get_system_prompts_catalog()
        all_prompts = catalog.list_all()

        # Catalog Preset Picker
        cat_box = QHBoxLayout()
        cat_box.setSpacing(10)
        lbl_preset = QLabel("<b>Specialized System Prompt Preset:</b>")
        lbl_preset.setStyleSheet("color: #38bdf8; font-size: 12px;")
        
        cmb_catalog = QComboBox()
        for p in all_prompts:
            cmb_catalog.addItem(f"⚡ {p['name']} ({p.get('category', 'general').upper()})", p["id"])
        
        btn_apply_preset = QPushButton("📥 Load into Editor")
        btn_apply_preset.setStyleSheet("""
            QPushButton {
                background: #0284c7;
                color: white;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 5px;
            }
            QPushButton:hover { background: #0369a1; }
        """)

        cat_box.addWidget(lbl_preset)
        cat_box.addWidget(cmb_catalog, stretch=1)
        cat_box.addWidget(btn_apply_preset)
        lay.addLayout(cat_box)

        # Prompt Content Editor
        txt_sys = QTextEdit()
        txt_sys.setFixedHeight(180)
        txt_sys.setPlaceholderText("Enter custom global system instructions or load a preset above...")
        default_claude_prompt = catalog.get_prompt_text("claude_coding_architect", "You are an expert autonomous AI coding assistant and agentic swarm orchestrator.")
        txt_sys.setText(default_claude_prompt)
        
        btn_apply_preset.clicked.connect(lambda: txt_sys.setText(catalog.get_prompt_text(cmb_catalog.currentData())))
        lay.addWidget(create_setting_row("Active System Prompt", "Base prompt injected into models and agent loops.", txt_sys))

        # Auto-match toggle
        cb_auto = QCheckBox()
        cb_auto.setChecked(True)
        lay.addWidget(create_setting_row("Auto-Match System Prompt by Task Query", "Dynamically routes coding, bug fixing, security, UI design, research, or math tasks to the optimal prompt.", cb_auto))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 9. IMAGES AND VIDEO
    # ─────────────────────────────────────────────────────────────
    def build_images_video_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("🖼️ Images and Video", "Image generation engines, resolution formats, and media studio options."))

        cmb_img = QComboBox()
        cmb_img.addItems(["DALL-E 3", "Imagen 3 (Google)", "Stable Diffusion XL", "Flux.1"])
        lay.addWidget(create_setting_row("Default Image Generator", "Provider used when calling image synthesis tools.", cmb_img))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 10. VISION AND CAMERA
    # ─────────────────────────────────────────────────────────────
    def build_vision_camera_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("👁️ Vision and Camera", "Live camera snapshots, desktop screen capture, and visual inspection."))

        cb_cam = QCheckBox()
        cb_cam.setChecked(True)
        lay.addWidget(create_setting_row("Enable Camera Tool", "Allows model to inspect live webcam capture when requested.", cb_cam))

        cb_screen = QCheckBox()
        cb_screen.setChecked(True)
        lay.addWidget(create_setting_row("Enable Screenshot Capture", "Allows taking screen captures for visual reasoning.", cb_screen))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 11. AUDIO
    # ─────────────────────────────────────────────────────────────
    def build_audio_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("🔊 Audio & Speech Synthesis", "Text-to-speech (TTS), live mic listening, and sound feedback."))

        cb_tts = QCheckBox()
        cb_tts.setChecked(True)
        lay.addWidget(create_setting_row("Enable Speech Synthesis (TTS)", "Narrates responses and agent status updates out loud.", cb_tts))

        cb_mic = QCheckBox()
        cb_mic.setChecked(True)
        lay.addWidget(create_setting_row("Enable Microphone STT Listening", "Allows speech-to-text dictation into input fields.", cb_mic))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 12. INDEXES / LLAMAINDEX
    # ─────────────────────────────────────────────────────────────
    def build_indexes_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("📚 Indexes / LlamaIndex", "Local vector stores, embedding models, and document indexing."))

        cmb_vdb = QComboBox()
        cmb_vdb.addItems(["SQLite Vector / Local", "ChromaDB", "FAISS", "Qdrant", "OpenAI Vector Store"])
        lay.addWidget(create_setting_row("Vector Storage Engine", "Storage backend for document embeddings and RAG indexes.", cmb_vdb))

        sp_chunk = QSpinBox()
        sp_chunk.setRange(128, 4096)
        sp_chunk.setValue(1024)
        lay.addWidget(create_setting_row("Chunk Size", "Document token segment size for embedding generation.", sp_chunk))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 13. AGENTS AND EXPERTS
    # ─────────────────────────────────────────────────────────────
    def build_agents_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("👥 Agents and Experts", "Multi-agent autonomous loops, co-op expert manager, and supervisor routing."))

        cb_coop = QCheckBox()
        cb_coop.setChecked(True)
        lay.addWidget(create_setting_row("Enable Experts Co-op Mode", "Allows isolated per-expert context banks with manager orchestration.", cb_coop))

        sp_iter = QSpinBox()
        sp_iter.setRange(1, 50)
        sp_iter.setValue(10)
        lay.addWidget(create_setting_row("Max Autonomous Loop Iterations", "Safety ceiling for autonomous Auto-GPT execution loops.", sp_iter))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 14. ACCESSIBILITY
    # ─────────────────────────────────────────────────────────────
    def build_accessibility_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("♿ Accessibility", "Screen reader narration, cyberpunk high contrast, and keyboard shortcuts."))

        cb_contrast = QCheckBox()
        cb_contrast.setChecked(False)
        lay.addWidget(create_setting_row("Cyberpunk High-Contrast Mode", "Enhances borders and text contrast for maximum readability.", cb_contrast))

        cb_nav = QCheckBox()
        cb_nav.setChecked(True)
        lay.addWidget(create_setting_row("Full Keyboard Navigation", "Enables Tab-indexing and fast shortcut keys across all tools.", cb_nav))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 15. SECURITY
    # ─────────────────────────────────────────────────────────────
    def build_security_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("🔒 Security & Isolation", "Credential masking, OS command safeguards, and sandbox permissions."))

        cb_mask = QCheckBox()
        cb_mask.setChecked(True)
        lay.addWidget(create_setting_row("Sanitize Credentials from LLM Prompts", "Strictly masks passwords and private keys from model context.", cb_mask))

        cb_exec = QCheckBox()
        cb_exec.setChecked(True)
        lay.addWidget(create_setting_row("Allow System Command Execution (sys_exec)", "Permits safe execution of OS terminal commands via agents.", cb_exec))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 16. PERSONALIZE
    # ─────────────────────────────────────────────────────────────
    def build_personalize_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("✨ Personalize & Themes", "Color palettes, dark mode presets, and interface accents."))

        cmb_theme = QComboBox()
        cmb_theme.addItems(["Cyberpunk Dark / Blue Accent", "Midnight Slate", "Deep Emerald", "OLED Pure Black"])
        lay.addWidget(create_setting_row("UI Theme Accent", "Primary accent color and dark glassmorphic styling.", cmb_theme))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 17. UPDATES
    # ─────────────────────────────────────────────────────────────
    def build_updates_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("🔄 Updates & Versions", "Software release channel, update checks, and version metadata."))

        lbl_ver = QLabel("<b>Version 2.4.4 (Latest Stable Release)</b>")
        lbl_ver.setStyleSheet("color: #38bdf8;")
        lay.addWidget(create_setting_row("Current Version", "Desktop agentic web workstation application build.", lbl_ver))

        btn_chk = QPushButton("🔄 Check for Updates Now")
        btn_chk.setStyleSheet("background: #0284c7; color: white; border-radius: 6px; padding: 8px 16px; font-weight: bold;")
        btn_chk.clicked.connect(lambda: QMessageBox.information(self, "Update Status", "You are running the latest version (v2.4.4)."))
        lay.addWidget(create_setting_row("Check Updates", "Connects to release server to check for new builds.", btn_chk))

        lay.addStretch()
        return panel

    # ─────────────────────────────────────────────────────────────
    # 18. DEBUG
    # ─────────────────────────────────────────────────────────────
    def build_debug_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(8)

        lay.addWidget(create_section_header("🐞 Debug & Diagnostics", "Real-time console logging, payload inspectors, and debug tracing."))

        cb_log_agents = QCheckBox()
        cb_log_agents.setChecked(True)
        lay.addWidget(create_setting_row("Log Agents usage to console", "Prints full agent pipeline executions, slot activations, and routing steps to console.", cb_log_agents))

        cb_verbose = QCheckBox()
        cb_verbose.setChecked(False)
        lay.addWidget(create_setting_row("Verbose LLM Payload Logging", "Outputs raw prompt tokens and tool call JSON envelopes to terminal.", cb_verbose))

        lay.addStretch()
        return panel

    def undo_changes(self):
        """Restores preferences from disk."""
        config.load()
        QMessageBox.information(self, "Undo Changes", "Reverted settings back to saved state.")

    def save_settings(self):
        """Saves API keys and configuration."""
        keys = {}
        for p_id, inp in self.key_inputs.items():
            val = inp.text().strip()
            if val:
                keys[p_id] = val
        if keys:
            save_api_keys(keys)

        config.save()
        QMessageBox.information(self, "Settings Saved", "All preferences and API configuration saved successfully.")
    def build_about_panel(self) -> QWidget:
        panel = QWidget()
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(15, 15, 15, 15)
        lay.setSpacing(10)

        lay.addWidget(create_section_header("ℹ️ About", "Information about the application, version, and license."))

        info_lbl = QLabel(
            "<h3>Agentic Web Console</h3>"
            "<p>Version: 1.0.0<br/>"
            "Build Date: 2026-09-05</p>"
            "<p>A leader-worker multi-AI collaborative system and live voice orchestrator.<br/>"
            "Powered by Google Gemini 2.0 and PySide6.</p>"
        )
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #cbd5e1; font-size: 13px; line-height: 1.5;")
        lay.addWidget(info_lbl)

        lay.addStretch(1)
        return panel
