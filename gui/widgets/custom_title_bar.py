"""
gui/widgets/custom_title_bar.py - Sleek Dark Sci-Fi Glassmorphism Custom Title Bar
Replaces the standard native OS caption bar with a modern, integrated top bar
featuring glowing brand identity, dynamic page breadcrumbs, live telemetry, and custom window controls.
"""

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy
)
from PySide6.QtCore import Qt, QPoint, Signal, QSize, QRectF
from PySide6.QtGui import QCursor, QFont, QColor, QIcon, QPixmap, QPainter, QPen, QBrush


def create_camera_icon(color: str = "#38bdf8", size: int = 32) -> QIcon:
    """Generates a crisp high-DPI vector camera icon."""
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)

    pen = QPen(QColor(color), 1.8)
    p.setPen(pen)

    # Camera body outline
    p.drawRoundedRect(QRectF(3, 8, size - 6, size - 12), 3, 3)

    # Viewfinder hump on top
    p.drawRoundedRect(QRectF(size * 0.32, 3.5, size * 0.36, 5.5), 1.5, 1.5)

    # Center lens
    p.drawEllipse(QRectF(size * 0.3, size * 0.42, size * 0.4, size * 0.4))

    # Flash indicator
    p.setBrush(QBrush(QColor(color)))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QRectF(size - 8, 10.5, 2.5, 2.5))

    p.end()
    return QIcon(pix)


