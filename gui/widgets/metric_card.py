"""
gui/widgets/metric_card.py - Clean Modern Telemetry Card matching Design System
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor


class MetricCard(QFrame):
    clicked = Signal()

    def __init__(self, value: str, label: str, is_featured: bool = False, is_clickable: bool = False, parent=None):
        super().__init__(parent)
        self.is_clickable = is_clickable
        self.is_featured = is_featured
        self.setObjectName("MetricCard")
        self.init_ui(value, label)

    def init_ui(self, value: str, label: str):
        self.setProperty("class", "card-featured" if self.is_featured else "card")
        if self.is_clickable:
            self.setCursor(QCursor(Qt.PointingHandCursor))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        self.val_lbl = QLabel(value)
        self.val_lbl.setAlignment(Qt.AlignCenter)
        self.val_lbl.setProperty("class", "metric-value")

        self.title_lbl = QLabel(label)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setProperty("class", "metric-label")

        layout.addWidget(self.val_lbl)
        layout.addWidget(self.title_lbl)

    def set_value(self, value: str):
        self.val_lbl.setText(value)

    def set_label(self, label: str):
        self.title_lbl.setText(label)

    def set_featured(self, featured: bool):
        self.is_featured = featured
        self.setProperty("class", "card-featured" if featured else "card")
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, event):
        if self.is_clickable and event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
