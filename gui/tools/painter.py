"""
gui/tools/painter.py - Interactive Painter & Sketch Drawing Canvas
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QColorDialog, QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QImage, QPixmap


class DrawingCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StaticContents)
        self.pen_color = QColor("#38bdf8")
        self.pen_width = 4
        self.is_eraser = False
        self.drawing = False
        self.last_point = QPoint()
        self.image = QImage(900, 600, QImage.Format_RGB32)
        self.image.fill(QColor("#090d16"))

    def set_pen_color(self, color: QColor):
        self.pen_color = color
        self.is_eraser = False

    def set_pen_width(self, width: int):
        self.pen_width = width

    def set_eraser(self, enabled: bool):
        self.is_eraser = enabled

    def clear_canvas(self):
        self.image.fill(QColor("#090d16"))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawImage(0, 0, self.image)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_point = event.position().toPoint()
            self.drawing = True

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.LeftButton) and self.drawing:
            painter = QPainter(self.image)
            draw_color = QColor("#090d16") if self.is_eraser else self.pen_color
            pen = QPen(draw_color, self.pen_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            current_point = event.position().toPoint()
            painter.drawLine(self.last_point, current_point)
            self.last_point = current_point
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False


class PainterPage(QWidget):
    send_sketch_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = DrawingCanvas()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🎨 PAINTER & SKETCH CANVAS")
        title.setStyleSheet("font-size: 26px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Freehand Drawing, Concept Wireframing & Visual Prompt Sketchpad")
        subtitle.setStyleSheet("font-size: 12px; color: #64748b; font-family: monospace; margin-bottom: 4px;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        # Preset Color Palette Buttons
        colors = ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f87171", "#ffffff"]
        for hex_col in colors:
            btn = QPushButton()
            btn.setFixedSize(26, 26)
            btn.setStyleSheet(f"background-color: {hex_col}; border-radius: 13px; border: 2px solid #1e293b;")
            btn.clicked.connect(lambda _, c=hex_col: self.canvas.set_pen_color(QColor(c)))
            toolbar.addWidget(btn)

        self.btn_color_picker = QPushButton("🌈 Custom Color")
        self.btn_color_picker.clicked.connect(self.pick_custom_color)
        toolbar.addWidget(self.btn_color_picker)

        toolbar.addWidget(QLabel("<b>Brush Size:</b>"))
        self.slider_size = QSlider(Qt.Horizontal)
        self.slider_size.setRange(1, 30)
        self.slider_size.setValue(4)
        self.slider_size.setFixedWidth(120)
        self.slider_size.valueChanged.connect(self.canvas.set_pen_width)
        toolbar.addWidget(self.slider_size)

        self.btn_eraser = QPushButton("🧹 Eraser")
        self.btn_eraser.setCheckable(True)
        self.btn_eraser.toggled.connect(self.canvas.set_eraser)
        toolbar.addWidget(self.btn_eraser)

        self.btn_clear = QPushButton("🗑️ Clear Canvas")
        self.btn_clear.clicked.connect(self.canvas.clear_canvas)
        toolbar.addWidget(self.btn_clear)

        toolbar.addStretch()

        self.btn_save = QPushButton("💾 Save Image")
        self.btn_save.clicked.connect(self.save_sketch)
        toolbar.addWidget(self.btn_save)

        self.btn_export_studio = QPushButton("🚀 Send to Image Studio")
        self.btn_export_studio.setProperty("class", "primary-btn")
        self.btn_export_studio.clicked.connect(self.send_to_studio)
        toolbar.addWidget(self.btn_export_studio)

        main_layout.addLayout(toolbar)

        # Canvas Frame
        frame = QFrame()
        frame.setStyleSheet("border: 2px solid rgba(56, 189, 248, 0.3); border-radius: 10px; background: #090d16;")
        f_layout = QVBoxLayout(frame)
        f_layout.setContentsMargins(0, 0, 0, 0)

        f_layout.addWidget(self.canvas)
        main_layout.addWidget(frame, stretch=1)

    def pick_custom_color(self):
        col = QColorDialog.getColor(self.canvas.pen_color, self, "Pick Brush Color")
        if col.isValid():
            self.canvas.set_pen_color(col)

    def save_sketch(self):
        os.makedirs("downloads", exist_ok=True)
        dest, _ = QFileDialog.getSaveFileName(self, "Save Sketch", "downloads/sketch.png", "PNG Image (*.png)")
        if dest:
            self.canvas.image.save(dest)
            QMessageBox.information(self, "Saved", f"Sketch saved to {dest}")

    def send_to_studio(self):
        os.makedirs("downloads", exist_ok=True)
        path = os.path.join("downloads", "canvas_sketch.png")
        self.canvas.image.save(path)
        self.send_sketch_requested.emit(path)
        QMessageBox.information(self, "Exported", f"Sketch saved to '{path}' and attached to Media Studio!")