class CustomTitleBar(QFrame):
    snapshot_requested = Signal()
    cursor_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CustomTitleBar")
        self._drag_pos = None
        self.init_ui()

    def init_ui(self):
        self.setFixedHeight(42)
        self.setStyleSheet("""
            QFrame#CustomTitleBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #060911, stop:0.35 #0b0f19, stop:0.75 #0f172a, stop:1 #060911);
                border-bottom: 1px solid rgba(56, 189, 248, 0.25);
            }
            QLabel {
                background: transparent;
                border: none;
                color: #cbd5e1;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Glowing Logo Badge
        self.logo_lbl = QLabel("⚡")
        self.logo_lbl.setAlignment(Qt.AlignCenter)
        self.logo_lbl.setStyleSheet("""
            QLabel {
                background: rgba(56, 189, 248, 0.15);
                border: 1px solid rgba(56, 189, 248, 0.45);
                border-radius: 6px;
                color: #38bdf8;
                font-size: 15px;
                font-weight: 800;
                padding: 2px 7px;
            }
        """)
        layout.addWidget(self.logo_lbl)

        # 2. Main Application Title
        self.title_lbl = QLabel("AUTONOMOUS MULTI-AGENT OS")
        self.title_lbl.setStyleSheet("""
            QLabel {
                font-size: 12px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: 0.9px;
            }
        """)
        layout.addWidget(self.title_lbl)

        # Separator Bar
        sep_lbl = QLabel("│")
        sep_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.18); font-size: 14px;")
        layout.addWidget(sep_lbl)

        # 3. Dynamic Page / Mode Breadcrumb
        self.page_lbl = QLabel("🛸 Mission Control Center")
        self.page_lbl.setStyleSheet("""
            QLabel {
                font-size: 11.5px;
                font-weight: 600;
                color: #38bdf8;
                background: rgba(56, 189, 248, 0.1);
                border: 1px solid rgba(56, 189, 248, 0.25);
                border-radius: 5px;
                padding: 3px 9px;
            }
        """)
        layout.addWidget(self.page_lbl)

        # Center Stretch (Drag Area)
        layout.addStretch(1)

        # Snapshot Button (Vector Camera Icon)
        self.btn_snapshot = QPushButton()
        self.btn_snapshot.setIcon(create_camera_icon("#38bdf8", 32))
        self.btn_snapshot.setIconSize(QSize(20, 20))
        self.btn_snapshot.setFixedSize(36, 30)
        self.btn_snapshot.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_snapshot.setToolTip("Capture Full Application Screenshots")
        self.btn_snapshot.setStyleSheet("""
            QPushButton {
                background: rgba(56, 189, 248, 0.08);
                border: 1px solid rgba(56, 189, 248, 0.28);
                border-radius: 6px;
                padding: 2px;
            }
            QPushButton:hover {
                background: rgba(56, 189, 248, 0.25);
                border-color: #38bdf8;
            }
            QPushButton:pressed {
                background: rgba(56, 189, 248, 0.4);
                border-color: #7dd3fc;
            }
        """)
        self.btn_snapshot.clicked.connect(self.snapshot_requested.emit)
        layout.addWidget(self.btn_snapshot)

        # Agent / Gemini Mouse Cursor Overlay Toggle Button
        self.btn_cursor = QPushButton("✨ Gemini Cursor")
        self.btn_cursor.setCheckable(True)
        self.btn_cursor.setChecked(False)
        self.btn_cursor.setFixedHeight(30)
        self.btn_cursor.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_cursor.setToolTip("Gemini Cursor: Master Leader visual cursor overlay (Click to toggle always ON)")
        self.btn_cursor.setStyleSheet("""
            QPushButton {
                background: rgba(124, 58, 237, 0.12);
                border: 1px solid rgba(124, 58, 237, 0.35);
                border-radius: 6px;
                color: #c4b5fd;
                font-size: 11px;
                font-weight: 700;
                padding: 2px 8px;
            }
            QPushButton:hover {
                background: rgba(124, 58, 237, 0.25);
                border-color: #a78bfa;
                color: #ffffff;
            }
            QPushButton:checked {
                background: rgba(124, 58, 237, 0.45);
                border-color: #a78bfa;
                color: #ffffff;
            }
        """)
        self.btn_cursor.toggled.connect(self.cursor_toggled.emit)
        layout.addWidget(self.btn_cursor)

        # 5. Native Windows-Style Caption Controls (Flush 0-margin right corner)
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(0)

        caption_btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
                color: #cccccc;
                font-family: 'Segoe UI', 'Segoe UI Symbol', 'Lucida Sans Unicode', Arial, sans-serif;
                font-size: 14px;
                font-weight: 400;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                color: #ffffff;
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.22);
                color: #ffffff;
            }
        """

        close_btn_style = """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 0px;
                color: #cccccc;
                font-family: 'Segoe UI', 'Segoe UI Symbol', 'Lucida Sans Unicode', Arial, sans-serif;
                font-size: 15px;
                font-weight: 400;
            }
            QPushButton:hover {
                background: #e81123;
                color: #ffffff;
            }
            QPushButton:pressed {
                background: #c4101e;
                color: #ffffff;
            }
        """

        self.btn_min = QPushButton("―")
        self.btn_min.setFixedSize(46, 42)
        self.btn_min.setToolTip("Minimize")
        self.btn_min.setStyleSheet(caption_btn_style + "QPushButton { font-size: 17px; font-weight: 700; }")
        self.btn_min.clicked.connect(self.minimize_window)
        controls_layout.addWidget(self.btn_min)

        self.btn_max = QPushButton("□")
        self.btn_max.setFixedSize(46, 42)
        self.btn_max.setToolTip("Maximize")
        self.btn_max.setStyleSheet(caption_btn_style + "QPushButton { font-size: 15px; font-weight: 600; }")
        self.btn_max.clicked.connect(self.toggle_maximize_window)
        controls_layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(46, 42)
        self.btn_close.setToolTip("Close")
        self.btn_close.setStyleSheet(close_btn_style)
        self.btn_close.clicked.connect(self.close_window)
        controls_layout.addWidget(self.btn_close)

        layout.addWidget(controls_widget)

    def set_page_title(self, title_text: str):
        """Updates the active page title badge."""
        self.page_lbl.setText(f"✦ {title_text}")

    def minimize_window(self):
        win = self.window()
        if win:
            win.showMinimized()

    def toggle_maximize_window(self):
        win = self.window()
        if not win:
            return
        if win.isMaximized():
            win.showNormal()
            self.btn_max.setText("□")
            self.btn_max.setToolTip("Maximize")
        else:
            win.showMaximized()
            self.btn_max.setText("❐")
            self.btn_max.setToolTip("Restore")

    def close_window(self):
        win = self.window()
        if win:
            win.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            win = self.window()
            if win:
                self._drag_pos = event.globalPosition().toPoint() - win.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            win = self.window()
            if win and not win.isMaximized():
                win.move(event.globalPosition().toPoint() - self._drag_pos)
                event.accept()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_maximize_window()
            event.accept()
