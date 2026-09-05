"""
gui/pages/media_studio_page.py - Image & Video Generation Studio (Imagen, DALL-E, Veo, Sora)
"""

import os
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QComboBox, QScrollArea, QFrame, QMessageBox,
    QTabWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from services.llm_provider import generate_chat_response


class MediaStudioPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🎨 IMAGE & VIDEO GENERATION STUDIO")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Visual Design & Prompt Studio: Imagen 3, DALL-E 3, Gemini Nano, Veo 3 & Sora 2")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Tabs: Image Studio vs Video Storyboard Studio
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_image_tab(), "🖼️ Image Generation Studio")
        self.tabs.addTab(self.create_video_tab(), "🎬 Video & Cinematics Studio (Veo3 / Sora2)")

        main_layout.addWidget(self.tabs, stretch=1)

    def create_image_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # Left: Prompt Form
        left_v = QVBoxLayout()
        left_v.setSpacing(10)

        left_v.addWidget(QLabel("<b>Image Prompt & Concept:</b>"))
        self.img_prompt_edit = QTextEdit()
        self.img_prompt_edit.setPlaceholderText("Describe the visual scene in detail: lighting, mood, camera angle, style...")
        self.img_prompt_edit.setFixedHeight(120)
        left_v.addWidget(self.img_prompt_edit)

        # Style & Aspect Ratio
        row_opts = QHBoxLayout()
        v_m = QVBoxLayout()
        v_m.addWidget(QLabel("<b>Model:</b>"))
        self.img_model_combo = QComboBox()
        self.img_model_combo.addItems(["Google Imagen 3", "OpenAI DALL-E 3", "Gemini 2.5 Flash Visual", "Nano Banana Studio"])
        v_m.addWidget(self.img_model_combo)
        row_opts.addLayout(v_m)

        v_s = QVBoxLayout()
        v_s.addWidget(QLabel("<b>Art Style:</b>"))
        self.img_style_combo = QComboBox()
        self.img_style_combo.addItems(["Photorealistic 8K", "Cyberpunk / Sci-Fi Neon", "Anime / Digital Art", "Minimalist 3D Render", "Oil Painting Masterpiece"])
        v_s.addWidget(self.img_style_combo)
        row_opts.addLayout(v_s)

        v_r = QVBoxLayout()
        v_r.addWidget(QLabel("<b>Aspect Ratio:</b>"))
        self.img_ratio_combo = QComboBox()
        self.img_ratio_combo.addItems(["16:9 (Landscape)", "1:1 (Square)", "9:16 (Portrait / Reel)", "4:3 (Classic)"])
        v_r.addWidget(self.img_ratio_combo)
        row_opts.addLayout(v_r)

        left_v.addLayout(row_opts)

        self.btn_gen_img = QPushButton("✨ Synthesize Visual Image")
        self.btn_gen_img.setProperty("class", "primary-btn")
        self.btn_gen_img.setFixedHeight(42)
        self.btn_gen_img.clicked.connect(self.generate_image)
        left_v.addWidget(self.btn_gen_img)

        left_v.addStretch()
        layout.addLayout(left_v, stretch=1)

        # Right: Image Preview Box
        right_v = QVBoxLayout()
        right_v.addWidget(QLabel("<b>🖼️ Generated Deliverable Preview:</b>"))

        self.img_preview_lbl = QLabel("No image generated yet.\nEnter a prompt and click 'Synthesize Visual Image'.")
        self.img_preview_lbl.setAlignment(Qt.AlignCenter)
        self.img_preview_lbl.setStyleSheet("""
            background: #030712;
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 10px;
            color: #64748b;
            font-size: 13px;
        """)
        right_v.addWidget(self.img_preview_lbl, stretch=1)

        layout.addLayout(right_v, stretch=1)
        return tab

    def create_video_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(QLabel("<b>Cinematic Video Concept & Storyboard Prompt (Veo3 / Sora2):</b>"))
        self.video_prompt_edit = QTextEdit()
        self.video_prompt_edit.setPlaceholderText("Describe the video scene, camera motion (drone sweep, pan, zoom), lighting, duration, and physics...")
        self.video_prompt_edit.setFixedHeight(100)
        layout.addWidget(self.video_prompt_edit)

        self.btn_gen_storyboard = QPushButton("🎬 Generate Cinematic Storyboard & Prompt Specification")
        self.btn_gen_storyboard.setProperty("class", "primary-btn")
        self.btn_gen_storyboard.clicked.connect(self.generate_storyboard)
        layout.addWidget(self.btn_gen_storyboard)

        layout.addWidget(QLabel("<b>Generated Cinematic Storyboard & Camera Cue Directives:</b>"))
        self.storyboard_viewer = QTextEdit()
        self.storyboard_viewer.setReadOnly(True)
        self.storyboard_viewer.setStyleSheet("background: #030712; color: #4ade80; font-family: monospace; font-size: 12px; border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px;")
        layout.addWidget(self.storyboard_viewer, stretch=1)

        return tab

    def generate_image(self):
        prompt = self.img_prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "Missing Prompt", "Please enter an image prompt description.")
            return

        style = self.img_style_combo.currentText()
        ratio = self.img_ratio_combo.currentText()
        model = self.img_model_combo.currentText()

        self.img_preview_lbl.setText(f"🎨 Generating image with {model} ({style} · {ratio})...\nConnecting to generative pipeline...")

    def generate_storyboard(self):
        prompt = self.video_prompt_edit.toPlainText().strip()
        if not prompt:
            return

        self.storyboard_viewer.setPlainText("Synthesizing cinematic scene breakdown...")

        system_prompt = (
            "You are a professional Hollywood cinematography director and AI video prompt engineer. "
            "Break down the user's video concept into a production-ready Veo3 / Sora2 specification: "
            "1. Shot 1 (Opening Shot & Camera Motion)\n"
            "2. Shot 2 (Core Action & Lighting)\n"
            "3. Shot 3 (Climax & Focus)\n"
            "4. Negative Prompt & Physics Directives."
        )

        resp = generate_chat_response(
            [{"role": "user", "content": prompt}],
            model_id="gemini-2.5-flash",
            system_prompt=system_prompt
        )

        self.storyboard_viewer.setPlainText(resp.get("content", ""))

    def attach_sketch(self, sketch_path: str):
        if os.path.exists(sketch_path):
            pix = QPixmap(sketch_path).scaled(400, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_preview_lbl.setPixmap(pix)
            self.tabs.setCurrentIndex(0)
