"""
gui/widgets/about_dialog.py - Comprehensive Open-Source About Dialog
Balances transparency, project identity, community attribution, live web links, and licensing.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices


class AboutDialog(QDialog):
    """Modern dark-themed About Modal for Agentic Web OS."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Agentic Web OS")
        self.setFixedSize(540, 660)
        self.setStyleSheet("""
            QDialog {
                background-color: #0B0D11;
                color: #F8FAFC;
                font-family: 'Segoe UI', Inter, -apple-system, sans-serif;
            }
            QLabel#appTitle {
                font-size: 20px;
                font-weight: 800;
                color: #38BDF8;
                letter-spacing: 0.5px;
            }
            QLabel#appDesc {
                font-size: 12.5px;
                color: #94A3B8;
                line-height: 1.45;
            }
            QFrame#card {
                background-color: #141822;
                border: 1px solid #232938;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton.primaryBtn {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #38BDF8, stop:1 #818CF8);
                color: #0F172A;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton.primaryBtn:hover {
                background: #38BDF8;
            }
            QPushButton.linkBtn {
                background-color: #1A202C;
                border: 1px solid #2D3748;
                color: #F8FAFC;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11.5px;
                font-weight: 600;
            }
            QPushButton.linkBtn:hover {
                background-color: #242D3D;
                border-color: #38BDF8;
                color: #38BDF8;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # 1. Header: App Identity & Versioning
        header_row = QHBoxLayout()
        lbl_title = QLabel("🤖 Agentic Web OS")
        lbl_title.setObjectName("appTitle")
        header_row.addWidget(lbl_title)
        header_row.addStretch()

        lbl_status = QLabel("● Stable")
        lbl_status.setStyleSheet("background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 4px; padding: 2px 8px; font-size: 10px; font-weight: 700;")
        header_row.addWidget(lbl_status)
        layout.addLayout(header_row)

        ver_row = QHBoxLayout()
        ver_row.setSpacing(8)
        lbl_version = QLabel("Version 2.5.0 • Build 2026.09 • Channel: Production")
        lbl_version.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 600;")
        ver_row.addWidget(lbl_version)
        ver_row.addStretch()

        btn_updates = QPushButton("🔄 Check Updates")
        btn_updates.setProperty("class", "linkBtn")
        btn_updates.setFixedHeight(24)
        btn_updates.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/MaxMasAI/agentic-web/releases")))
        ver_row.addWidget(btn_updates)
        layout.addLayout(ver_row)

        lbl_desc = QLabel(
            "An enterprise-grade autonomous multi-agent operating system, live browser orchestration engine, "
            "and leader-worker collaborative workbench powered by Google Gemini 2.0, DeepSeek, and PySide6."
        )
        lbl_desc.setObjectName("appDesc")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        # 2. Live Web Portal Featured Banner
        web_card = QFrame()
        web_card.setObjectName("card")
        web_card.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b); border: 1px solid #0284c7; border-radius: 8px; padding: 10px;")
        web_layout = QHBoxLayout(web_card)
        web_layout.setContentsMargins(10, 8, 10, 8)
        web_layout.setSpacing(10)

        web_info = QVBoxLayout()
        web_info.setSpacing(2)
        web_title = QLabel("🌐 <b>Official Live Web Portal</b>")
        web_title.setStyleSheet("font-size: 12.5px; color: #38bdf8;")
        web_url = QLabel("<a href='https://agentic-web-self.vercel.app/' style='color: #94a3b8; text-decoration: none;'>https://agentic-web-self.vercel.app/</a>")
        web_url.setOpenExternalLinks(True)
        web_url.setStyleSheet("font-size: 11px; font-family: monospace;")
        web_info.addWidget(web_title)
        web_info.addWidget(web_url)
        web_layout.addLayout(web_info, stretch=1)

        btn_open_web = QPushButton("🚀 Open Web App")
        btn_open_web.setProperty("class", "primaryBtn")
        btn_open_web.setFixedHeight(30)
        btn_open_web.setCursor(Qt.PointingHandCursor)
        btn_open_web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://agentic-web-self.vercel.app/")))
        web_layout.addWidget(btn_open_web)

        layout.addWidget(web_card)

        # 3. Community & Repository Links Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_repo = QPushButton("⭐ GitHub Repo")
        btn_repo.setProperty("class", "linkBtn")
        btn_repo.setCursor(Qt.PointingHandCursor)
        btn_repo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/MaxMasAI/agentic-web")))

        btn_issues = QPushButton("🐞 Report Issue")
        btn_issues.setProperty("class", "linkBtn")
        btn_issues.setCursor(Qt.PointingHandCursor)
        btn_issues.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/MaxMasAI/agentic-web/issues")))

        btn_contributors = QPushButton("👥 Contributors")
        btn_contributors.setProperty("class", "linkBtn")
        btn_contributors.setCursor(Qt.PointingHandCursor)
        btn_contributors.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/MaxMasAI/agentic-web/graphs/contributors")))

        btn_layout.addWidget(btn_repo)
        btn_layout.addWidget(btn_issues)
        btn_layout.addWidget(btn_contributors)
        layout.addLayout(btn_layout)

        # 4. License & Third-Party Attribution Card
        info_card = QFrame()
        info_card.setObjectName("card")
        card_layout = QVBoxLayout(info_card)
        card_layout.setSpacing(6)

        lbl_license_title = QLabel("📜 Open Source License (MIT)")
        lbl_license_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #F8FAFC;")
        
        lbl_license_body = QLabel(
            "Released under the MIT License. Free and open for personal, academic, "
            "and commercial development with zero telemetry."
        )
        lbl_license_body.setWordWrap(True)
        lbl_license_body.setStyleSheet("font-size: 11px; color: #94A3B8; line-height: 1.4;")

        lbl_deps_title = QLabel("🧩 Core Open-Source Ecosystem")
        lbl_deps_title.setStyleSheet("font-size: 12px; font-weight: 700; color: #F8FAFC; margin-top: 4px;")

        lbl_deps_body = QLabel(
            "• <b>The Agency:</b> 287+ AI Specialists (@msitarzewski/agency-agents)\n"
            "• <b>Agent Skills:</b> Modular prompt packages (@addyosmani/agent-skills)\n"
            "• <b>Framework:</b> PySide6 / Qt6, Google GenAI SDK, SQLite, MCP Server"
        )
        lbl_deps_body.setWordWrap(True)
        lbl_deps_body.setStyleSheet("font-size: 11px; color: #94A3B8; line-height: 1.45;")

        card_layout.addWidget(lbl_license_title)
        card_layout.addWidget(lbl_license_body)
        card_layout.addWidget(lbl_deps_title)
        card_layout.addWidget(lbl_deps_body)

        layout.addWidget(info_card)

        # 5. Bottom Actions Row
        bottom_row = QHBoxLayout()
        
        lbl_copyright = QLabel("© 2026 MaxMasAI • Open Source Software")
        lbl_copyright.setStyleSheet("font-size: 10.5px; color: #475569;")
        bottom_row.addWidget(lbl_copyright)
        bottom_row.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setProperty("class", "linkBtn")
        btn_close.setFixedWidth(80)
        btn_close.clicked.connect(self.accept)
        bottom_row.addWidget(btn_close)

        layout.addLayout(bottom_row)
