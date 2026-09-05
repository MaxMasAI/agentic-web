"""
gui/widgets/lightbox.py - Full-Resolution Image Lightbox Dialog
"""

import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QImage, QPainter


class LightboxDialog(QDialog):
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setWindowTitle(f"Screenshot Inspector - {os.path.basename(image_path)}")
        self.setMinimumSize(850, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #080b11;
                color: #f8fafc;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Bar
        header = QHBoxLayout()
        title = QLabel(f"🖼️ {os.path.basename(self.image_path)}")
        title.setStyleSheet("font-size: 14px; font-weight: 700; color: #38bdf8;")
        header.addWidget(title)
        header.addStretch()

        save_btn = QPushButton("💾 Save Image")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(56, 189, 248, 0.15);
                color: #38bdf8;
                border: 1px solid #38bdf8;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(56, 189, 248, 0.3);
            }
        """)
        save_btn.clicked.connect(self.save_image)
        header.addWidget(save_btn)

        close_btn = QPushButton("✖ Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid #ef4444;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: rgba(239, 68, 68, 0.3);
            }
        """)
        close_btn.clicked.connect(self.accept)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # Scroll Area with Image
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 8px; background: #030712; }")

        self.img_lbl = QLabel()
        self.img_lbl.setAlignment(Qt.AlignCenter)
        if os.path.exists(self.image_path):
            pix = QPixmap(self.image_path)
            self.img_lbl.setPixmap(pix)
        else:
            self.img_lbl.setText(f"Image not found at {self.image_path}")
            self.img_lbl.setStyleSheet("color: #ef4444; font-size: 14px;")

        scroll.setWidget(self.img_lbl)
        layout.addWidget(scroll)

    def save_image(self):
        if not os.path.exists(self.image_path):
            return
        dest, _ = QFileDialog.getSaveFileName(self, "Save Image", os.path.basename(self.image_path), "Images (*.png *.jpg *.jpeg *.webp)")
        if dest:
            pix = QPixmap(self.image_path)
            pix.save(dest)
