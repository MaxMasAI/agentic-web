"""
gui/widgets/metric_card.py - High-Tech Glassmorphism Telemetry Card
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QCursor


class MetricCard(QFrame):
    clicked = Signal()

    def __init__(self, value: str, label: str, color: str = "#38bdf8", is_clickable: bool = False, parent=None):
        super().__init__(parent)
        self.is_clickable = is_clickable
        self.color = color
        self.setObjectName("MetricCard")
        self.init_ui(value, label)

    def init_ui(self, value: str, label: str):
        self.setStyleSheet(f"""
            QFrame#MetricCard {{
                background-color: rgba(15, 23, 42, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 12px;
            }}
            QFrame#MetricCard:hover {{
                border-color: {self.color}66;
                background-color: rgba(19, 29, 49, 0.9);
            }}
        """)
        if self.is_clickable:
            self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        self.val_lbl = QLabel(value)
        self.val_lbl.setAlignment(Qt.AlignCenter)
        self.val_lbl.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 800;
            color: {self.color};
            font-family: 'Segoe UI', sans-serif;
        """)

        self.title_lbl = QLabel(label)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet("""
            font-size: 11px;
            font-weight: 600;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.8px;
        """)

        layout.addWidget(self.val_lbl)
        layout.addWidget(self.title_lbl)

    def set_value(self, value: str):
        self.val_lbl.setText(value)

    def set_label(self, label: str):
        self.title_lbl.setText(label)

    def mousePressEvent(self, event):
        if self.is_clickable and event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
