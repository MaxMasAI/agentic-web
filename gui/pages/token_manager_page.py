"""
gui/pages/token_manager_page.py - Futuristic Multi-Model Token Manager & Free Quotas Dashboard.

Displays lifetime token consumption ('till today'), today's daily free-tier usage across models,
countdown timer to midnight UTC quota resets, and interactive visual charts.
"""

import math
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QProgressBar, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QLinearGradient,
    QPainterPath, QCursor
)

from services.token_manager import get_token_manager, MODEL_QUOTAS_CATALOG


class DailyTrendChartWidget(QWidget):
    """
    Custom-painted 7-day token consumption bar & trend curve chart using QPainter.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.history_data: List[Dict[str, Any]] = []

    def set_data(self, data: List[Dict[str, Any]]):
        self.history_data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background Frame
        bg_rect = QRectF(0, 0, w, h)
        painter.fillRect(bg_rect, QColor(11, 17, 32, 220))
        painter.setPen(QPen(QColor(56, 189, 248, 40), 1))
        painter.drawRoundedRect(bg_rect.adjusted(1, 1, -1, -1), 8, 8)

        if not self.history_data:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(bg_rect, Qt.AlignCenter, "No token transaction history yet.")
            return

        margin_left = 60
        margin_right = 30
        margin_top = 35
        margin_bottom = 35

        plot_w = w - margin_left - margin_right
        plot_h = h - margin_top - margin_bottom

        # Max token value for scaling
        max_val = max([d["total_tokens"] for d in self.history_data] + [10000])
        # Round max_val up to nice ceiling
        ceil_val = math.ceil(max_val * 1.15)

        # Draw Grid Lines & Y-axis labels
        painter.setFont(QFont("Segoe UI", 8))
        for i in range(4):
            y = margin_top + (plot_h / 3) * i
            val = int(ceil_val * (1 - i / 3))
            val_str = f"{val/1000:.0f}k" if val >= 1000 else str(val)

            painter.setPen(QPen(QColor(148, 163, 184, 40), 1, Qt.DashLine))
            painter.drawLine(int(margin_left), int(y), int(w - margin_right), int(y))

            painter.setPen(QColor("#64748b"))
            painter.drawText(QRectF(5, y - 10, margin_left - 15, 20), Qt.AlignRight | Qt.AlignVCenter, val_str)

        # Draw Bars & Trend Line
        n = len(self.history_data)
        slot_w = plot_w / n
        bar_w = min(42.0, slot_w * 0.55)

        points = []
        for i, d in enumerate(self.history_data):
            val = d["total_tokens"]
            bar_h = (val / ceil_val) * plot_h
            bx = margin_left + (i * slot_w) + (slot_w - bar_w) / 2
            by = margin_top + plot_h - bar_h

            # Bar Gradient
            grad = QLinearGradient(bx, by, bx, by + bar_h)
            grad.setColorAt(0.0, QColor("#38bdf8"))
            grad.setColorAt(1.0, QColor("#0369a1"))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(bx, by, bar_w, bar_h), 4, 4)

            # Center point for line graph overlay
            cx = bx + bar_w / 2
            points.append(QPointF(cx, by))

            # Value text above bar
            if val > 0:
                painter.setPen(QColor("#e2e8f0"))
                v_text = f"{val/1000:.0f}k" if val >= 1000 else str(val)
                painter.drawText(QRectF(bx - 10, by - 18, bar_w + 20, 16), Qt.AlignCenter, v_text)

            # X-axis label
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(QRectF(bx - 15, h - margin_bottom + 6, bar_w + 30, 20), Qt.AlignCenter, d.get("label", d["date"]))

        # Draw smooth line connecting peaks
        if len(points) > 1:
            painter.setPen(QPen(QColor("#38bdf8"), 2))
            painter.setBrush(Qt.NoBrush)
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])

            # Draw glowing dots on vertices
            for pt in points:
                painter.setPen(QPen(QColor("#ffffff"), 2))
                painter.setBrush(QColor("#0284c7"))
                painter.drawEllipse(pt, 3.5, 3.5)


class ModelDistributionDonutWidget(QWidget):
    """
    Custom-painted Donut / Pie distribution chart showing token share per model.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        self.distribution: List[Dict[str, Any]] = []

    def set_data(self, data: List[Dict[str, Any]]):
        self.distribution = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background Frame
        bg_rect = QRectF(0, 0, w, h)
        painter.fillRect(bg_rect, QColor(11, 17, 32, 220))
        painter.setPen(QPen(QColor(56, 189, 248, 40), 1))
        painter.drawRoundedRect(bg_rect.adjusted(1, 1, -1, -1), 8, 8)

        if not self.distribution:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(bg_rect, Qt.AlignCenter, "No distribution data available.")
            return

        # Donut dimensions
        center_x = 100
        center_y = h / 2
        radius = min(75, h / 2 - 20)
        inner_radius = radius * 0.58

        outer_rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)

        start_angle = 90 * 16
        for item in self.distribution:
            span_angle = int((item["percent"] / 100.0) * 360 * 16)
            col = QColor(item.get("color", "#38bdf8"))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(col))
            painter.drawPie(outer_rect, start_angle, span_angle)
            start_angle += span_angle

        # Cut out center to create Donut
        inner_rect = QRectF(center_x - inner_radius, center_y - inner_radius, inner_radius * 2, inner_radius * 2)
        painter.setBrush(QBrush(QColor(11, 17, 32)))
        painter.drawEllipse(inner_rect)

        # Center label
        painter.setPen(QColor("#f8fafc"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(inner_rect, Qt.AlignCenter, "MODELS")

        # Legend on the right side
        legend_x = 210
        legend_y = 25
        painter.setFont(QFont("Segoe UI", 8.5))

        for i, item in enumerate(self.distribution[:6]):
            ly = legend_y + (i * 26)
            col = QColor(item.get("color", "#38bdf8"))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(col))
            painter.drawRoundedRect(QRectF(legend_x, ly + 2, 12, 12), 3, 3)

            painter.setPen(QColor("#f1f5f9"))
            name = item["provider"]
            tok_k = f"{item['tokens']/1000:.0f}k" if item["tokens"] >= 1000 else str(item["tokens"])
            painter.drawText(QRectF(legend_x + 20, ly, w - legend_x - 25, 18), Qt.AlignLeft | Qt.AlignVCenter, f"{name}: {item['percent']}% ({tok_k})")


class TokenManagerPage(QWidget):
    """
    Main Multi-Model Token Manager & Daily Quota Console Page.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mgr = get_token_manager()
        self.init_ui()

        # 1-second timer for live countdown and metrics refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_countdown_and_live_ticks)
        self.refresh_timer.start(1000)

    def init_ui(self):
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(12, 12, 12, 12)
        root_lay.setSpacing(12)

        # Scroll Area for Full Content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        container = QWidget()
        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(4, 4, 4, 4)
        self.main_layout.setSpacing(14)

        # ── 1. Page Header ────────────────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: rgba(15, 23, 42, 0.7);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        h_lay = QHBoxLayout(header_frame)
        h_lay.setContentsMargins(12, 8, 12, 8)

        t_box = QVBoxLayout()
        t_box.setSpacing(2)
        lbl_title = QLabel("💎 Multi-Model Token Manager & Free Daily Quotas")
        lbl_title.setStyleSheet("font-size: 20px; font-weight: 800; color: #38bdf8; letter-spacing: 0.5px;")
        t_box.addWidget(lbl_title)

        lbl_sub = QLabel("Real-time token telemetry, cumulative lifetime metrics ('till today'), model free-tier quotas, and midnight UTC reset tracking.")
        lbl_sub.setStyleSheet("font-size: 11.5px; color: #94a3b8;")
        t_box.addWidget(lbl_sub)
        h_lay.addLayout(t_box, stretch=1)

        # Action Buttons
        btn_sim = QPushButton("⚡ Simulate API Request")
        btn_sim.setCursor(QCursor(Qt.PointingHandCursor))
        btn_sim.setStyleSheet("background: rgba(124, 58, 237, 0.8); color: white; border-radius: 6px; padding: 6px 14px; font-weight: bold;")
        btn_sim.clicked.connect(self.simulate_request)
        h_lay.addWidget(btn_sim)

        btn_export = QPushButton("📥 Export CSV")
        btn_export.setCursor(QCursor(Qt.PointingHandCursor))
        btn_export.setStyleSheet("background: rgba(30, 41, 59, 0.9); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); border-radius: 6px; padding: 6px 14px; font-weight: 600;")
        btn_export.clicked.connect(self.export_csv)
        h_lay.addWidget(btn_export)

        btn_refresh = QPushButton("🔄 Refresh")
        btn_refresh.setCursor(QCursor(Qt.PointingHandCursor))
        btn_refresh.setStyleSheet("background: #0284c7; color: white; border-radius: 6px; padding: 6px 14px; font-weight: bold;")
        btn_refresh.clicked.connect(self.refresh_data)
        h_lay.addWidget(btn_refresh)

        self.main_layout.addWidget(header_frame)

        # ── 2. Top 4 Metric Telemetry Cards ───────────────────────────────────
        self.metrics_layout = QGridLayout()
        self.metrics_layout.setSpacing(10)

        self.card_lifetime = self._create_metric_card("💎 TOTAL TOKENS (TILL TODAY)", "0 Tokens", "Prompt: 0 · Completion: 0", "#38bdf8")
        self.card_today = self._create_metric_card("⚡ TOKENS USED TODAY", "0 / 1B", "0% of Daily Free Allowance", "#10b981")
        self.card_saved = self._create_metric_card("💰 ESTIMATED VALUE SAVED", "$0.00 Saved", "Via Free Tier Credits & Quotas", "#f59e0b")
        self.card_reset = self._create_metric_card("⏳ DAILY QUOTA RESET IN", "00h 00m 00s", "Resets at 00:00:00 UTC", "#8b5cf6")

        self.metrics_layout.addWidget(self.card_lifetime, 0, 0)
        self.metrics_layout.addWidget(self.card_today, 0, 1)
        self.metrics_layout.addWidget(self.card_saved, 0, 2)
        self.metrics_layout.addWidget(self.card_reset, 0, 3)

        self.main_layout.addLayout(self.metrics_layout)

        # ── 3. Visual Charts Section ──────────────────────────────────────────
        charts_box = QHBoxLayout()
        charts_box.setSpacing(12)

        # Daily Trend Chart Frame
        trend_frame = QFrame()
        trend_frame.setStyleSheet("background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 8px; padding: 10px;")
        t_lay = QVBoxLayout(trend_frame)
        t_lay.setContentsMargins(10, 8, 10, 8)
        lbl_t = QLabel("📊 <b>7-Day Token Consumption Trend</b>")
        lbl_t.setStyleSheet("color: #38bdf8; font-size: 13px;")
        t_lay.addWidget(lbl_t)
        self.chart_trend = DailyTrendChartWidget()
        t_lay.addWidget(self.chart_trend)
        charts_box.addWidget(trend_frame, stretch=3)

        # Model Distribution Donut Frame
        dist_frame = QFrame()
        dist_frame.setStyleSheet("background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.15); border-radius: 8px; padding: 10px;")
        d_lay = QVBoxLayout(dist_frame)
        d_lay.setContentsMargins(10, 8, 10, 8)
        lbl_d = QLabel("🍩 <b>Model & Provider Share</b>")
        lbl_d.setStyleSheet("color: #38bdf8; font-size: 13px;")
        d_lay.addWidget(lbl_d)
        self.chart_donut = ModelDistributionDonutWidget()
        d_lay.addWidget(self.chart_donut)
        charts_box.addWidget(dist_frame, stretch=2)

        self.main_layout.addLayout(charts_box)

        # ── 4. Model Free Quotas & Allowances Grid ────────────────────────────
        quota_header = QLabel("🤖 <b>Provider Free Daily Quotas & Rate Limits</b>")
        quota_header.setStyleSheet("font-size: 14px; color: #f1f5f9; margin-top: 4px;")
        self.main_layout.addWidget(quota_header)

        self.quotas_grid = QGridLayout()
        self.quotas_grid.setSpacing(10)
        self.main_layout.addLayout(self.quotas_grid)

        # ── 5. Granular Transaction Ledger Table ──────────────────────────────
        table_header = QLabel("📋 <b>Recent Token Ledger Transactions</b>")
        table_header.setStyleSheet("font-size: 14px; color: #f1f5f9; margin-top: 6px;")
        self.main_layout.addWidget(table_header)

        self.table_tx = QTableWidget()
        self.table_tx.setColumnCount(8)
        self.table_tx.setHorizontalHeaderLabels([
            "Time (UTC)", "Provider", "Model", "Prompt Tokens",
            "Completion Tokens", "Total Tokens", "Est. Cost ($)", "Task ID"
        ])
        self.table_tx.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_tx.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_tx.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table_tx.setMinimumHeight(240)
        self.table_tx.setStyleSheet("""
            QTableWidget {
                background: rgba(11, 17, 32, 0.9);
                color: #e2e8f0;
                gridline-color: rgba(56, 189, 248, 0.1);
                border: 1px solid rgba(56, 189, 248, 0.2);
                border-radius: 8px;
            }
            QHeaderView::section {
                background: #0f172a;
                color: #38bdf8;
                font-weight: bold;
                border: 1px solid rgba(56, 189, 248, 0.15);
                padding: 6px;
            }
        """)
        self.main_layout.addWidget(self.table_tx)

        scroll.setWidget(container)
        root_lay.addWidget(scroll)

        self.refresh_data()

    def _create_metric_card(self, title: str, main_val: str, sub_val: str, accent_color: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid {accent_color}40;
                border-left: 4px solid {accent_color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(3)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {accent_color}; letter-spacing: 0.8px;")
        lay.addWidget(lbl_t)

        lbl_m = QLabel(main_val)
        lbl_m.setObjectName("main_val")
        lbl_m.setStyleSheet("font-size: 19px; font-weight: 800; color: #f8fafc;")
        lay.addWidget(lbl_m)

        lbl_s = QLabel(sub_val)
        lbl_s.setObjectName("sub_val")
        lbl_s.setStyleSheet("font-size: 10.5px; color: #94a3b8;")
        lay.addWidget(lbl_s)
        return card

    def refresh_data(self):
        """Reloads all metrics from SQLite WAL state store."""
        lifetime = self.mgr.get_lifetime_summary()
        today = self.mgr.get_today_summary()
        history = self.mgr.get_daily_history(days=7)
        dist = self.mgr.get_model_distribution()
        statuses = self.mgr.get_all_model_statuses()
        txs = self.mgr.get_recent_transactions(limit=30)

        # 1. Update Metric Cards
        tot_tok = lifetime["total_tokens"]
        tot_str = f"{tot_tok:,} Tokens"
        p_tok = lifetime["total_prompt_tokens"]
        c_tok = lifetime["total_completion_tokens"]
        sub_str = f"Prompt: {p_tok:,} · Completion: {c_tok:,}"
        self._update_card_text(self.card_lifetime, tot_str, sub_str)

        today_tok = today["today_tokens"]
        lim = today["combined_daily_limit"]
        lim_str = f"{lim/1_000_000_000:.1f}B" if lim >= 1_000_000_000 else f"{lim/1_000_000:.0f}M"
        self._update_card_text(
            self.card_today,
            f"{today_tok:,} / {lim_str}",
            f"{today['usage_percent']}% of Combined Daily Quotas"
        )

        self._update_card_text(
            self.card_saved,
            f"${lifetime['total_saved_usd']:.2f} USD Saved",
            f"Today: ${today['today_saved_usd']:.2f} · Lifetime Total"
        )

        # 2. Update Charts
        self.chart_trend.set_data(history)
        self.chart_donut.set_data(dist)

        # 3. Update Model Quotas Grid
        self._render_quotas_grid(statuses)

        # 4. Update Transactions Table
        self._render_transactions_table(txs)

        self.update_countdown_and_live_ticks()

    def _update_card_text(self, card: QFrame, main_val: str, sub_val: str):
        lbl_m = card.findChild(QLabel, "main_val")
        lbl_s = card.findChild(QLabel, "sub_val")
        if lbl_m:
            lbl_m.setText(main_val)
        if lbl_s:
            lbl_s.setText(sub_val)

    def update_countdown_and_live_ticks(self):
        """Calculates live countdown until midnight UTC reset."""
        sec = self.mgr.get_seconds_until_midnight_utc()
        hrs = sec // 3600
        mins = (sec % 3600) // 60
        secs = sec % 60
        time_str = f"{hrs:02d}h {mins:02d}m {secs:02d}s"
        self._update_card_text(self.card_reset, time_str, "Resets daily at 00:00:00 UTC")

    def _render_quotas_grid(self, statuses: List[Dict[str, Any]]):
        # Clear existing items in grid
        while self.quotas_grid.count():
            item = self.quotas_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cols = 2
        for i, s in enumerate(statuses):
            row = i // cols
            col = i % cols

            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: rgba(15, 23, 42, 0.7);
                    border: 1px solid rgba(56, 189, 248, 0.15);
                    border-radius: 8px;
                    padding: 8px;
                }}
            """)
            c_lay = QVBoxLayout(card)
            c_lay.setContentsMargins(10, 8, 10, 8)
            c_lay.setSpacing(6)

            # Top Row: Icon, Name, Health Badge
            top_h = QHBoxLayout()
            lbl_name = QLabel(f"{s['icon']} <b>{s['provider']}</b> ({s['model_name']})")
            lbl_name.setStyleSheet(f"font-size: 12.5px; color: {s['color']};")
            top_h.addWidget(lbl_name, stretch=1)

            lbl_badge = QLabel(f" {s['health']} ")
            lbl_badge.setStyleSheet(f"background: rgba(15, 23, 42, 0.9); color: {s['health_color']}; border: 1px solid {s['health_color']}; border-radius: 4px; font-weight: bold; font-size: 10px; padding: 2px 6px;")
            top_h.addWidget(lbl_badge)
            c_lay.addLayout(top_h)

            # Middle Stats Row
            lim_val = s['daily_limit']
            lim_fmt = f"{lim_val/1_000_000_000:.1f}B" if lim_val >= 1_000_000_000 else f"{lim_val/1_000_000:.1f}M" if lim_val >= 1_000_000 else f"{lim_val:,}"

            lbl_stats = QLabel(f"Used Today: <b>{s['used_today']:,}</b> / {lim_fmt} tokens ({s['usage_percent']}%) · Remaining: <b>{s['remaining_today']:,}</b>")
            lbl_stats.setStyleSheet("font-size: 11px; color: #cbd5e1;")
            c_lay.addWidget(lbl_stats)

            # Progress Bar
            pbar = QProgressBar()
            pbar.setFixedHeight(6)
            pbar.setTextVisible(False)
            pbar.setRange(0, 100)
            pbar.setValue(min(100, int(s["usage_percent"])))
            bar_col = s["health_color"]
            pbar.setStyleSheet(f"""
                QProgressBar {{
                    background: rgba(30, 41, 59, 0.8);
                    border: none;
                    border-radius: 3px;
                }}
                QProgressBar::chunk {{
                    background: {bar_col};
                    border-radius: 3px;
                }}
            """)
            c_lay.addWidget(pbar)

            # Footer Limits Specs
            lbl_limits = QLabel(f"Rate Limits: <b>{s['rpm_limit']} RPM</b> · <b>{s['tpm_limit']:,} TPM</b> · <b>{s['requests_limit']} RPD</b> | <i>{s['tier_type']}</i>")
            lbl_limits.setStyleSheet("font-size: 9.5px; color: #64748b;")
            c_lay.addWidget(lbl_limits)

            self.quotas_grid.addWidget(card, row, col)

    def _render_transactions_table(self, txs: List[Dict[str, Any]]):
        self.table_tx.setRowCount(len(txs))
        for r, tx in enumerate(txs):
            self.table_tx.setItem(r, 0, QTableWidgetItem(f"{tx['time']}"))
            self.table_tx.setItem(r, 1, QTableWidgetItem(f"{tx['provider']}"))
            self.table_tx.setItem(r, 2, QTableWidgetItem(f"{tx['model']}"))
            self.table_tx.setItem(r, 3, QTableWidgetItem(f"{tx['prompt_tokens']:,}"))
            self.table_tx.setItem(r, 4, QTableWidgetItem(f"{tx['completion_tokens']:,}"))
            self.table_tx.setItem(r, 5, QTableWidgetItem(f"{tx['total_tokens']:,}"))
            self.table_tx.setItem(r, 6, QTableWidgetItem(f"${tx['cost_usd']:.4f}"))
            self.table_tx.setItem(r, 7, QTableWidgetItem(f"{tx['task_id']}"))

    def simulate_request(self):
        """Simulates an AI model call with prompt & completion token consumption."""
        import random
        providers_list = [
            ("Google Gemini", "gemini-2.0-flash", 12000, 4500),
            ("DeepSeek", "deepseek-v3", 8500, 3200),
            ("Anthropic Claude", "claude-3.5-sonnet", 4200, 1800),
            ("OpenAI ChatGPT", "gpt-4o-mini", 6000, 2400),
            ("Groq Cloud", "groq-llama-3.3", 9500, 3800),
            ("OpenRouter", "openrouter-free", 14000, 6000),
        ]
        prov, mod, p_base, c_base = random.choice(providers_list)
        p_tok = p_base + random.randint(-1500, 3000)
        c_tok = c_base + random.randint(-800, 1500)

        res = self.mgr.record_usage(
            provider=prov,
            model=mod,
            prompt_tokens=p_tok,
            completion_tokens=c_tok,
            task_id=f"sim-{int(time.time())}"
        )
        self.refresh_data()
        QMessageBox.information(
            self,
            "⚡ Token Event Logged",
            f"Simulated live model invocation:\n\n"
            f"• Provider: {prov}\n"
            f"• Model: {mod}\n"
            f"• Prompt Tokens: {p_tok:,}\n"
            f"• Completion Tokens: {c_tok:,}\n"
            f"• Total Logged: {res['total_tokens']:,} tokens"
        )

    def export_csv(self):
        """Exports full token ledger history to a CSV file."""
        path, _ = QFileDialog.getSaveFileName(self, "Export Token History CSV", "token_usage_report.csv", "CSV Files (*.csv)")
        if not path:
            return
        txs = self.mgr.get_recent_transactions(limit=1000)
        try:
            import csv
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Time", "Provider", "Model", "Prompt Tokens", "Completion Tokens", "Total Tokens", "Est Cost USD", "Task ID"])
                for t in txs:
                    writer.writerow([t["id"], t["date"], t["time"], t["provider"], t["model"], t["prompt_tokens"], t["completion_tokens"], t["total_tokens"], t["cost_usd"], t["task_id"]])
            QMessageBox.information(self, "Export Complete", f"Successfully exported {len(txs)} token transactions to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export CSV: {str(e)}")
