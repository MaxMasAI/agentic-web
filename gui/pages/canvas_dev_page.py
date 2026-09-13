"""
gui/pages/canvas_dev_page.py - Autonomous Multi-Agent Infinite Canvas Development IDE.

Features:
- Infinite zoomable & pannable 2D workspace with dark grid and interactive radar minimap.
- Interactive connection wires with 4-directional Bézier routing, animated glowing execution particles,
  data-type color themes (Green: File Diff, Purple: Shell Stream, Blue: Agent Intent), and wire inspection modal.
- Live CLI Terminal Node with typewriter command reception and self-healing error triggers.
- Autonomous Agent Node with Thought / Tool / Artifact micro-tabs and Human-in-the-Loop (HITL) step breakpoints.
- File / Diff Viewer Node with one-click Accept Diff, Discard Diff, and Branching Versions (Option A / Option B).
- Sticky Note & Documentation Node for spatial task cards and architectural specs.
- Web Browser / Live Preview Node for previewing web apps and server outputs directly on the canvas.
- Canvas Right-Click Quick-Spawn menu.
- Dynamic recursive node creation (`create_node()`).
- "✨ Tidy Graph" Topological Layered DAG Auto-Layout engine.
- Complete JSON session export and import persistence.
"""

import os
import sys
import json
import time
import uuid
import math
import subprocess
import threading
import difflib
from typing import Dict, List, Optional, Tuple, Any

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsPathItem, QGraphicsProxyWidget, QGraphicsEllipseItem,
    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QFrame,
    QMessageBox, QFileDialog, QSplitter, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QMenu, QTabWidget, QCheckBox, QDialog
)
from PySide6.QtCore import Qt, QRectF, QPointF, Signal, QTimer, QThread, QUrl
from PySide6.QtGui import (
    QBrush, QPen, QColor, QFont, QPainterPath, QCursor, QPainter,
    QLinearGradient, QRadialGradient, QWheelEvent, QMouseEvent, QPixmap,
    QKeyEvent, QKeySequence, QShortcut
)

from core.canvas_engine import (
    CanvasEventBroker, CanvasNodeData, ConnectionEdgeData,
    ToolCallPayload, NodeContextStreamData, AutonomousAgentWorker
)


# ─────────────────────────────────────────────────────────────────────────────
#  0. Antigravity Collaborative Visual Agent Cursor
# ─────────────────────────────────────────────────────────────────────────────

