"""
gui/widgets/custom_popup.py - Premium Glassmorphic Modal Popups & Alert Dialogs
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGraphicsDropShadowEffect, QWidget
)
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QColor, QFont, QCursor


class CustomPopup(QDialog):
    """
    State-of-the-art Glassmorphic Modal Dialog for Alerts, Success, Warnings & Confirmations.
    """

    def __init__(
        self,
        title: str,
        message: str,
        dialog_type: str = "info",
        details: str = "",
        buttons: list = None,
        parent=None
    ):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumWidth(440)
        self.setMaximumWidth(520)

        self._drag_pos = QPoint()
        self.result_button = None

        self.title_text = title
        self.message_text = message
        self.dialog_type = dialog_type  # "success", "error", "warning", "info", "confirm"
        self.details_text = details
        self.buttons = buttons or [{"text": "OK", "role": "accept", "primary": True}]

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Card container with glassmorphism & glow
        self.card = QFrame()
        
        type_colors = {
            "success": {"glow": "rgba(16, 185, 129, 0.5)", "border": "#10b981", "accent": "#34d399", "icon": "✅", "badge": "SUCCESS"},
            "error": {"glow": "rgba(239, 68, 68, 0.5)", "border": "#ef4444", "accent": "#f87171", "icon": "❌", "badge": "ERROR"},
            "warning": {"glow": "rgba(245, 158, 11, 0.5)", "border": "#f59e0b", "accent": "#fbbf24", "icon": "⚠️", "badge": "WARNING"},
            "info": {"glow": "rgba(56, 189, 248, 0.5)", "border": "#38bdf8", "accent": "#38bdf8", "icon": "✨", "badge": "INFO"},
            "confirm": {"glow": "rgba(129, 140, 248, 0.5)", "border": "#818cf8", "accent": "#a5b4fc", "icon": "❓", "badge": "CONFIRM"},
        }
        cfg = type_colors.get(self.dialog_type, type_colors["info"])

        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: #0b0f19;
                border: 1px solid {cfg['border']};
                border-radius: 14px;
            }}
        """)

        # Drop Shadow Effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(36)
        shadow.setColor(QColor(0, 0, 0, 190))
        shadow.setOffset(0, 8)
        self.card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(20, 18, 20, 20)
        card_layout.setSpacing(14)

        # ── Header Bar ──
        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        # Icon & Badge
        icon_lbl = QLabel(cfg["icon"])
        icon_lbl.setStyleSheet("font-size: 20px; background: transparent; border: none;")
        header_row.addWidget(icon_lbl)

        title_lbl = QLabel(self.title_text)
        title_lbl.setStyleSheet(f"""
            font-size: 15px;
            font-weight: 800;
            color: {cfg['accent']};
            letter-spacing: 0.5px;
            background: transparent;
            border: none;
        """)
        header_row.addWidget(title_lbl, stretch=1)

        badge_lbl = QLabel(cfg["badge"])
        badge_lbl.setStyleSheet(f"""
            background-color: rgba(15, 23, 42, 0.8);
            color: {cfg['accent']};
            border: 1px solid {cfg['border']};
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 800;
        """)
        header_row.addWidget(badge_lbl)

        # Close Button
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(24, 24)
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #64748b;
                font-size: 14px;
                font-weight: 700;
                border-radius: 12px;
            }
            QPushButton:hover {
                background: rgba(239, 68, 68, 0.2);
                color: #ef4444;
            }
        """)
        btn_close.clicked.connect(self.reject)
        header_row.addWidget(btn_close)

        card_layout.addLayout(header_row)

        # Subtle Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: rgba(255, 255, 255, 0.08); border: none; height: 1px;")
        card_layout.addWidget(sep)

        # ── Message Content ──
        msg_lbl = QLabel(self.message_text)
        msg_lbl.setWordWrap(True)
        msg_lbl.setTextFormat(Qt.RichText)
        msg_lbl.setStyleSheet("""
            font-size: 13.5px;
            color: #f1f5f9;
            line-height: 1.5;
            background: transparent;
            border: none;
            padding: 2px 0px;
        """)
        card_layout.addWidget(msg_lbl)

        # Optional Details Box
        if self.details_text:
            details_box = QFrame()
            details_box.setStyleSheet("""
                QFrame {
                    background-color: rgba(15, 23, 42, 0.7);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 8px;
                    padding: 8px 12px;
                }
            """)
            d_lay = QVBoxLayout(details_box)
            d_lay.setContentsMargins(6, 6, 6, 6)
            d_lbl = QLabel(self.details_text)
            d_lbl.setWordWrap(True)
            d_lbl.setStyleSheet("font-size: 12px; color: #94a3b8; font-family: monospace; background: transparent; border: none;")
            d_lay.addWidget(d_lbl)
            card_layout.addWidget(details_box)

        # ── Action Buttons ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        for b in self.buttons:
            text = b.get("text", "OK")
            is_primary = b.get("primary", False)
            role = b.get("role", "accept")

            btn = QPushButton(text)
            btn.setFixedHeight(36)
            btn.setMinimumWidth(100)
            btn.setCursor(QCursor(Qt.PointingHandCursor))

            if is_primary:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {cfg['border']}, stop:1 #2563eb);
                        color: #ffffff;
                        border: 1px solid {cfg['border']};
                        border-radius: 8px;
                        font-weight: 700;
                        font-size: 13px;
                        padding: 0 16px;
                    }}
                    QPushButton:hover {{
                        background: {cfg['border']};
                        box-shadow: 0 0 15px {cfg['glow']};
                    }}
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {{
                        background: rgba(15, 23, 42, 0.8);
                        color: #cbd5e1;
                        border: 1px solid rgba(255, 255, 255, 0.15);
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 13px;
                        padding: 0 16px;
                    }}
                    QPushButton:hover {{
                        background: rgba(30, 41, 59, 0.9);
                        color: #f8fafc;
                        border-color: rgba(255, 255, 255, 0.3);
                    }}
                """)

            if role == "accept":
                btn.clicked.connect(lambda _, b_text=text: self.on_button_clicked(b_text, True))
            else:
                btn.clicked.connect(lambda _, b_text=text: self.on_button_clicked(b_text, False))

            btn_row.addWidget(btn)

        card_layout.addLayout(btn_row)
        main_layout.addWidget(self.card)

    def on_button_clicked(self, btn_text: str, is_accept: bool):
        self.result_button = btn_text
        if is_accept:
            self.accept()
        else:
            self.reject()

    # Enable window dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    @staticmethod
    def show_success(parent, title: str, message: str, details: str = "") -> bool:
        dlg = CustomPopup(title, message, dialog_type="success", details=details, buttons=[{"text": "✨ Got It", "role": "accept", "primary": True}], parent=parent)
        return dlg.exec_() == QDialog.Accepted

    @staticmethod
    def show_error(parent, title: str, message: str, details: str = "") -> bool:
        dlg = CustomPopup(title, message, dialog_type="error", details=details, buttons=[{"text": "Dismiss", "role": "accept", "primary": True}], parent=parent)
        return dlg.exec_() == QDialog.Accepted

    @staticmethod
    def show_warning(parent, title: str, message: str, details: str = "") -> bool:
        dlg = CustomPopup(title, message, dialog_type="warning", details=details, buttons=[{"text": "OK", "role": "accept", "primary": True}], parent=parent)
        return dlg.exec_() == QDialog.Accepted

    @staticmethod
    def show_info(parent, title: str, message: str, details: str = "") -> bool:
        dlg = CustomPopup(title, message, dialog_type="info", details=details, buttons=[{"text": "OK", "role": "accept", "primary": True}], parent=parent)
        return dlg.exec_() == QDialog.Accepted

    @staticmethod
    def confirm(parent, title: str, message: str, ok_text: str = "Confirm", cancel_text: str = "Cancel") -> bool:
        dlg = CustomPopup(
            title,
            message,
            dialog_type="confirm",
            buttons=[
                {"text": cancel_text, "role": "reject", "primary": False},
                {"text": ok_text, "role": "accept", "primary": True},
            ],
            parent=parent
        )
        return dlg.exec_() == QDialog.Accepted
