"""
gui/tools/agent_builder.py - Node-Based Visual Agent Pipeline Builder
Implements visual graph editing with Start, Agent, Memory, and End nodes, slot connections,
middle-click panning, zooming, and compilation into OpenAI / LlamaIndex presets.
"""

import os
import json
import time
import math
from typing import List, Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsTextItem, QGraphicsLineItem, QGraphicsPathItem,
    QComboBox, QLineEdit, QFrame, QMessageBox, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QFont, QPainterPath, QCursor, QPainter

from core.agent_workflows import PRESETS, AgentWorkflowType


class NodeType:
    START = "Start"
    AGENT = "Agent"
    MEMORY = "Memory"
    END = "End"


class VisualConnection(QGraphicsPathItem):
    """Connection wire between two nodes."""
    def __init__(self, start_node, end_node, parent=None):
        super().__init__(parent)
        self.start_node = start_node
        self.end_node = end_node
        pen = QPen(QColor("#38bdf8"), 2.5)
        pen.setCapStyle(Qt.RoundCap)
        self.setPen(pen)
        self.setZValue(-1)
        self.update_path()

    def update_path(self):
        if not self.start_node or not self.end_node:
            return
        p1 = self.start_node.get_output_port_pos()
        p2 = self.end_node.get_input_port_pos()

        path = QPainterPath()
        path.moveTo(p1)
        dx = (p2.x() - p1.x()) * 0.5
        ctrl1 = QPointF(p1.x() + dx, p1.y())
        ctrl2 = QPointF(p2.x() - dx, p2.y())
        path.cubicTo(ctrl1, ctrl2, p2)
        self.setPath(path)


class VisualAgentNode(QGraphicsRectItem):
    """
    Visual Node Item with Input/Output Slots and configurable parameters.
    """
    def __init__(
        self,
        node_id: str,
        title: str,
        node_type: str = NodeType.AGENT,
        x: float = 50,
        y: float = 50,
        system_prompt: str = "",
        model_id: str = "gemini-2.0-flash",
        tools: Optional[List[str]] = None
    ):
        super().__init__(0, 0, 190, 85)
        self.setPos(x, y)
        self.node_id = node_id
        self.title = title
        self.node_type = node_type
        self.system_prompt = system_prompt
        self.model_id = model_id
        self.tools = tools or []
        self.connections: List[VisualConnection] = []

        self.setFlags(
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemSendsGeometryChanges
        )

        # Color Accent per Node Type
        palette = {
            NodeType.START: ("#10b981", "🎯 START"),
            NodeType.AGENT: ("#38bdf8", "🤖 AGENT"),
            NodeType.MEMORY: ("#f59e0b", "🧠 SHARED MEMORY"),
            NodeType.END: ("#c084fc", "🏁 END")
        }
        accent, type_label = palette.get(node_type, ("#818cf8", "NODE"))

        self.setBrush(QBrush(QColor("#0f172a")))
        self.setPen(QPen(QColor(accent), 2))

        # Title and Type Text Item
        self.title_item = QGraphicsTextItem(f"<b>[{type_label}]</b>\n{title}", self)
        self.title_item.setDefaultTextColor(QColor("#f8fafc"))
        self.title_item.setFont(QFont("Segoe UI", 9))
        self.title_item.setPos(10, 8)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            for conn in self.connections:
                conn.update_path()
        return super().itemChange(change, value)

    def get_input_port_pos(self) -> QPointF:
        return self.scenePos() + QPointF(0, 42)

    def get_output_port_pos(self) -> QPointF:
        return self.scenePos() + QPointF(190, 42)