class AntigravityCanvasCursorItem(QGraphicsItem):
    """
    Antigravity Collaborative Visual Agent Cursor for Canvas IDE.
    Shows an arrow pointer with an attached '[Agent Name] • agent' pill badge,
    theme color, glowing status dot, and smooth animated gliding.
    """
    def __init__(self, agent_name: str = "Atlas", color_hex: str = "#2e6f54", parent=None):
        super().__init__(parent)
        self.agent_name = agent_name
        self.color = QColor(color_hex)
        self.action_text = ""
        self.setZValue(100)
        self.setAcceptHoverEvents(False)
        self._target_pos = QPointF(0, 0)
        self._glide_timer = QTimer()
        self._glide_timer.setInterval(20)
        self._glide_timer.timeout.connect(self._step_glide)

    def boundingRect(self) -> QRectF:
        return QRectF(-5, -5, 260, 50)

    def set_agent(self, name: str, color_hex: str = "#2e6f54"):
        self.agent_name = name
        self.color = QColor(color_hex)
        self.update()

    def set_action(self, action: str):
        self.action_text = action
        self.update()

    def glide_to(self, target_point: QPointF):
        self._target_pos = target_point
        if not self._glide_timer.isActive():
            self._glide_timer.start()

    def _step_glide(self):
        cur = self.pos()
        dx = self._target_pos.x() - cur.x()
        dy = self._target_pos.y() - cur.y()
        if abs(dx) < 1.0 and abs(dy) < 1.0:
            self.setPos(self._target_pos)
            self._glide_timer.stop()
        else:
            self.setPos(QPointF(cur.x() + dx * 0.25, cur.y() + dy * 0.25))

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. White Arrow Pointer with dark stroke
        arrow_path = QPainterPath()
        arrow_path.moveTo(0, 0)
        arrow_path.lineTo(0, 16)
        arrow_path.lineTo(4.5, 12)
        arrow_path.lineTo(11, 12)
        arrow_path.closeSubpath()
        
        painter.setBrush(QBrush(QColor("#ffffff")))
        painter.setPen(QPen(QColor("#164e37"), 1.2))
        painter.drawPath(arrow_path)
        
        # 2. Pill Badge
        label_text = f"{self.agent_name} • agent"
        if self.action_text:
            label_text += f" | {self.action_text}"
            
        font = QFont("Inter", 8, QFont.Bold)
        font.setStyleHint(QFont.Monospace)
        painter.setFont(font)
        
        fm = painter.fontMetrics()
        txt_w = fm.horizontalAdvance(label_text)
        badge_w = txt_w + 24
        badge_h = 22
        badge_rect = QRectF(12, 10, badge_w, badge_h)
        
        # Drop shadow
        shadow_rect = QRectF(13, 12, badge_w, badge_h)
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(shadow_rect, 6.0, 6.0)
        
        # Badge background
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(QColor(255, 255, 255, 60), 1.0))
        painter.drawRoundedRect(badge_rect, 6.0, 6.0)
        
        # Glowing status dot
        painter.setBrush(QBrush(QColor("#4ade80")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(18, 18, 6, 6))
        
        # Badge text
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(QRectF(28, 10, txt_w, badge_h), Qt.AlignVCenter, label_text)


# ─────────────────────────────────────────────────────────────────────────────
#  1. Port Handle & Animated Bézier Connection Wire with Particles
# ─────────────────────────────────────────────────────────────────────────────

class PortHandleItem(QGraphicsEllipseItem):
    """Interactive Connection Handle on Node Perimeter (Top, Right, Bottom, Left)."""
    RADIUS = 6.5

    def __init__(self, node_item, side: str, port_name: str, parent=None):
        super().__init__(-self.RADIUS, -self.RADIUS, self.RADIUS * 2, self.RADIUS * 2, parent)
        self.node_item = node_item
        self.side = side  # "top", "right", "bottom", "left"
        self.port_name = port_name
        self.setAcceptHoverEvents(True)
        self.setZValue(12)
        self._update_color(False)

    def _update_color(self, hovered: bool):
        col_map = {
            "top": QColor("#38bdf8"),     # Cyan / Agent Intent
            "right": QColor("#38bdf8"),   # Cyan / Outgoing Bridge
            "bottom": QColor("#a78bfa"),  # Purple / Shell Stream
            "left": QColor("#34d399")     # Emerald / File Diff
        }
        col = col_map.get(self.side, QColor("#38bdf8"))
        if hovered:
            col = col.lighter(140)
        self.setBrush(QBrush(col))
        self.setPen(QPen(QColor("#030712"), 2.0))

    def hoverEnterEvent(self, event):
        self._update_color(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._update_color(False)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            scene = self.scene()
            if hasattr(scene, "start_wire_drag"):
                scene.start_wire_drag(self)
            event.accept()
        else:
            super().mousePressEvent(event)


class ContextBridgeWireItem(QGraphicsPathItem):
    """
    Dynamic Directed 4-Directional Bézier Connection wire linking two nodes.
    Features:
    - Glowing animated execution pulse particles.
    - Data-type color themes (Green: File, Purple: Shell, Blue: Agent).
    - Interactive inspection modal on click / right-click.
    """
    def __init__(self, edge_data: ConnectionEdgeData, start_pos: QPointF, end_pos: QPointF, parent=None):
        super().__init__(parent)
        self.edge_data = edge_data
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.setZValue(2)
        self.setAcceptHoverEvents(True)
        self._hovered = False

        # Particle Animation state
        self._particle_phase = 0.0
        self._is_active = False
        self._anim_timer = QTimer()
        self._anim_timer.setInterval(40)  # ~25 FPS animation
        self._anim_timer.timeout.connect(self._advance_particle)

        self.update_path()

    def set_active_stream(self, active: bool):
        self._is_active = active
        if active and not self._anim_timer.isActive():
            self._anim_timer.start()
        elif not active and self._anim_timer.isActive():
            self._anim_timer.stop()
            self.update()

    def _advance_particle(self):
        self._particle_phase = (self._particle_phase + 0.04) % 1.0
        self.update()

    def update_endpoints(self, start_pos: QPointF, end_pos: QPointF):
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.update_path()

    def _get_cubic_control_points(self) -> Tuple[QPointF, QPointF]:
        src_side = (getattr(self.edge_data, "source_port", "right") or "right").lower()
        tgt_side = (getattr(self.edge_data, "target_port", "left") or "left").lower()

        p1 = self.start_pos
        p2 = self.end_pos

        dist_x = abs(p2.x() - p1.x())
        dist_y = abs(p2.y() - p1.y())

        # Directional projection offsets based on connectivity axis
        offset_x = max(30.0, min(dist_x * 0.5, 300.0))
        offset_y = max(30.0, min(dist_y * 0.5, 300.0))

        # Source control point normal projection
        if src_side in ("right", "out", "output"):
            ctrl1 = QPointF(p1.x() + offset_x, p1.y())
        elif src_side in ("left", "in", "input"):
            ctrl1 = QPointF(p1.x() - offset_x, p1.y())
        elif src_side in ("top", "up"):
            ctrl1 = QPointF(p1.x(), p1.y() - offset_y)
        elif src_side in ("bottom", "down"):
            ctrl1 = QPointF(p1.x(), p1.y() + offset_y)
        else:
            ctrl1 = QPointF(p1.x() + offset_x, p1.y())

        # Target control point normal projection
        if tgt_side in ("right", "out", "output"):
            ctrl2 = QPointF(p2.x() + offset_x, p2.y())
        elif tgt_side in ("left", "in", "input"):
            ctrl2 = QPointF(p2.x() - offset_x, p2.y())
        elif tgt_side in ("top", "up"):
            ctrl2 = QPointF(p2.x(), p2.y() - offset_y)
        elif tgt_side in ("bottom", "down"):
            ctrl2 = QPointF(p2.x(), p2.y() + offset_y)
        else:
            ctrl2 = QPointF(p2.x() - offset_x, p2.y())

        return ctrl1, ctrl2

    def update_path(self):
        path = QPainterPath()
        path.moveTo(self.start_pos)
        ctrl1, ctrl2 = self._get_cubic_control_points()
        path.cubicTo(ctrl1, ctrl2, self.end_pos)
        self.setPath(path)

        # Wire color based on edge data type
        dt = getattr(self.edge_data, "data_type", "stream")
        if dt == "file_diff":
            base_col = QColor("#34d399")
        elif dt == "shell_stream":
            base_col = QColor("#a78bfa")
        else:
            base_col = QColor("#38bdf8")

        col = QColor("#ec4899") if self._hovered else base_col
        pen = QPen(col, 2.8 if not self._hovered else 3.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        self.setPen(pen)

    def paint(self, painter: QPainter, option, widget=None):
        super().paint(painter, option, widget)

        # Draw animated travelling execution particles when active or hovered
        if self._is_active or self._hovered:
            painter.setRenderHint(QPainter.Antialiasing)
            ctrl1, ctrl2 = self._get_cubic_control_points()

            # Compute positions along Bézier curve for multiple particles
            for i in range(3):
                t = (self._particle_phase + (i * 0.33)) % 1.0
                inv_t = 1.0 - t
                pt_x = (inv_t**3 * self.start_pos.x() +
                        3 * inv_t**2 * t * ctrl1.x() +
                        3 * inv_t * t**2 * ctrl2.x() +
                        t**3 * self.end_pos.x())
                pt_y = (inv_t**3 * self.start_pos.y() +
                        3 * inv_t**2 * t * ctrl1.y() +
                        3 * inv_t * t**2 * ctrl2.y() +
                        t**3 * self.end_pos.y())

                # Glowing particle
                p_col = QColor("#38bdf8" if i % 2 == 0 else "#a78bfa")
                p_col.setAlpha(220)
                painter.setBrush(QBrush(p_col))
                painter.setPen(QPen(QColor("#ffffff"), 1.0))
                painter.drawEllipse(QPointF(pt_x, pt_y), 4.5, 4.5)

    def hoverEnterEvent(self, event):
        self._hovered = True
        self.setToolTip(f"Context Bridge: {self.edge_data.source_node_id} -> {self.edge_data.target_node_id}\nClick to inspect stream payload.")
        self.update_path()
        if not self._anim_timer.isActive():
            self._anim_timer.start()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._hovered = False
        self.update_path()
        if not self._is_active and self._anim_timer.isActive():
            self._anim_timer.stop()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.show_inspection_dialog()
            event.accept()
        elif event.button() == Qt.RightButton:
            menu = QMenu()
            inspect_act = menu.addAction("🔍 Inspect Context Payloads")
            menu.addSeparator()
            del_act = menu.addAction("🗑️ Disconnect Bridge")
            action = menu.exec(event.screenPos())
            if action == inspect_act:
                self.show_inspection_dialog()
            elif action == del_act:
                scene = self.scene()
                if hasattr(scene, "remove_wire"):
                    scene.remove_wire(self)
            event.accept()
        else:
            super().mousePressEvent(event)

    def show_inspection_dialog(self):
        """Displays interactive Edge Inspection modal with live payload history."""
        broker = CanvasEventBroker.get_instance()
        history = broker.get_edge_history(self.edge_data.edge_id)

        dlg = QDialog()
        dlg.setWindowTitle(f"🔍 Context Bridge Inspector - {self.edge_data.edge_id}")
        dlg.resize(620, 420)
        dlg.setStyleSheet("""
            QDialog {
                background-color: #0b1120;
                color: #f8fafc;
            }
            QLabel { color: #cbd5e1; font-size: 12px; }
            QTableWidget {
                background-color: #030712;
                color: #f8fafc;
                gridline-color: #1e293b;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
            QHeaderView::section {
                background-color: #0f172a;
                color: #94a3b8;
                font-weight: 700;
                padding: 4px;
                border: 1px solid #1e293b;
            }
            QPlainTextEdit {
                background-color: #030712;
                color: #4ade80;
                font-family: monospace;
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout(dlg)

        # Header Info
        hdr = QHBoxLayout()
        hdr.addWidget(QLabel(f"<b>Source:</b> <span style='color:#38bdf8;'>{self.edge_data.source_node_id}</span> ({self.edge_data.source_port})"))
        hdr.addWidget(QLabel(f"<b>Target:</b> <span style='color:#a78bfa;'>{self.edge_data.target_node_id}</span> ({self.edge_data.target_port})"))
        hdr.addWidget(QLabel(f"<b>Type:</b> {self.edge_data.data_type}"))
        layout.addLayout(hdr)

        # History Table
        table = QTableWidget(len(history), 4)
        table.setHorizontalHeaderLabels(["Time", "Payload Type", "Size", "Content Preview"])
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        for row, entry in enumerate(reversed(history)):
            tm = time.strftime("%H:%M:%S", time.localtime(entry.get("timestamp", time.time())))
            table.setItem(row, 0, QTableWidgetItem(tm))
            table.setItem(row, 1, QTableWidgetItem(entry.get("payload_type", "stream")))
            table.setItem(row, 2, QTableWidgetItem(f"{entry.get('byte_size', 0)} B"))
            table.setItem(row, 3, QTableWidgetItem(entry.get("content_preview", "")[:60]))

        layout.addWidget(table, stretch=2)

        # Selected Payload Detail
        detail_view = QPlainTextEdit()
        detail_view.setReadOnly(True)
        detail_view.setPlaceholderText("Select a payload above to inspect raw contents...")
        layout.addWidget(detail_view, stretch=1)

        def on_row_selected(row, col):
            if 0 <= row < len(history):
                idx = len(history) - 1 - row
                item = history[idx]
                detail_view.setPlainText(item.get("content_preview", "") + "\n\nMetadata:\n" + json.dumps(item.get("metadata", {}), indent=2))

        table.cellClicked.connect(on_row_selected)
        if history:
            on_row_selected(0, 0)

        # Close
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("background: #1e293b; color: white; padding: 5px 15px; border-radius: 4px;")
        close_btn.clicked.connect(dlg.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)

        dlg.exec()


# ─────────────────────────────────────────────────────────────────────────────
#  2. Custom Interactive Node Widgets
# ─────────────────────────────────────────────────────────────────────────────

class CLITerminalNodeWidget(QFrame):
    """
    Live interactive shell terminal node on the canvas.
    Features:
    - Real-time command execution with error interception & downstream self-healing trigger.
    - Agent command output typing reception.
    """
    def __init__(self, node_id: str, title: str = "Terminal / CLI", parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.title = title
        self.broker = CanvasEventBroker.get_instance()
        self.init_ui()
        self.broker.subscribe(self.node_id, self.on_upstream_stream)
        self.broker.terminal_typewriter_dispatched.connect(self.on_agent_typewriter_command)

    def init_ui(self):
        self.setFixedSize(390, 300)
        self.setStyleSheet("""
            QFrame {
                background-color: #0b1120;
                border: 1.5px solid #1e293b;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        icon_lbl = QLabel("🖥️")
        icon_lbl.setStyleSheet("border:none; font-size: 13px;")
        title_lbl = QLabel(self.title)
        title_lbl.setStyleSheet("border:none; font-weight: 700; color: #38bdf8; font-size: 12px;")
        self.status_pill = QLabel("IDLE")
        self.status_pill.setStyleSheet("border:none; font-size: 9px; font-weight: 800; color: #94a3b8; background: #1e293b; border-radius: 4px; padding: 2px 6px;")

        hdr.addWidget(icon_lbl)
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        hdr.addWidget(self.status_pill)
        layout.addLayout(hdr)

        # Terminal Output Screen
        self.output_edit = QPlainTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #030712;
                color: #4ade80;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #1f2937;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        self.output_edit.appendPlainText("$ Agent Canvas Interactive Terminal ready.\n$ Connected to global pipeline event broker.")
        layout.addWidget(self.output_edit, stretch=1)

        # Command Input & Run Row
        cmd_row = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setPlaceholderText("Enter command (e.g. dir, python --version)...")
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 4px 8px;
                font-family: monospace;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 1px solid #38bdf8;
            }
        """)
        self.cmd_input.returnPressed.connect(self.execute_command)

        run_btn = QPushButton("▶ Run")
        run_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: 700;
                border: none;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #0369a1; }
        """)
        run_btn.clicked.connect(self.execute_command)

        clr_btn = QPushButton("🧹")
        clr_btn.setToolTip("Clear terminal output")
        clr_btn.setStyleSheet("background: #1e293b; border: none; border-radius: 4px; padding: 4px 6px;")
        clr_btn.clicked.connect(self.output_edit.clear)

        cmd_row.addWidget(self.cmd_input, stretch=1)
        cmd_row.addWidget(run_btn)
        cmd_row.addWidget(clr_btn)
        layout.addLayout(cmd_row)

    def execute_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        self.cmd_input.clear()
        self.output_edit.appendPlainText(f"\n$ {cmd}")
        self.status_pill.setText("RUNNING")
        self.status_pill.setStyleSheet("border:none; font-size: 9px; font-weight: 800; color: #38bdf8; background: rgba(56, 189, 248, 0.2); border-radius: 4px; padding: 2px 6px;")

        threading.Thread(target=self._run_cmd_thread, args=(cmd,), daemon=True).start()

    def _run_cmd_thread(self, cmd: str):
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            out = res.stdout if res.returncode == 0 else f"{res.stdout}\n{res.stderr}".strip()
            code = res.returncode
        except Exception as e:
            out = f"Execution error: {e}"
            code = 1

        QTimer.singleShot(0, lambda: self._on_cmd_done(cmd, out, code))

    def _on_cmd_done(self, cmd: str, out: str, exit_code: int):
        if out:
            self.output_edit.appendPlainText(out)
        self.status_pill.setText(f"EXIT {exit_code}")
        col = "#4ade80" if exit_code == 0 else "#f87171"
        bg = "rgba(74, 222, 128, 0.2)" if exit_code == 0 else "rgba(248, 113, 113, 0.2)"
        self.status_pill.setStyleSheet(f"border:none; font-size: 9px; font-weight: 800; color: {col}; background: {bg}; border-radius: 4px; padding: 2px 6px;")

        # Forward output or error trigger to downstream agents
        payload_type = "stdout" if exit_code == 0 else "stderr"
        content = f"Executed command: `{cmd}` (Exit: {exit_code})\nOutput:\n{out}"
        if exit_code != 0:
            content = f"[ERROR: CLI Command Failed with exit code {exit_code}]: cmd={cmd}\nOutput:\n{out}"

        self.broker.publish_stream(NodeContextStreamData(
            stream_id=str(uuid.uuid4())[:8],
            source_node_id=self.node_id,
            source_type="terminal",
            target_node_id=None,
            payload_type=payload_type,
            content=content,
            metadata={"cmd": cmd, "exit_code": exit_code}
        ))

    def on_agent_typewriter_command(self, target_id: str, cmd: str):
        if target_id == self.node_id:
            # Simulate typewriter effect
            self.cmd_input.setText(cmd)
            QTimer.singleShot(400, self.execute_command)

    def on_upstream_stream(self, stream: NodeContextStreamData):
        if stream.payload_type == "tool_result" and "cmd" in stream.metadata:
            self.output_edit.appendPlainText(f"\n[Agent Tool Result]: {stream.metadata['cmd']}\n{stream.content}")


class AgentInspectorNodeWidget(QFrame):
    """
    Autonomous LLM Agent Inspector Node on the canvas.
    Features:
    - Micro-tabs: 🧠 Thoughts (Chain-of-Thought), 🛠️ Tool Calls, 📦 Artifacts.
    - Human-in-the-Loop (HITL) step approval breakpoint toggle.
    """
    def __init__(self, node_id: str, title: str = "Autonomous Agent", parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.title = title
        self.broker = CanvasEventBroker.get_instance()
        self.worker: Optional[AutonomousAgentWorker] = None
        self.worker_thread: Optional[threading.Thread] = None
        self._current_pending_tool: Optional[ToolCallPayload] = None
        self.init_ui()
        self.broker.subscribe(self.node_id, self.on_upstream_stream)

    def init_ui(self):
        self.setFixedSize(440, 360)
        self.setStyleSheet("""
            QFrame {
                background-color: #0b1120;
                border: 1.5px solid #6366f1;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        icon_lbl = QLabel("🤖")
        icon_lbl.setStyleSheet("border:none; font-size: 13px;")
        title_lbl = QLabel(self.title)
        title_lbl.setStyleSheet("border:none; font-weight: 700; color: #a78bfa; font-size: 12px;")

        self.model_badge = QLabel("gemini-2.5-pro")
        self.model_badge.setStyleSheet("border:none; font-size: 9px; font-weight: 700; color: #94a3b8; background: #1e293b; border-radius: 4px; padding: 2px 6px;")

        self.status_pill = QLabel("IDLE")
        self.status_pill.setStyleSheet("border:none; font-size: 9px; font-weight: 800; color: #94a3b8; background: #1e293b; border-radius: 4px; padding: 2px 6px;")

        hdr.addWidget(icon_lbl)
        hdr.addWidget(title_lbl)
        hdr.addWidget(self.model_badge)
        hdr.addStretch()
        hdr.addWidget(self.status_pill)
        layout.addLayout(hdr)

        # Goal Directive Row
        self.goal_input = QLineEdit("Inspect repository, generate modular implementation, and verify execution")
        self.goal_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 3px 6px;
                font-size: 11px;
            }
        """)
        layout.addWidget(self.goal_input)

        # ── Micro-Tabs Drawer (Thoughts / Tool Calls / Artifacts) ───────────
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1f2937;
                border-radius: 6px;
                background: #030712;
            }
            QTabBar::tab {
                background: #0f172a;
                color: #94a3b8;
                padding: 4px 10px;
                font-size: 10px;
                font-weight: 700;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #1e293b;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
        """)

        # Tab 1: Thoughts (Chain-of-Thought Log)
        self.thought_edit = QTextEdit()
        self.thought_edit.setReadOnly(True)
        self.thought_edit.setStyleSheet("background-color: #030712; color: #cbd5e1; font-size: 11px; padding: 4px; border: none;")
        self.thought_edit.append("<span style='color:#64748b;'>Agent initialized. Awaiting user directive or upstream context trigger.</span>")
        self.tabs.addTab(self.thought_edit, "🧠 Thoughts")

        # Tab 2: Tool Calls
        self.tool_calls_edit = QTextEdit()
        self.tool_calls_edit.setReadOnly(True)
        self.tool_calls_edit.setStyleSheet("background-color: #030712; color: #a78bfa; font-family: monospace; font-size: 10.5px; padding: 4px; border: none;")
        self._has_tool_executions = False
        self.tool_calls_edit.setHtml("""
            <div style='color: #94a3b8;'>
                <b style='color: #38bdf8;'>🛠️ Available Agent Tools:</b><br/>
                • <code>run_command</code> (Shell execution & syntax test)<br/>
                • <code>read_file</code> (Local workspace inspection)<br/>
                • <code>write_file</code> (Surgical module & patch creation)<br/>
                • <code>create_node</code> (Parallel terminal worker spawning)<br/>
                • <code>mcp_tools</code> (MCP Hub registered tools)<br/>
                <hr style='border: 1px solid #1e293b; margin: 6px 0;'/>
                <span style='color: #64748b; font-style: italic;'>Click '⚡ Launch Autonomous Loop' or '⏭️ Step' to execute tool iterations.</span>
            </div>
        """)
        self.tabs.addTab(self.tool_calls_edit, "🛠️ Tool Calls")

        # Tab 3: Artifacts
        self.artifacts_edit = QTextEdit()
        self.artifacts_edit.setReadOnly(True)
        self.artifacts_edit.setStyleSheet("background-color: #030712; color: #34d399; font-size: 10.5px; padding: 4px; border: none;")
        self.artifacts_edit.append("<span style='color:#64748b;'>No generated artifacts yet.</span>")
        self.tabs.addTab(self.artifacts_edit, "📦 Artifacts")

        layout.addWidget(self.tabs, stretch=1)

        # ── HITL Breakpoint Notification Bar ──────────────────────────────
        self.hitl_bar = QFrame()
        self.hitl_bar.setVisible(False)
        self.hitl_bar.setStyleSheet("background: rgba(245, 158, 11, 0.15); border: 1px solid #f59e0b; border-radius: 4px; padding: 3px;")
        hitl_layout = QHBoxLayout(self.hitl_bar)
        hitl_layout.setContentsMargins(4, 2, 4, 2)
        self.hitl_msg = QLabel("🛑 Tool Breakpoint: Approve execution?")
        self.hitl_msg.setStyleSheet("color: #fbbf24; font-size: 10px; font-weight: 700; border: none;")

        approve_btn = QPushButton("✅ Approve")
        approve_btn.setStyleSheet("background: #059669; color: white; font-weight: 700; font-size: 10px; border-radius: 3px; padding: 2px 8px;")
        approve_btn.clicked.connect(lambda: self.handle_hitl_decision(True))

        reject_btn = QPushButton("❌ Reject")
        reject_btn.setStyleSheet("background: #dc2626; color: white; font-weight: 700; font-size: 10px; border-radius: 3px; padding: 2px 8px;")
        reject_btn.clicked.connect(lambda: self.handle_hitl_decision(False))

        hitl_layout.addWidget(self.hitl_msg, stretch=1)
        hitl_layout.addWidget(approve_btn)
        hitl_layout.addWidget(reject_btn)
        layout.addWidget(self.hitl_bar)

        # ── Footer Controls ───────────────────────────────────────────────
        ftr = QHBoxLayout()
        self.run_btn = QPushButton("⚡ Launch Autonomous Loop")
        self.run_btn.setStyleSheet("background-color: #4f46e5; color: white; font-weight: 700; border: none; border-radius: 4px; padding: 5px 12px; font-size: 11px;")
        self.run_btn.clicked.connect(self.toggle_autonomous_loop)

        self.hitl_checkbox = QCheckBox("🛑 Human-in-the-Loop")
        self.hitl_checkbox.setToolTip("Pause on every tool step for human approval")
        self.hitl_checkbox.setStyleSheet("color: #cbd5e1; font-size: 10px; font-weight: 700;")

        step_btn = QPushButton("⏭️ Step")
        step_btn.setStyleSheet("background: #1e293b; color: #cbd5e1; border: none; border-radius: 4px; padding: 5px 8px; font-size: 11px;")
        step_btn.clicked.connect(self.step_one_iteration)

        ftr.addWidget(self.run_btn, stretch=1)
        ftr.addWidget(self.hitl_checkbox)
        ftr.addWidget(step_btn)
        layout.addLayout(ftr)

    def toggle_autonomous_loop(self):
        if self.worker and self.worker._is_running:
            self.worker.stop()
            self.run_btn.setText("⚡ Launch Autonomous Loop")
            self.run_btn.setStyleSheet("background-color: #4f46e5; color: white; font-weight: 700; border: none; border-radius: 4px; padding: 5px 12px;")
            self.hitl_bar.setVisible(False)
        else:
            self.start_worker_thread()

    def start_worker_thread(self):
        goal = self.goal_input.text().strip() or "Inspect and implement autonomous directive"
        hitl = self.hitl_checkbox.isChecked()
        self.worker = AutonomousAgentWorker(self.node_id, goal=goal, human_in_the_loop=hitl)
        self.worker.log_emitted.connect(self.on_worker_log)
        self.worker.status_changed.connect(self.on_worker_status)
        self.worker.thought_emitted.connect(self.on_thought_emitted)
        self.worker.tool_executed.connect(self.on_tool_executed)
        self.worker.artifact_emitted.connect(self.on_artifact_emitted)
        self.worker.tool_approval_requested.connect(self.on_tool_approval_requested)
        self.worker.loop_finished.connect(self.on_worker_finished)

        self.run_btn.setText("⏹️ Stop Loop")
        self.run_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: 700; border: none; border-radius: 4px; padding: 5px 12px;")

        self.worker.start()

    def step_one_iteration(self):
        if not self.worker or not self.worker._is_running:
            self.start_worker_thread()
        else:
            self.worker.resume()

    def handle_hitl_decision(self, approved: bool):
        self.hitl_bar.setVisible(False)
        if self.worker:
            self.worker.resolve_approval(approved)

    def on_tool_approval_requested(self, node_id: str, tool_call: ToolCallPayload):
        self.hitl_msg.setText(f"🛑 Approve `{tool_call.tool_name}`: {json.dumps(tool_call.arguments)[:40]}...")
        self.hitl_bar.setVisible(True)
        self.tabs.setCurrentIndex(1)  # Focus Tool Calls tab

    def on_thought_emitted(self, node_id: str, thought: str):
        self.thought_edit.append(f"<p><b style='color:#38bdf8;'>🧠 Thought:</b> {thought}</p>")

    def on_tool_executed(self, node_id: str, payload: ToolCallPayload):
        if not getattr(self, "_has_tool_executions", False):
            self._has_tool_executions = True
            self.tool_calls_edit.clear()

        col = "#4ade80" if payload.status == "success" else "#f87171"
        self.tool_calls_edit.append(
            f"<div style='margin-bottom:6px; padding:4px; background: rgba(15, 23, 42, 0.6); border-radius: 4px; border-left: 2px solid {col};'>"
            f"<span style='color:#38bdf8; font-weight:bold;'>🛠️ {payload.tool_name}</span> "
            f"<span style='color:{col}; font-weight:bold;'>[{payload.status.upper()}]</span><br/>"
            f"<span style='color:#94a3b8;'><b>Args:</b> {json.dumps(payload.arguments)}</span><br/>"
            f"<span style='color:#e2e8f0;'><b>Result:</b> {payload.result}</span>"
            f"</div>"
        )

    def on_artifact_emitted(self, node_id: str, atype: str, info: str):
        self.artifacts_edit.append(f"📦 <b>[{atype.upper()}]</b> {info}")

    def on_worker_log(self, node_id: str, level: str, msg: str):
        col_map = {
            "INFO": "#94a3b8", "PLAN": "#38bdf8", "THOUGHT": "#c084fc",
            "TOOL": "#fbbf24", "REFLECT": "#60a5fa", "SUCCESS": "#4ade80",
            "HITL": "#fbbf24", "REJECTED": "#f87171"
        }
        col = col_map.get(level, "#cbd5e1")
        self.thought_edit.append(f"<span style='color:{col};'><b>[{level}]</b> {msg}</span>")

    def on_worker_status(self, node_id: str, status: str):
        self.status_pill.setText(status.upper())
        col_map = {"idle": "#94a3b8", "planning": "#38bdf8", "executing": "#fbbf24", "done": "#4ade80", "paused": "#f59e0b"}
        bg_map = {
            "idle": "#1e293b", "planning": "rgba(56, 189, 248, 0.2)",
            "executing": "rgba(251, 191, 36, 0.2)", "done": "rgba(74, 222, 128, 0.2)",
            "paused": "rgba(245, 158, 11, 0.2)"
        }
        self.status_pill.setStyleSheet(
            f"border:none; font-size: 9px; font-weight: 800; color: {col_map.get(status, '#cbd5e1')}; "
            f"background: {bg_map.get(status, '#1e293b')}; border-radius: 4px; padding: 2px 6px;"
        )

    def on_worker_finished(self, node_id: str, success: bool, summary: str):
        self.run_btn.setText("⚡ Launch Autonomous Loop")
        self.run_btn.setStyleSheet("background-color: #4f46e5; color: white; font-weight: 700; border: none; border-radius: 4px; padding: 5px 12px;")
        self.hitl_bar.setVisible(False)

    def on_upstream_stream(self, stream: NodeContextStreamData):
        if stream.payload_type == "stderr" or "[ERROR" in stream.content:
            self.thought_edit.appendHtml(
                f"<b style='color:#f87171;'>[Interception Alert from {stream.source_type.upper()} {stream.source_node_id}]:</b> {stream.content[:140]}..."
            )
            # Auto-trigger self-healing if idle
            if not self.worker or not self.worker._is_running:
                self.goal_input.setText(f"Diagnose and resolve upstream error: {stream.content[:50]}...")
                self.start_worker_thread()
        else:
            self.thought_edit.appendHtml(
                f"<b style='color:#38bdf8;'>[Piped Context from {stream.source_type.upper()} {stream.source_node_id}]:</b> {stream.content[:140]}..."
            )


class FileDiffNodeWidget(QFrame):
    """
    Live Code & Unified Diff viewer on the canvas.
    Features:
    - One-click Accept Diff (write to disk) & Discard Diff (revert).
    - Branching Versions (Option A vs Option B comparison).
    """
    def __init__(self, node_id: str, title: str = "File / Diff Viewer", parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.title = title
        self.broker = CanvasEventBroker.get_instance()
        self._disk_original_content = ""
        self._branch_options = {"Option A": "", "Option B": ""}
        self.init_ui()
        self.broker.subscribe(self.node_id, self.on_upstream_stream)
        self.broker.file_diff_updated.connect(self.on_diff_updated)

    def init_ui(self):
        self.setFixedSize(410, 320)
        self.setStyleSheet("""
            QFrame {
                background-color: #0b1120;
                border: 1.5px solid #10b981;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(6)

        # Header
        hdr = QHBoxLayout()
        icon_lbl = QLabel("📄")
        icon_lbl.setStyleSheet("border:none; font-size: 13px;")
        title_lbl = QLabel(self.title)
        title_lbl.setStyleSheet("border:none; font-weight: 700; color: #34d399; font-size: 12px;")

        # Branch Selector
        self.branch_combo = QComboBox()
        self.branch_combo.addItems(["Option A (Primary)", "Option B (Alternate)"])
        self.branch_combo.setStyleSheet("""
            QComboBox {
                background: #0f172a;
                color: #38bdf8;
                border: 1px solid #1e293b;
                border-radius: 3px;
                font-size: 9px;
                padding: 1px 4px;
            }
        """)
        self.branch_combo.currentIndexChanged.connect(self.on_branch_switched)

        self.status_pill = QLabel("SYNCED")
        self.status_pill.setStyleSheet("border:none; font-size: 9px; font-weight: 800; color: #34d399; background: rgba(52, 211, 153, 0.2); border-radius: 4px; padding: 2px 6px;")

        hdr.addWidget(icon_lbl)
        hdr.addWidget(title_lbl)
        hdr.addWidget(self.branch_combo)
        hdr.addStretch()
        hdr.addWidget(self.status_pill)
        layout.addLayout(hdr)

        # File Selector Row
        file_row = QHBoxLayout()
        self.path_input = QLineEdit("tasks/autonomous_canvas_output.py")
        self.path_input.setStyleSheet("""
            QLineEdit {
                background-color: #0f172a;
                color: #f8fafc;
                border: 1px solid #334155;
                border-radius: 4px;
                padding: 3px 6px;
                font-family: monospace;
                font-size: 11px;
            }
        """)
        load_btn = QPushButton("📂 Load")
        load_btn.setStyleSheet("background: #1e293b; color: #f8fafc; border: none; border-radius: 4px; padding: 3px 8px; font-size: 11px;")
        load_btn.clicked.connect(self.load_file)

        file_row.addWidget(self.path_input, stretch=1)
        file_row.addWidget(load_btn)
        layout.addLayout(file_row)

        # Diff / Code Viewer
        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setStyleSheet("""
            QTextEdit {
                background-color: #030712;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid #1f2937;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        self.render_sample_diff()
        layout.addWidget(self.diff_view, stretch=1)

        # Footer Actions (Accept Diff / Discard Diff / Toggle Editor)
        ftr = QHBoxLayout()
        accept_btn = QPushButton("✅ Accept Diff")
        accept_btn.setToolTip("Writes current diff changes directly to disk")
        accept_btn.setStyleSheet("background: #059669; color: white; font-weight: 700; border: none; border-radius: 4px; padding: 4px 10px; font-size: 11px;")
        accept_btn.clicked.connect(self.accept_current_diff)

        discard_btn = QPushButton("❌ Discard")
        discard_btn.setToolTip("Discards generated diff and reverts to disk state")
        discard_btn.setStyleSheet("background: #dc2626; color: white; font-weight: 700; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
        discard_btn.clicked.connect(self.discard_current_diff)

        edit_toggle = QPushButton("✏️ Edit")
        edit_toggle.setStyleSheet("background: #1e293b; color: #cbd5e1; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
        edit_toggle.clicked.connect(lambda: self.diff_view.setReadOnly(not self.diff_view.isReadOnly()))

        ftr.addWidget(accept_btn)
        ftr.addWidget(discard_btn)
        ftr.addWidget(edit_toggle)
        ftr.addStretch()
        layout.addLayout(ftr)

    def render_sample_diff(self):
        sample = (
            "<span style='color:#64748b;'>@@ -1,4 +1,7 @@</span><br/>"
            "<span style='color:#cbd5e1;'> import asyncio</span><br/>"
            "<span style='color:#f87171;'>- def legacy_function():</span><br/>"
            "<span style='color:#f87171;'>-     pass</span><br/>"
            "<span style='color:#4ade80;'>+ async def execute_task():</span><br/>"
            "<span style='color:#4ade80;'>+     print('Agent Canvas autonomous pipeline operational')</span><br/>"
            "<span style='color:#4ade80;'>+     return {'status': 'SUCCESS'}</span>"
        )
        self.diff_view.setHtml(sample)
        self._branch_options["Option A"] = sample
        self._branch_options["Option B"] = sample.replace("Agent Canvas", "Agent Canvas (Branch B Parallel Variant)")

    def on_branch_switched(self, index: int):
        key = "Option A" if index == 0 else "Option B"
        content = self._branch_options.get(key, "")
        if content.startswith("<span"):
            self.diff_view.setHtml(content)
        else:
            self.diff_view.setPlainText(content)

    def load_file(self):
        path = self.path_input.text().strip()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self._disk_original_content = content
                self.diff_view.setPlainText(content)
                self.status_pill.setText("LOADED")
            except Exception as e:
                self.diff_view.setPlainText(f"Read error: {e}")
        else:
            self.diff_view.setPlainText(f"# File '{path}' does not exist yet.\n# It will be created when an agent writes code.")

    def accept_current_diff(self):
        path = self.path_input.text().strip()
        content = self.diff_view.toPlainText()
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            self._disk_original_content = content
            self.status_pill.setText("ACCEPTED")
            self.status_pill.setStyleSheet("border:none; font-size: 9px; font-weight: 800; color: #34d399; background: rgba(52, 211, 153, 0.2); border-radius: 4px; padding: 2px 6px;")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to accept diff: {e}")

    def discard_current_diff(self):
        if self._disk_original_content:
            self.diff_view.setPlainText(self._disk_original_content)
        else:
            self.load_file()
        self.status_pill.setText("DISCARDED")
        self.status_pill.setStyleSheet("border:none; font-size: 9px; font-weight: 800; color: #f87171; background: rgba(248, 113, 113, 0.2); border-radius: 4px; padding: 2px 6px;")

    def on_diff_updated(self, path: str, orig: str, modified: str):
        self.path_input.setText(path)
        self._disk_original_content = orig
        self._branch_options["Option A"] = modified

        diff_lines = list(difflib.unified_diff(
            orig.splitlines(), modified.splitlines(),
            fromfile="a/" + path, tofile="b/" + path, lineterm=""
        ))

        html_lines = []
        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                html_lines.append(f"<span style='color:#4ade80;'>{line}</span>")
            elif line.startswith("-") and not line.startswith("---"):
                html_lines.append(f"<span style='color:#f87171;'>{line}</span>")
            elif line.startswith("@@"):
                html_lines.append(f"<span style='color:#c084fc;'>{line}</span>")
            else:
                html_lines.append(f"<span style='color:#94a3b8;'>{line}</span>")

        if html_lines:
            self.diff_view.setHtml("<br/>".join(html_lines))
        else:
            self.diff_view.setPlainText(modified)

        self.status_pill.setText("DIFF AVAILABLE")
        self.status_pill.setStyleSheet("border:none; font-size: 9px; font-weight: 800; color: #60a5fa; background: rgba(96, 165, 250, 0.2); border-radius: 4px; padding: 2px 6px;")

    def on_upstream_stream(self, stream: NodeContextStreamData):
        if stream.payload_type == "diff":
            self.load_file()


class StickyNoteNodeWidget(QFrame):
    """
    Spatial Note & Architectural Spec Node on the canvas.
    """
    def __init__(self, node_id: str, title: str = "Mission Card / Spec", parent=None):
        super().__init__(parent)
        self.node_id = node_id
        self.title = title
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(280, 220)
        self.setStyleSheet("""
            QFrame {
                background-color: #1e1b4b;
                border: 1.5px solid #818cf8;
                border-radius: 8px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        hdr = QHBoxLayout()
        icon_lbl = QLabel("📌")
        title_lbl = QLabel(self.title)
        title_lbl.setStyleSheet("color: #c7d2fe; font-weight: 700; font-size: 11px;")
        hdr.addWidget(icon_lbl)
        hdr.addWidget(title_lbl)
        hdr.addStretch()
        layout.addLayout(hdr)

        self.note_edit = QTextEdit()
        self.note_edit.setPlaceholderText("Enter operator instructions, architecture specs, or acceptance criteria...")
        self.note_edit.setStyleSheet("""
            QTextEdit {
                background: #0f172a;
                color: #e0e7ff;
                border: 1px solid #312e81;
                border-radius: 4px;
                font-size: 11px;
                padding: 4px;
            }
        """)
        self.note_edit.setText("### Directive Specifications\n1. Run parallel unit test harnesses.\n2. Ensure zero regressions.\n3. Emit verified diffs.")
        layout.addWidget(self.note_edit)


# ─────────────────────────────────────────────────────────────────────────────
#  3. Canvas Visual Node Container Item
# ─────────────────────────────────────────────────────────────────────────────

class CanvasVisualNodeItem(QGraphicsRectItem):
    """Draggable Visual Container holding custom interactive Node widgets with 4-directional connection ports."""
    def __init__(self, node_data: CanvasNodeData, widget: QWidget, parent=None):
        w = widget.width()
        h = widget.height()
        super().__init__(0, 0, w, h, parent)
        self.node_data = node_data
        self.widget = widget

        self.setPos(node_data.pos_x, node_data.pos_y)
        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setZValue(5)

        # Embedded Widget Proxy
        self.proxy = QGraphicsProxyWidget(self)
        self.proxy.setWidget(widget)
        self.proxy.setPos(0, 0)

        # 4-Directional Connection Port Handles (Top, Right, Bottom, Left)
        self.top_port = PortHandleItem(self, "top", "top", self)
        self.top_port.setPos(w * 0.5, 0)

        self.right_port = PortHandleItem(self, "right", "right", self)
        self.right_port.setPos(w, h * 0.5)

        self.bottom_port = PortHandleItem(self, "bottom", "bottom", self)
        self.bottom_port.setPos(w * 0.5, h)

        self.left_port = PortHandleItem(self, "left", "left", self)
        self.left_port.setPos(0, h * 0.5)

        self.ports = {
            "top": self.top_port,
            "right": self.right_port,
            "bottom": self.bottom_port,
            "left": self.left_port,
        }

        self.setPen(QPen(Qt.NoPen))
        self.setBrush(QBrush(Qt.transparent))

    def get_port_scene_pos(self, side: str = "right") -> QPointF:
        """Returns the scene coordinate for the specified port side (top, right, bottom, left)."""
        side_lower = (side or "right").lower()
        if side_lower in ("right", "out", "output"):
            return self.mapToScene(self.right_port.pos())
        elif side_lower in ("left", "in", "input"):
            return self.mapToScene(self.left_port.pos())
        elif side_lower in ("top", "up"):
            return self.mapToScene(self.top_port.pos())
        elif side_lower in ("bottom", "down"):
            return self.mapToScene(self.bottom_port.pos())
        return self.mapToScene(self.right_port.pos())

    def get_input_port_scene_pos(self) -> QPointF:
        return self.get_port_scene_pos("left")

    def get_output_port_scene_pos(self) -> QPointF:
        return self.get_port_scene_pos("right")

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            scene = self.scene()
            if hasattr(scene, "update_wires_for_node"):
                scene.update_wires_for_node(self.node_data.node_id)
            if hasattr(scene, "canvas_view") and hasattr(scene.canvas_view, "update_minimap"):
                scene.canvas_view.update_minimap()
        return super().itemChange(change, value)


# ─────────────────────────────────────────────────────────────────────────────
#  4. Infinite Canvas Scene & View
# ─────────────────────────────────────────────────────────────────────────────

class InfiniteCanvasScene(QGraphicsScene):
    """Infinite 2D Graph Scene with grid background and connection manager."""
    GRID_SIZE = 30

    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas_view = None
        self.setSceneRect(-10000, -10000, 20000, 20000)
        self.broker = CanvasEventBroker.get_instance()
        self.node_items: Dict[str, CanvasVisualNodeItem] = {}
        self.wire_items: Dict[str, ContextBridgeWireItem] = {}
        self.dragging_wire: Optional[QGraphicsPathItem] = None
        self.drag_start_port: Optional[PortHandleItem] = None

        self.broker.edge_payload_received.connect(self.on_edge_payload_received)

    def drawBackground(self, painter: QPainter, rect: QRectF):
        painter.fillRect(rect, QColor("#030712"))

        # Grid lines
        pen = QPen(QColor("#0f172a"), 1.0, Qt.DotLine)
        painter.setPen(pen)

        left = int(math.floor(rect.left() / self.GRID_SIZE) * self.GRID_SIZE)
        top = int(math.floor(rect.top() / self.GRID_SIZE) * self.GRID_SIZE)

        for x in range(left, int(rect.right()), self.GRID_SIZE):
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))

        for y in range(top, int(rect.bottom()), self.GRID_SIZE):
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)

    def add_canvas_node(self, node_data: CanvasNodeData, widget: QWidget) -> CanvasVisualNodeItem:
        item = CanvasVisualNodeItem(node_data, widget)
        self.addItem(item)
        self.node_items[node_data.node_id] = item
        self.broker.register_node(node_data)
        if self.canvas_view and hasattr(self.canvas_view, "update_minimap"):
            self.canvas_view.update_minimap()
        return item

    def remove_canvas_node(self, node_id: str):
        if node_id in self.node_items:
            item = self.node_items[node_id]
            self.removeItem(item)
            del self.node_items[node_id]
            self.broker.unregister_node(node_id)

            # Remove attached wires
            for eid in list(self.wire_items.keys()):
                edge = self.wire_items[eid].edge_data
                if edge.source_node_id == node_id or edge.target_node_id == node_id:
                    self.remove_wire(self.wire_items[eid])

            if self.canvas_view and hasattr(self.canvas_view, "update_minimap"):
                self.canvas_view.update_minimap()

    def connect_nodes(
        self,
        source_id: str,
        target_id: str,
        source_side: str = "right",
        target_side: str = "left",
        data_type: str = "stream",
        label: str = "Context Bridge"
    ):
        if source_id not in self.node_items or target_id not in self.node_items:
            return
        edge_id = f"edge_{source_id}_{source_side}_{target_id}_{target_side}_{int(time.time()*1000)}"
        edge_data = ConnectionEdgeData(
            edge_id=edge_id,
            source_node_id=source_id,
            source_port=source_side,
            target_node_id=target_id,
            target_port=target_side,
            data_type=data_type,
            label=label
        )
        src_item = self.node_items[source_id]
        tgt_item = self.node_items[target_id]

        wire = ContextBridgeWireItem(
            edge_data,
            src_item.get_port_scene_pos(source_side),
            tgt_item.get_port_scene_pos(target_side)
        )
        self.addItem(wire)
        self.wire_items[edge_id] = wire
        self.broker.add_edge(edge_data)

    def remove_wire(self, wire: ContextBridgeWireItem):
        eid = wire.edge_data.edge_id
        if eid in self.wire_items:
            self.removeItem(wire)
            del self.wire_items[eid]
            self.broker.remove_edge(eid)

    def update_wires_for_node(self, node_id: str):
        for wire in self.wire_items.values():
            e = wire.edge_data
            if e.source_node_id == node_id and e.source_node_id in self.node_items:
                wire.start_pos = self.node_items[e.source_node_id].get_port_scene_pos(e.source_port)
                wire.update_path()
            if e.target_node_id == node_id and e.target_node_id in self.node_items:
                wire.end_pos = self.node_items[e.target_node_id].get_port_scene_pos(e.target_port)
                wire.update_path()

    def on_edge_payload_received(self, edge_id: str, stream: NodeContextStreamData):
        if edge_id in self.wire_items:
            wire = self.wire_items[edge_id]
            wire.set_active_stream(True)
            QTimer.singleShot(2500, lambda: wire.set_active_stream(False))

    def start_wire_drag(self, port: PortHandleItem):
        self.drag_start_port = port
        self.dragging_wire = QGraphicsPathItem()
        pen = QPen(QColor("#38bdf8"), 2.0, Qt.DashLine)
        self.dragging_wire.setPen(pen)
        self.addItem(self.dragging_wire)

    def mouseMoveEvent(self, event):
        if self.dragging_wire and self.drag_start_port:
            p1 = self.drag_start_port.scenePos()
            p2 = event.scenePos()
            src_side = self.drag_start_port.side
            dist_x = abs(p2.x() - p1.x())
            dist_y = abs(p2.y() - p1.y())
            offset = max(45.0, max(dist_x, dist_y) * 0.45)

            if src_side == "right":
                ctrl1 = QPointF(p1.x() + offset, p1.y())
            elif src_side == "left":
                ctrl1 = QPointF(p1.x() - offset, p1.y())
            elif src_side == "top":
                ctrl1 = QPointF(p1.x(), p1.y() - offset)
            elif src_side == "bottom":
                ctrl1 = QPointF(p1.x(), p1.y() + offset)
            else:
                ctrl1 = QPointF(p1.x() + offset, p1.y())

            path = QPainterPath()
            path.moveTo(p1)
            path.quadTo(ctrl1, p2)
            self.dragging_wire.setPath(path)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.dragging_wire and self.drag_start_port:
            self.removeItem(self.dragging_wire)
            self.dragging_wire = None

            items = self.items(event.scenePos())
            for item in items:
                if isinstance(item, PortHandleItem) and item != self.drag_start_port:
                    src_node_id = self.drag_start_port.node_item.node_data.node_id
                    tgt_node_id = item.node_item.node_data.node_id
                    if src_node_id != tgt_node_id:
                        self.connect_nodes(
                            src_node_id,
                            tgt_node_id,
                            source_side=self.drag_start_port.side,
                            target_side=item.side
                        )
                    break
            self.drag_start_port = None
        super().mouseReleaseEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
#  5. Radar Minimap HUD Overlay
# ─────────────────────────────────────────────────────────────────────────────

class CanvasMinimapOverlay(QWidget):
    """
    Floating bottom-right radar minimap tracking all nodes and viewport position.
    """
    def __init__(self, canvas_view, parent=None):
        super().__init__(parent)
        self.canvas_view = canvas_view
        self.setFixedSize(180, 120)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setStyleSheet("""
            CanvasMinimapOverlay {
                background-color: rgba(11, 17, 32, 0.85);
                border: 1px solid #1e293b;
                border-radius: 6px;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(11, 17, 32, 210))
        painter.setPen(QPen(QColor("#1e293b"), 1.0))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 6, 6)

        scene = self.canvas_view.scene()
        if not scene or not scene.node_items:
            return

        min_x, min_y, max_x, max_y = 1e9, 1e9, -1e9, -1e9
        for item in scene.node_items.values():
            pos = item.pos()
            min_x = min(min_x, pos.x())
            min_y = min(min_y, pos.y())
            max_x = max(max_x, pos.x() + item.widget.width())
            max_y = max(max_y, pos.y() + item.widget.height())

        margin = 150.0
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        span_w = max(1.0, max_x - min_x)
        span_h = max(1.0, max_y - min_y)

        scale_x = (self.width() - 16) / span_w
        scale_y = (self.height() - 16) / span_h
        scale = min(scale_x, scale_y)

        # Draw nodes
        for item in scene.node_items.values():
            nx = 8 + (item.pos().x() - min_x) * scale
            ny = 8 + (item.pos().y() - min_y) * scale
            nw = item.widget.width() * scale
            nh = item.widget.height() * scale

            ntype = item.node_data.node_type
            col = QColor("#38bdf8") if ntype == "terminal" else (QColor("#a78bfa") if ntype == "agent" else QColor("#34d399"))
            painter.setBrush(QBrush(col))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(nx, ny, max(4.0, nw), max(3.0, nh)), 2, 2)

        # Draw Viewport Frame
        vp_rect = self.canvas_view.mapToScene(self.canvas_view.viewport().rect()).boundingRect()
        vx = 8 + (vp_rect.left() - min_x) * scale
        vy = 8 + (vp_rect.top() - min_y) * scale
        vw = vp_rect.width() * scale
        vh = vp_rect.height() * scale

        painter.setBrush(QBrush(QColor(56, 189, 248, 25)))
        painter.setPen(QPen(QColor("#38bdf8"), 1.2))
        painter.drawRect(QRectF(vx, vy, vw, vh))

    def mousePressEvent(self, event: QMouseEvent):
        scene = self.canvas_view.scene()
        if not scene or not scene.node_items:
            return

        min_x, min_y, max_x, max_y = 1e9, 1e9, -1e9, -1e9
        for item in scene.node_items.values():
            pos = item.pos()
            min_x = min(min_x, pos.x())
            min_y = min(min_y, pos.y())
            max_x = max(max_x, pos.x() + item.widget.width())
            max_y = max(max_y, pos.y() + item.widget.height())

        margin = 150.0
        min_x -= margin
        min_y -= margin
        max_x += margin
        max_y += margin

        span_w = max(1.0, max_x - min_x)
        span_h = max(1.0, max_y - min_y)

        scale = min((self.width() - 16) / span_w, (self.height() - 16) / span_h)
        click_x = min_x + (event.pos().x() - 8) / scale
        click_y = min_y + (event.pos().y() - 8) / scale
        self.canvas_view.centerOn(click_x, click_y)
        self.update()


class InfiniteCanvasView(QGraphicsView):
    """Pannable and Zoomable 2D Viewport with Minimap overlay and context menu."""
    def __init__(self, scene: InfiniteCanvasScene, parent=None):
        super().__init__(scene, parent)
        scene.canvas_view = self
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self._is_panning = False
        self._pan_start = QPointF()
        self.setFocusPolicy(Qt.StrongFocus)

        # Minimap
        self.minimap = CanvasMinimapOverlay(self, self)
        self.minimap.move(10, 10)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.minimap.move(self.width() - self.minimap.width() - 20, self.height() - self.minimap.height() - 20)
        self.update_minimap()

    def update_minimap(self):
        if hasattr(self, "minimap") and self.minimap:
            self.minimap.update()

    def wheelEvent(self, event: QWheelEvent):
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        current_scale = self.transform().m11()
        if 0.1 < current_scale * zoom_factor < 4.0:
            self.scale(zoom_factor, zoom_factor)
            self.update_minimap()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() in [Qt.MiddleButton] or (event.button() == Qt.LeftButton and event.modifiers() & Qt.AltModifier):
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        elif event.button() == Qt.RightButton:
            # Check if clicked on empty canvas area
            items = self.items(event.position().toPoint())
            if not items or len(items) == 1 and isinstance(items[0], QGraphicsRectItem) and items[0].brush().color() == Qt.transparent:
                self.show_canvas_context_menu(event)
                event.accept()
                return
            super().mousePressEvent(event)
        else:
            super().mousePressEvent(event)

    def show_canvas_context_menu(self, event: QMouseEvent):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #0b1120;
                color: #f8fafc;
                border: 1px solid #1e293b;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0284c7;
            }
        """)
        add_t = menu.addAction("➕ Add Terminal / CLI Node")
        add_a = menu.addAction("➕ Add Autonomous Agent Node")
        add_f = menu.addAction("➕ Add File / Diff Viewer Node")
        add_n = menu.addAction("📌 Add Note / Spec Card")
        menu.addSeparator()
        tidy_act = menu.addAction("✨ Tidy Graph (DAG Layout)")
        center_act = menu.addAction("🎯 Center Canvas View")

        action = menu.exec(event.globalPosition().toPoint())
        pos = self.mapToScene(event.position().toPoint())
        page = self.parent()

        if action == add_t and hasattr(page, "spawn_node"):
            page.spawn_node("terminal", pos_x=pos.x() - 190, pos_y=pos.y() - 140)
        elif action == add_a and hasattr(page, "spawn_node"):
            page.spawn_node("agent", pos_x=pos.x() - 210, pos_y=pos.y() - 160)
        elif action == add_f and hasattr(page, "spawn_node"):
            page.spawn_node("file_diff", pos_x=pos.x() - 200, pos_y=pos.y() - 150)
        elif action == add_n and hasattr(page, "spawn_node"):
            page.spawn_node("note", pos_x=pos.x() - 140, pos_y=pos.y() - 110)
        elif action == tidy_act and hasattr(page, "tidy_graph_dag"):
            page.tidy_graph_dag()
        elif action == center_act:
            self.centerOn(0, 0)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            self.update_minimap()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_panning:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            self.update_minimap()
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        """Dispatches keypresses directly so hotkeys work instantly when canvas viewport is active."""
        focused_widget = QApplication.focusWidget()
        is_editing_text = isinstance(focused_widget, (QLineEdit, QTextEdit, QPlainTextEdit))

        key = event.key()
        modifiers = event.modifiers()
        page = self.parent()

        # Ctrl+A: Select all items on canvas (if not typing in a text field)
        if key == Qt.Key_A and (modifiers & Qt.ControlModifier) and not (modifiers & (Qt.ShiftModifier | Qt.AltModifier)):
            if not is_editing_text and page and hasattr(page, "select_all_items"):
                page.select_all_items()
                event.accept()
                return

        # Delete / Backspace: Delete selected items (if not typing in a text field)
        if key in (Qt.Key_Delete, Qt.Key_Backspace):
            if not is_editing_text and page and hasattr(page, "delete_selected_items"):
                page.delete_selected_items()
                event.accept()
                return

        # Ctrl+T: Spawn terminal node
        if key == Qt.Key_T and (modifiers & Qt.ControlModifier):
            if not is_editing_text and page and hasattr(page, "spawn_node_at_viewport"):
                page.spawn_node_at_viewport("terminal")
                event.accept()
                return

        # Alt+A or Ctrl+Shift+A: Spawn autonomous agent node
        if (key == Qt.Key_A and (modifiers & Qt.AltModifier)) or (key == Qt.Key_A and (modifiers & Qt.ControlModifier) and (modifiers & Qt.ShiftModifier)):
            if page and hasattr(page, "spawn_node_at_viewport"):
                page.spawn_node_at_viewport("agent")
                event.accept()
                return

        # Alt+D or Ctrl+D: Spawn file diff node
        if (key == Qt.Key_D and (modifiers & Qt.AltModifier)) or (key == Qt.Key_D and (modifiers & Qt.ControlModifier)):
            if not is_editing_text and page and hasattr(page, "spawn_node_at_viewport"):
                page.spawn_node_at_viewport("file_diff")
                event.accept()
                return

        # F5 or Ctrl+Return / Ctrl+Enter: Run multi-agent pipeline
        if key == Qt.Key_F5 or (key in (Qt.Key_Return, Qt.Key_Enter) and (modifiers & Qt.ControlModifier)):
            if page and hasattr(page, "run_entire_pipeline"):
                page.run_entire_pipeline()
                event.accept()
                return

        # Ctrl+0: Center canvas viewport at origin
        if key == Qt.Key_0 and (modifiers & Qt.ControlModifier):
            self.centerOn(0, 0)
            event.accept()
            return

        # Ctrl+= or Ctrl++: Zoom in
        if key in (Qt.Key_Equal, Qt.Key_Plus) and (modifiers & Qt.ControlModifier):
            self.scale(1.2, 1.2)
            self.update_minimap()
            event.accept()
            return

        # Ctrl+-: Zoom out
        if key == Qt.Key_Minus and (modifiers & Qt.ControlModifier):
            self.scale(0.83, 0.83)
            self.update_minimap()
            event.accept()
            return

        # Ctrl+M: Load multi-agent demo scenario
        if key == Qt.Key_M and (modifiers & Qt.ControlModifier):
            if not is_editing_text and page and hasattr(page, "load_demo_scenario"):
                page.load_demo_scenario()
                event.accept()
                return

        # Ctrl+L: Clear canvas
        if key == Qt.Key_L and (modifiers & Qt.ControlModifier):
            if not is_editing_text and page and hasattr(page, "clear_canvas"):
                page.clear_canvas()
                event.accept()
                return

        # Ctrl+S: Export canvas session
        if key == Qt.Key_S and (modifiers & Qt.ControlModifier):
            if not is_editing_text and page and hasattr(page, "export_session"):
                page.export_session()
                event.accept()
                return

        # Ctrl+O: Import canvas session
        if key == Qt.Key_O and (modifiers & Qt.ControlModifier):
            if not is_editing_text and page and hasattr(page, "import_session"):
                page.import_session()
                event.accept()
                return

        # Alt+N: Spawn note card
        if key == Qt.Key_N and (modifiers & Qt.AltModifier):
            if page and hasattr(page, "spawn_node_at_viewport"):
                page.spawn_node_at_viewport("note")
                event.accept()
                return

        # Alt+T or Ctrl+Shift+T: Tidy Graph DAG layout
        if (key == Qt.Key_T and (modifiers & Qt.AltModifier)) or (key == Qt.Key_T and (modifiers & Qt.ControlModifier) and (modifiers & Qt.ShiftModifier)):
            if page and hasattr(page, "tidy_graph_dag"):
                page.tidy_graph_dag()
                event.accept()
                return

        # Ctrl+H: Show shortcuts cheatsheet
        if key == Qt.Key_H and (modifiers & Qt.ControlModifier):
            if page and hasattr(page, "show_shortcuts_modal"):
                page.show_shortcuts_modal()
                event.accept()
                return

        super().keyPressEvent(event)


# ─────────────────────────────────────────────────────────────────────────────
#  6. Main Canvas Dev Page Container
# ─────────────────────────────────────────────────────────────────────────────

class CanvasDevPage(QWidget):
    """
    Main Autonomous Multi-Agent Development Canvas.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = InfiniteCanvasScene(self)
        self.view = InfiniteCanvasView(self.scene, self)
        self.broker = CanvasEventBroker.get_instance()
        self.init_ui()
        self.load_demo_scenario()

        # Listen for recursive agent node spawn events
        self.broker.node_spawn_requested.connect(self.on_agent_node_spawn_requested)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top Control Toolbar ───────────────────────────────────────────
        toolbar = QFrame()
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #0b1120;
                border-bottom: 1.5px solid #1e293b;
                padding: 6px 12px;
            }
        """)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(8, 4, 8, 4)
        tb_layout.setSpacing(8)

        title_box = QHBoxLayout()
        title_box.setSpacing(6)
        logo_lbl = QLabel("🌌")
        logo_lbl.setStyleSheet("font-size: 16px;")
        name_lbl = QLabel("AGENT CANVAS IDE")
        name_lbl.setStyleSheet("font-weight: 900; color: #38bdf8; font-size: 14px; letter-spacing: 1px;")
        sub_lbl = QLabel("Autonomous Multi-Agent Infinite Workspace")
        sub_lbl.setStyleSheet("color: #64748b; font-size: 11px; margin-left: 4px;")
        title_box.addWidget(logo_lbl)
        title_box.addWidget(name_lbl)
        title_box.addWidget(sub_lbl)
        tb_layout.addLayout(title_box)

        tb_layout.addStretch()

        # Add Node Buttons
        add_term_btn = QPushButton("➕ Terminal")
        add_term_btn.setToolTip("Add new Terminal Node (Ctrl+T)")
        add_term_btn.setStyleSheet("background: #0f172a; color: #38bdf8; border: 1px solid #1e293b; border-radius: 4px; padding: 4px 8px; font-weight: 700; font-size: 11px;")
        add_term_btn.clicked.connect(lambda: self.spawn_node("terminal"))
        tb_layout.addWidget(add_term_btn)

        add_agent_btn = QPushButton("➕ Agent")
        add_agent_btn.setToolTip("Add new Autonomous Agent Node (Alt+A / Ctrl+Shift+A)")
        add_agent_btn.setStyleSheet("background: #0f172a; color: #a78bfa; border: 1px solid #1e293b; border-radius: 4px; padding: 4px 8px; font-weight: 700; font-size: 11px;")
        add_agent_btn.clicked.connect(lambda: self.spawn_node("agent"))
        tb_layout.addWidget(add_agent_btn)

        add_file_btn = QPushButton("➕ File/Diff")
        add_file_btn.setToolTip("Add new File/Diff Node (Alt+D / Ctrl+D)")
        add_file_btn.setStyleSheet("background: #0f172a; color: #34d399; border: 1px solid #1e293b; border-radius: 4px; padding: 4px 8px; font-weight: 700; font-size: 11px;")
        add_file_btn.clicked.connect(lambda: self.spawn_node("file_diff"))
        tb_layout.addWidget(add_file_btn)

        add_note_btn = QPushButton("📌 Note")
        add_note_btn.setToolTip("Add Spatial Spec / Sticky Note (Alt+N)")
        add_note_btn.setStyleSheet("background: #0f172a; color: #c7d2fe; border: 1px solid #1e293b; border-radius: 4px; padding: 4px 8px; font-weight: 700; font-size: 11px;")
        add_note_btn.clicked.connect(lambda: self.spawn_node("note"))
        tb_layout.addWidget(add_note_btn)

        # Pipeline Trigger
        run_pipe_btn = QPushButton("⚡ Run Pipeline")
        run_pipe_btn.setToolTip("Trigger connected agent pipeline (F5 / Ctrl+Enter)")
        run_pipe_btn.setStyleSheet("background: #4f46e5; color: white; border: none; border-radius: 4px; padding: 4px 12px; font-weight: 800; font-size: 11px;")
        run_pipe_btn.clicked.connect(self.run_entire_pipeline)
        tb_layout.addWidget(run_pipe_btn)

        # Auto-Layout / Tidy Graph
        tidy_btn = QPushButton("✨ Tidy Graph")
        tidy_btn.setToolTip("Organize canvas nodes into a clean DAG layout (Alt+T)")
        tidy_btn.setStyleSheet("background: #1e293b; color: #38bdf8; border: 1px solid #334155; border-radius: 4px; padding: 4px 10px; font-weight: 700; font-size: 11px;")
        tidy_btn.clicked.connect(self.tidy_graph_dag)
        tb_layout.addWidget(tidy_btn)

        # Session Export & Import
        export_btn = QPushButton("💾 Export")
        export_btn.setToolTip("Save complete canvas layout & edges to JSON (Ctrl+S)")
        export_btn.setStyleSheet("background: #1e293b; color: #cbd5e1; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
        export_btn.clicked.connect(self.export_session)
        tb_layout.addWidget(export_btn)

        import_btn = QPushButton("📂 Import")
        import_btn.setToolTip("Load saved canvas session JSON file (Ctrl+O)")
        import_btn.setStyleSheet("background: #1e293b; color: #cbd5e1; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
        import_btn.clicked.connect(self.import_session)
        tb_layout.addWidget(import_btn)

        # Demo Scenario Loader
        demo_btn = QPushButton("📦 Demo Scenario")
        demo_btn.setToolTip("Load Multi-Agent Template (Ctrl+M)")
        demo_btn.setStyleSheet("background: #0284c7; color: white; border: none; border-radius: 4px; padding: 4px 10px; font-weight: 700; font-size: 11px;")
        demo_btn.clicked.connect(self.load_demo_scenario)
        tb_layout.addWidget(demo_btn)

        # Clear & Reset View
        clr_btn = QPushButton("🧹 Clear")
        clr_btn.setToolTip("Clear all nodes on canvas (Ctrl+L)")
        clr_btn.setStyleSheet("background: #1e293b; color: #cbd5e1; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
        clr_btn.clicked.connect(self.clear_canvas)
        tb_layout.addWidget(clr_btn)

        center_btn = QPushButton("🎯 Center")
        center_btn.setToolTip("Center viewport at origin (Ctrl+0)")
        center_btn.setStyleSheet("background: #1e293b; color: #cbd5e1; border: none; border-radius: 4px; padding: 4px 8px; font-size: 11px;")
        center_btn.clicked.connect(lambda: self.view.centerOn(0, 0))
        tb_layout.addWidget(center_btn)

        # Shortcuts Info Button
        shortcuts_btn = QPushButton("⌨️ Hotkeys")
        shortcuts_btn.setToolTip("View Master Keyboard Shortcuts Cheatsheet (Ctrl+H)")
        shortcuts_btn.setStyleSheet("background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.4); border-radius: 4px; padding: 4px 8px; font-weight: 700; font-size: 11px;")
        shortcuts_btn.clicked.connect(self.show_shortcuts_modal)
        tb_layout.addWidget(shortcuts_btn)

        layout.addWidget(toolbar)

        # ── Main Canvas View ───────────────────────────────────────────────
        layout.addWidget(self.view, stretch=1)

        # Setup Canvas Keyboard Shortcuts
        self.init_canvas_shortcuts()

    def init_canvas_shortcuts(self):
        """Initializes dedicated keyboard shortcuts for canvas management."""
        self._shortcuts = []

        sc_map = [
            ("Ctrl+A", self.select_all_items),
            ("Ctrl+T", lambda: self.spawn_node_at_viewport("terminal")),
            ("Alt+A", lambda: self.spawn_node_at_viewport("agent")),
            ("Ctrl+Shift+A", lambda: self.spawn_node_at_viewport("agent")),
            ("Alt+D", lambda: self.spawn_node_at_viewport("file_diff")),
            ("Ctrl+D", lambda: self.spawn_node_at_viewport("file_diff")),
            ("Alt+N", lambda: self.spawn_node_at_viewport("note")),
            ("Alt+T", self.tidy_graph_dag),
            ("Ctrl+Shift+T", self.tidy_graph_dag),
            ("Ctrl+S", self.export_session),
            ("Ctrl+O", self.import_session),
            ("F5", self.run_entire_pipeline),
            ("Ctrl+Return", self.run_entire_pipeline),
            ("Ctrl+0", lambda: self.view.centerOn(0, 0)),
            ("Ctrl+=", lambda: self.view.scale(1.2, 1.2)),
            ("Ctrl++", lambda: self.view.scale(1.2, 1.2)),
            ("Ctrl+-", lambda: self.view.scale(0.83, 0.83)),
            ("Ctrl+L", self.clear_canvas),
            ("Ctrl+M", self.load_demo_scenario),
            ("Delete", self.delete_selected_items),
            ("Backspace", self.delete_selected_items),
        ]

        for key_seq, callback in sc_map:
            sc = QShortcut(QKeySequence(key_seq), self)
            sc.setContext(Qt.WidgetWithChildrenShortcut)
            sc.activated.connect(callback)
            self._shortcuts.append(sc)

    def select_all_items(self):
        """Selects all visual node items and connection wires on the canvas."""
        for item in self.scene.items():
            if isinstance(item, (CanvasVisualNodeItem, ContextBridgeWireItem)):
                item.setSelected(True)

    def spawn_node_at_viewport(self, node_type: str):
        center_pos = self.view.mapToScene(self.view.viewport().rect().center())
        self.spawn_node(node_type, pos_x=center_pos.x() - 190, pos_y=center_pos.y() - 140)

    def delete_selected_items(self):
        """Deletes any currently selected nodes or wires on the canvas."""
        for item in self.scene.selectedItems():
            if isinstance(item, CanvasVisualNodeItem):
                self.scene.remove_canvas_node(item.node_data.node_id)
            elif isinstance(item, ContextBridgeWireItem):
                self.scene.remove_wire(item)

    def show_shortcuts_modal(self):
        """Displays master side-by-side 3-column hotkey cheatsheet dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("⌨️ Agent Canvas IDE - Keyboard Shortcuts (Ctrl+H)")
        dialog.setMinimumWidth(920)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #0b1120;
                border: 1.5px solid rgba(56, 189, 248, 0.4);
                border-radius: 12px;
            }
            QLabel {
                color: #f8fafc;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #2563eb);
                color: white;
                font-weight: 700;
                border-radius: 6px;
                padding: 7px 24px;
                font-size: 12px;
                border: none;
            }
            QPushButton:hover {
                background: #38bdf8;
                color: #080b11;
            }
        """)
        d_layout = QVBoxLayout(dialog)
        d_layout.setContentsMargins(18, 16, 18, 16)
        d_layout.setSpacing(12)

        hdr = QLabel("<div style='margin-bottom: 2px;'><span style='font-size: 16px; font-weight: 800; color: #38bdf8;'>🌌 Agent Canvas IDE & Master Shortcuts</span> &nbsp;<span style='color: #64748b; font-size: 11px;'>(Press <b>Ctrl+H</b> anytime)</span></div>")
        d_layout.addWidget(hdr)

        content_lbl = QLabel()
        content_lbl.setText("""
        <table border="0" cellspacing="10" cellpadding="0" width="100%" style="font-family: 'Segoe UI', sans-serif;">
        <tr>
            <!-- Column 1: Agent Canvas IDE -->
            <td valign="top" width="36%" style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(167, 139, 250, 0.25); border-radius: 8px; padding: 10px 12px;">
                <div style="color: #a78bfa; font-weight: 800; font-size: 12px; border-bottom: 1px solid rgba(167, 139, 250, 0.2); padding-bottom: 4px; margin-bottom: 6px;">🌌 CANVAS NODE CONTROLS</div>
                <table border="0" cellpadding="3" cellspacing="0" width="100%" style="font-family: monospace; font-size: 11px;">
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+A</td><td style="color:#cbd5e1;">Select All Nodes & Wires</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Delete / Backspace</td><td style="color:#cbd5e1;">Delete Selected Items</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+T</td><td style="color:#cbd5e1;">Spawn CLI Terminal Node</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Alt+A / Ctrl+Shift+A</td><td style="color:#cbd5e1;">Spawn Autonomous Agent</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Alt+D / Ctrl+D</td><td style="color:#cbd5e1;">Spawn File / Diff Node</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Alt+N</td><td style="color:#cbd5e1;">Spawn Sticky Note Card</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Alt+T / Ctrl+Shift+T</td><td style="color:#cbd5e1;">✨ Tidy Graph (DAG Layout)</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">F5 / Ctrl+Enter</td><td style="color:#cbd5e1;">Run Multi-Agent Pipeline</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+S</td><td style="color:#cbd5e1;">Export Canvas Session JSON</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+O</td><td style="color:#cbd5e1;">Import Canvas Session JSON</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+M</td><td style="color:#cbd5e1;">Load Demo Template</td></tr>
                    <tr><td style="color:#a78bfa; font-weight:bold;">Ctrl+L</td><td style="color:#cbd5e1;">Clear Canvas</td></tr>
                </table>
            </td>

            <!-- Column 2: Canvas Viewport & Navigation -->
            <td valign="top" width="34%" style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 10px 12px;">
                <div style="color: #38bdf8; font-weight: 800; font-size: 12px; border-bottom: 1px solid rgba(56, 189, 248, 0.2); padding-bottom: 4px; margin-bottom: 6px;">🎯 VIEWPORT & NAVIGATION</div>
                <table border="0" cellpadding="3" cellspacing="0" width="100%" style="font-family: monospace; font-size: 11px;">
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+0</td><td style="color:#cbd5e1;">Center Viewport (0, 0)</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl++ / Ctrl+=</td><td style="color:#cbd5e1;">Zoom In Viewport</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+-</td><td style="color:#cbd5e1;">Zoom Out Viewport</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Middle-Click Drag</td><td style="color:#cbd5e1;">Pan Infinite Workspace</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Right-Click Area</td><td style="color:#cbd5e1;">Quick-Add Palette</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+B</td><td style="color:#cbd5e1;">Toggle Sidebar</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+H</td><td style="color:#cbd5e1;">Mission Control</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+D</td><td style="color:#cbd5e1;">Task Dispatch</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+K / Alt+C</td><td style="color:#cbd5e1;">Agent Canvas IDE</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+P</td><td style="color:#cbd5e1;">Playground Studio</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+U</td><td style="color:#cbd5e1;">Universal AI Chat</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Ctrl+E / Alt+E</td><td style="color:#cbd5e1;">Folder Explorer</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+S</td><td style="color:#cbd5e1;">Agent Squads</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+R</td><td style="color:#cbd5e1;">Deep Research</td></tr>
                    <tr><td style="color:#38bdf8; font-weight:bold;">Alt+M</td><td style="color:#cbd5e1;">Media Studio</td></tr>
                </table>
            </td>

            <!-- Column 3: Workflows & Actions -->
            <td valign="top" width="30%" style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(52, 211, 153, 0.25); border-radius: 8px; padding: 10px 12px;">
                <div style="color: #34d399; font-weight: 800; font-size: 12px; border-bottom: 1px solid rgba(52, 211, 153, 0.2); padding-bottom: 4px; margin-bottom: 6px;">🚀 DISPATCH & WORKFLOWS</div>
                <table border="0" cellpadding="3" cellspacing="0" width="100%" style="font-family: monospace; font-size: 11px;">
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+Enter</td><td style="color:#cbd5e1;">Deploy / Send / Run</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+N</td><td style="color:#cbd5e1;">New Conversation</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+Shift+L</td><td style="color:#cbd5e1;">Clear Chat History</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+S</td><td style="color:#cbd5e1;">Export HTML Preview</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Ctrl+Shift+X</td><td style="color:#cbd5e1;">Abort Active Mission</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">F5 / Ctrl+R</td><td style="color:#cbd5e1;">Global Refresh</td></tr>
                    <tr><td style="color:#34d399; font-weight:bold;">Esc</td><td style="color:#cbd5e1;">Close Modal / Dialog</td></tr>
                </table>
            </td>
        </tr>
        </table>
        """)
        d_layout.addWidget(content_lbl)

        btn_box = QHBoxLayout()
        btn_box.addStretch()
        close_btn = QPushButton("Done (Esc)")
        close_btn.clicked.connect(dialog.accept)
        btn_box.addWidget(close_btn)
        d_layout.addLayout(btn_box)

        dialog.exec()

    def spawn_node(self, node_type: str, pos_x: float = 0, pos_y: float = 0, title: Optional[str] = None) -> str:
        nid = str(uuid.uuid4())[:8]
        if node_type == "terminal":
            t = title or f"CLI Terminal #{len(self.scene.node_items)+1}"
            widget = CLITerminalNodeWidget(nid, t)
        elif node_type == "agent":
            t = title or f"Autonomous Agent #{len(self.scene.node_items)+1}"
            widget = AgentInspectorNodeWidget(nid, t)
        elif node_type == "file_diff":
            t = title or f"File Diff Viewer #{len(self.scene.node_items)+1}"
            widget = FileDiffNodeWidget(nid, t)
        elif node_type == "note":
            t = title or f"Mission Spec #{len(self.scene.node_items)+1}"
            widget = StickyNoteNodeWidget(nid, t)
        else:
            return ""

        node_data = CanvasNodeData(
            node_id=nid,
            node_type=node_type,
            title=t,
            pos_x=pos_x,
            pos_y=pos_y,
            width=widget.width(),
            height=widget.height()
        )
        self.scene.add_canvas_node(node_data, widget)
        return nid

    def on_agent_node_spawn_requested(self, ntype: str, title: str, offset_x: float, offset_y: float, args: dict):
        """Recursive node creation invoked by an autonomous agent tool call."""
        center_pos = self.view.mapToScene(self.view.viewport().rect().center())
        px = center_pos.x() + (offset_x if offset_x != 0 else 50.0)
        py = center_pos.y() + (offset_y if offset_y != 0 else 120.0)

        nid = self.spawn_node(ntype, pos_x=px, pos_y=py, title=title)

        # If terminal was spawned with initial cmd, auto execute
        if ntype == "terminal" and "cmd" in args and nid in self.scene.node_items:
            terminal_item = self.scene.node_items[nid]
            if isinstance(terminal_item.widget, CLITerminalNodeWidget):
                terminal_item.widget.cmd_input.setText(args["cmd"])
                QTimer.singleShot(600, terminal_item.widget.execute_command)

    def tidy_graph_dag(self):
        """
        Organizes canvas nodes into a clean left-to-right Directed Acyclic Graph (DAG) layout.
        Uses layered topological sorting based on edge dependencies.
        """
        nodes = list(self.scene.node_items.keys())
        if not nodes:
            return

        in_degree = {nid: 0 for nid in nodes}
        adj = {nid: [] for nid in nodes}

        for edge in self.broker.edges.values():
            if edge.source_node_id in in_degree and edge.target_node_id in in_degree:
                adj[edge.source_node_id].append(edge.target_node_id)
                in_degree[edge.target_node_id] += 1

        layers: Dict[int, List[str]] = {}
        node_layer: Dict[str, int] = {}

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        if not queue:
            queue = [nodes[0]]

        for nid in queue:
            node_layer[nid] = 0

        while queue:
            curr = queue.pop(0)
            curr_layer = node_layer[curr]
            if curr_layer not in layers:
                layers[curr_layer] = []
            layers[curr_layer].append(curr)

            for neighbor in adj.get(curr, []):
                new_layer = curr_layer + 1
                if neighbor not in node_layer or new_layer > node_layer[neighbor]:
                    node_layer[neighbor] = new_layer
                    if neighbor not in queue:
                        queue.append(neighbor)

        for nid in nodes:
            if nid not in node_layer:
                max_l = max(layers.keys(), default=0)
                node_layer[nid] = max_l + 1
                if max_l + 1 not in layers:
                    layers[max_l + 1] = []
                layers[max_l + 1].append(nid)

        layer_spacing_x = 480.0
        row_spacing_y = 350.0

        for l_idx, layer_nodes in layers.items():
            start_x = (l_idx - len(layers) / 2.0) * layer_spacing_x
            total_h = len(layer_nodes) * row_spacing_y
            start_y = -total_h / 2.0

            for r_idx, nid in enumerate(layer_nodes):
                item = self.scene.node_items.get(nid)
                if item:
                    target_x = start_x
                    target_y = start_y + r_idx * row_spacing_y
                    item.setPos(target_x, target_y)
                    item.node_data.pos_x = target_x
                    item.node_data.pos_y = target_y
                    self.scene.update_wires_for_node(nid)

        self.view.update_minimap()
        self.view.centerOn(0, 0)

    def export_session(self):
        """Exports the entire canvas graph, configurations, and memory to JSON."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Canvas Workspace Session", "agent_canvas_session.json", "JSON Files (*.json)"
        )
        if not file_path:
            return

        for nid, item in self.scene.node_items.items():
            item.node_data.pos_x = item.pos().x()
            item.node_data.pos_y = item.pos().y()

        data = self.broker.export_session_dict()
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            QMessageBox.information(self, "Export Session", f"Workspace session saved successfully to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to save session: {e}")

    def import_session(self):
        """Restores full canvas workspace session from JSON."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Canvas Workspace Session", "", "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.clear_canvas()

            for n in data.get("nodes", []):
                self.spawn_node(
                    node_type=n.get("node_type", "terminal"),
                    pos_x=n.get("pos_x", 0),
                    pos_y=n.get("pos_y", 0),
                    title=n.get("title")
                )

            for e in data.get("edges", []):
                self.scene.connect_nodes(
                    source_id=e.get("source_node_id"),
                    target_id=e.get("target_node_id"),
                    source_side=e.get("source_port", "right"),
                    target_side=e.get("target_port", "left"),
                    data_type=e.get("data_type", "stream"),
                    label=e.get("label", "Context Bridge")
                )

            self.view.centerOn(0, 0)
            self.view.update_minimap()
            QMessageBox.information(self, "Import Session", "Workspace session loaded and reconstructed successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to load session: {e}")

    def clear_canvas(self):
        for nid in list(self.scene.node_items.keys()):
            self.scene.remove_canvas_node(nid)

    def load_demo_scenario(self):
        """Loads a pre-configured full-stack multi-agent workflow."""
        self.clear_canvas()

        # 1. Terminal Node (Left)
        term_id = self.spawn_node("terminal", pos_x=-520, pos_y=-120, title="Development Shell (CLI)")

        # 2. Autonomous Agent Node (Center)
        agent_id = self.spawn_node("agent", pos_x=-40, pos_y=-140, title="Orchestrator Agent (Gemini)")

        # 3. File / Diff Viewer Node (Right)
        diff_id = self.spawn_node("file_diff", pos_x=480, pos_y=-130, title="Live Code & Git Diff Inspector")

        # 4. Note / Mission Spec (Top-Left)
        note_id = self.spawn_node("note", pos_x=-520, pos_y=-380, title="Pipeline Mission Card")

        # Connect Context Bridges
        self.scene.connect_nodes(term_id, agent_id, source_side="right", target_side="left", data_type="shell_stream", label="CLI Output Stream -> Agent Context")
        self.scene.connect_nodes(agent_id, diff_id, source_side="right", target_side="left", data_type="file_diff", label="Agent Code Emits -> File Diff")
        self.scene.connect_nodes(note_id, agent_id, source_side="right", target_side="top", data_type="agent_intent", label="Mission Specs -> Agent Goal")

        self.view.centerOn(0, -100)
        self.view.update_minimap()

    def run_entire_pipeline(self):
        """Triggers all active agent nodes on the canvas."""
        for item in self.scene.node_items.values():
            if item.node_data.node_type == "agent" and isinstance(item.widget, AgentInspectorNodeWidget):
                item.widget.toggle_autonomous_loop()