class InteractiveGraphicsView(QGraphicsView):
    """Graphics View supporting Middle-Click Panning and Ctrl+Wheel Zoom."""
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._is_panning = False
        self._pan_start = QPointF()

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(zoom_factor, zoom_factor)
        else:
            super().wheelEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.position() - self._pan_start
            self._pan_start = event.position()
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class AgentBuilderPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.nodes: List[VisualAgentNode] = []
        self.connections: List[VisualConnection] = []
        self.selected_source_node: Optional[VisualAgentNode] = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)

        # Header Title
        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        title = QLabel("🧩 AGENTS BUILDER (Visual Workflow Editor)")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #38bdf8; letter-spacing: 1.2px;")
        subtitle = QLabel("Visual Node-Based Multi-Agent Pipeline Assembly: Connect Agents, Shared Memory & Decision Routes")
        subtitle.setStyleSheet("font-size: 11.5px; color: #64748b; font-family: monospace;")
        t_box.addWidget(title)
        t_box.addWidget(subtitle)
        main_layout.addLayout(t_box)

        # Palette Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_add_start = QPushButton("🎯 + Start")
        self.btn_add_start.clicked.connect(lambda *args: self.add_node_by_type(NodeType.START))
        toolbar.addWidget(self.btn_add_start)

        self.btn_add_agent = QPushButton("🤖 + Agent")
        self.btn_add_agent.clicked.connect(lambda *args: self.add_node_by_type(NodeType.AGENT))
        toolbar.addWidget(self.btn_add_agent)

        self.btn_add_memory = QPushButton("🧠 + Memory")
        self.btn_add_memory.clicked.connect(lambda *args: self.add_node_by_type(NodeType.MEMORY))
        toolbar.addWidget(self.btn_add_memory)

        self.btn_add_end = QPushButton("🏁 + End")
        self.btn_add_end.clicked.connect(lambda *args: self.add_node_by_type(NodeType.END))
        toolbar.addWidget(self.btn_add_end)

        self.btn_connect = QPushButton("🔗 Connect Selected")
        self.btn_connect.clicked.connect(lambda *args: self.connect_selected_nodes())
        toolbar.addWidget(self.btn_connect)

        self.btn_clear = QPushButton("🗑️ Clear Canvas")
        self.btn_clear.clicked.connect(lambda *args: self.clear_canvas())
        toolbar.addWidget(self.btn_clear)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("<b>Pipeline Name:</b>"))
        self.pipeline_name_edit = QLineEdit("Custom Autonomous Swarm")
        self.pipeline_name_edit.setFixedWidth(200)
        toolbar.addWidget(self.pipeline_name_edit)

        self.btn_compile = QPushButton("🚀 Compile & Register Preset")
        self.btn_compile.setProperty("class", "primary-btn")
        self.btn_compile.clicked.connect(lambda *args: self.compile_preset())
        toolbar.addWidget(self.btn_compile)

        main_layout.addLayout(toolbar)

        # Scene and View
        self.scene = QGraphicsScene(0, 0, 1800, 1000)
        self.scene.setBackgroundBrush(QBrush(QColor("#080b11")))

        self.view = InteractiveGraphicsView(self.scene)
        self.view.setStyleSheet("border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 10px; background: #080b11;")
        self.view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.view, stretch=1)

        self.add_starter_nodes()

    def add_starter_nodes(self):
        n_start = VisualAgentNode("node_start", "User Goal Input", NodeType.START, 50, 200)
        n_agent1 = VisualAgentNode("node_architect", "System Architect", NodeType.AGENT, 300, 100, system_prompt="Design structure.")
        n_memory = VisualAgentNode("node_memory", "Shared Context Memory", NodeType.MEMORY, 300, 320)
        n_agent2 = VisualAgentNode("node_coder", "Core Implementer", NodeType.AGENT, 580, 100, system_prompt="Write implementation.")
        n_end = VisualAgentNode("node_end", "Deliverable Output", NodeType.END, 860, 200)

        for n in [n_start, n_agent1, n_memory, n_agent2, n_end]:
            self.scene.addItem(n)
            self.nodes.append(n)

        # Connect them
        self.create_connection(n_start, n_agent1)
        self.create_connection(n_agent1, n_memory)
        self.create_connection(n_agent1, n_agent2)
        self.create_connection(n_agent2, n_end)

    def add_node_by_type(self, node_type: str):
        title, ok = QInputDialog.getText(self, f"Add {node_type} Node", "Enter title/label for node:")
        if not ok or not title.strip():
            title = f"{node_type} #{len(self.nodes)+1}"

        node_id = f"node_{len(self.nodes)+1}_{int(time.time())}"
        pos_x = 100 + (len(self.nodes) * 50) % 600
        pos_y = 150 + (len(self.nodes) * 40) % 400

        node = VisualAgentNode(node_id, title.strip(), node_type, pos_x, pos_y)
        self.scene.addItem(node)
        self.nodes.append(node)

    def create_connection(self, start_node: VisualAgentNode, end_node: VisualAgentNode):
        conn = VisualConnection(start_node, end_node)
        self.scene.addItem(conn)
        self.connections.append(conn)
        start_node.connections.append(conn)
        end_node.connections.append(conn)

    def connect_selected_nodes(self):
        selected = [item for item in self.scene.selectedItems() if isinstance(item, VisualAgentNode)]
        if len(selected) >= 2:
            self.create_connection(selected[0], selected[1])
        else:
            QMessageBox.information(self, "Connection Guide", "Select at least two nodes (hold Shift or drag selection) to connect them.")

    def clear_canvas(self):
        self.scene.clear()
        self.nodes.clear()
        self.connections.clear()

    def show_context_menu(self, pos):
        item = self.view.itemAt(pos)
        menu = QMenu(self)

        if isinstance(item, VisualAgentNode) or (item and isinstance(item.parentItem(), VisualAgentNode)):
            node = item if isinstance(item, VisualAgentNode) else item.parentItem()
            del_act = menu.addAction(f"🗑️ Delete Node ({node.title})")
            edit_act = menu.addAction("✏️ Edit Node Properties...")
            act = menu.exec(self.view.mapToGlobal(pos))
            if act == del_act:
                self.scene.removeItem(node)
                if node in self.nodes:
                    self.nodes.remove(node)
            elif act == edit_act:
                new_title, ok = QInputDialog.getText(self, "Edit Title", "Node Title:", text=node.title)
                if ok and new_title.strip():
                    node.title = new_title.strip()
                    node.title_item.setHtml(f"<b>[{node.node_type.upper()}]</b><br>{node.title}")
        else:
            add_s = menu.addAction("🎯 Add Start Node")
            add_a = menu.addAction("🤖 Add Agent Node")
            add_m = menu.addAction("🧠 Add Shared Memory Node")
            add_e = menu.addAction("🏁 Add End Node")
            menu.addSeparator()
            clear_act = menu.addAction("🗑️ Clear Canvas")

            act = menu.exec(self.view.mapToGlobal(pos))
            if act == add_s:
                self.add_node_by_type(NodeType.START)
            elif act == add_a:
                self.add_node_by_type(NodeType.AGENT)
            elif act == add_m:
                self.add_node_by_type(NodeType.MEMORY)
            elif act == add_e:
                self.add_node_by_type(NodeType.END)
            elif act == clear_act:
                self.clear_canvas()

    def compile_preset(self):
        pipeline_name = self.pipeline_name_edit.text().strip() or "Custom Pipeline"
        agents = [n for n in self.nodes if n.node_type == NodeType.AGENT]
        memories = [n for n in self.nodes if n.node_type == NodeType.MEMORY]

        preset_key = pipeline_name.lower().replace(" ", "_")
        PRESETS[preset_key] = {
            "name": pipeline_name,
            "type": AgentWorkflowType.AGENT_EXPERTS_FEEDBACK if memories else AgentWorkflowType.AGENT_EXPERTS,
            "description": f"Visual workflow with {len(agents)} agents and {len(memories)} shared memory context banks.",
            "icon": "🧩",
            "system_prompt": f"You are part of the '{pipeline_name}' visual pipeline.",
            "experts": [{"name": a.title, "role": a.system_prompt or "Specialist"} for a in agents],
            "max_iterations": 3
        }

        QMessageBox.information(
            self,
            "Workflow Compiled",
            f"Successfully compiled <b>{pipeline_name}</b>!<br><br>"
            f"Nodes: {len(self.nodes)} ({len(agents)} Agents, {len(memories)} Shared Contexts, {len(self.connections)} Connections).<br>"
            f"Registered into active preset key: <code>{preset_key}</code>"
        )
