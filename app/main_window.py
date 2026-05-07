"""
Main Application Window for Laptop Inspector.
Sidebar navigation with stacked page views.
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QStackedWidget, QFrame, QSizePolicy, QApplication,
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QColor, QIcon

from app.theme import (
    COLOR_BG_DARK, COLOR_BG_MAIN, COLOR_BG_HEADER, COLOR_ACCENT,
    COLOR_TEXT_LIGHT, COLOR_TEXT_SECONDARY, COLOR_BORDER,
    FONT_FAMILY, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM, FONT_SIZE_LARGE,
    SIDEBAR_WIDTH, HEADER_HEIGHT, QSS_GLOBAL,
)
from app.widgets import SidebarButton, Divider
from app.views.inspection_form import InspectionFormView
from app.views.history_view import HistoryView
import app.database as db


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laptop Inspector")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        self.setStyleSheet(QSS_GLOBAL + f"QMainWindow {{ background-color: {COLOR_BG_MAIN}; }}")

        db.initialize_database()

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        root_layout.addWidget(sidebar)

        # Right panel (header + stacked pages)
        right_panel = QWidget()
        right_panel.setStyleSheet(f"background-color: {COLOR_BG_MAIN};")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        header = self._build_header()
        right_layout.addWidget(header)

        # Stacked pages
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent;")

        self._inspection_view = InspectionFormView()
        self._history_view = HistoryView()

        self._stack.addWidget(self._inspection_view)   # index 0
        self._stack.addWidget(self._history_view)      # index 1

        right_layout.addWidget(self._stack)
        root_layout.addWidget(right_panel, stretch=1)

        # Connect signals
        self._inspection_view.inspection_saved.connect(self._on_inspection_saved)

        # Navigate to first page
        self._navigate(0)

    # ---------------------------------------------------------------- Sidebar

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"background-color: {COLOR_BG_DARK};")

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 0, 12, 16)
        layout.setSpacing(4)

        # Logo / App name
        logo_container = QWidget()
        logo_container.setFixedHeight(HEADER_HEIGHT)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(8, 0, 0, 0)
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        logo_label = QLabel("💻  Laptop Inspector")
        logo_font = QFont(FONT_FAMILY, FONT_SIZE_MEDIUM)
        logo_font.setWeight(QFont.Weight.Bold)
        logo_label.setFont(logo_font)
        logo_label.setStyleSheet("color: white;")
        logo_layout.addWidget(logo_label)
        layout.addWidget(logo_container)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #1e2d3d;")
        layout.addWidget(div)
        layout.addSpacing(8)

        # Navigation section label
        nav_label = QLabel("MAIN MENU")
        nav_label.setStyleSheet(f"""
            color: #475569;
            font-size: 8pt;
            font-weight: 700;
            font-family: "{FONT_FAMILY}";
            padding-left: 8px;
        """)
        layout.addWidget(nav_label)
        layout.addSpacing(4)

        # Nav buttons
        self._nav_buttons = []
        nav_items = [
            ("New Inspection", "🔍", 0),
            ("Inspection History", "📋", 1),
        ]

        for label, icon, index in nav_items:
            btn = SidebarButton(label, icon)
            btn.clicked.connect(lambda checked, i=index: self._navigate(i))
            layout.addWidget(btn)
            self._nav_buttons.append(btn)

        layout.addStretch()

        # Version footer
        version_label = QLabel("v1.0.0 — 2026")
        version_label.setStyleSheet(f"""
            color: #334155;
            font-size: 8pt;
            font-family: "{FONT_FAMILY}";
            padding-left: 8px;
        """)
        layout.addWidget(version_label)

        return sidebar

    # ---------------------------------------------------------------- Header

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setFixedHeight(HEADER_HEIGHT)
        header.setStyleSheet(f"""
            background-color: {COLOR_BG_HEADER};
            border-bottom: 1px solid #0f2640;
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 24, 0)

        self._header_title = QLabel("New Inspection")
        font = QFont(FONT_FAMILY, FONT_SIZE_MEDIUM)
        font.setWeight(QFont.Weight.DemiBold)
        self._header_title.setFont(font)
        self._header_title.setStyleSheet("color: white;")

        self._header_subtitle = QLabel("Scan and record hardware specs")
        self._header_subtitle.setStyleSheet(f"color: #94a3b8; font-size: {FONT_SIZE_NORMAL}pt;")

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_col.addWidget(self._header_title)
        title_col.addWidget(self._header_subtitle)

        layout.addLayout(title_col)
        layout.addStretch()

        return header

    # ------------------------------------------------------------ Navigation

    PAGE_META = {
        0: ("New Inspection", "Scan and record hardware specs"),
        1: ("Inspection History", "Browse, search and export past inspections"),
    }

    def _navigate(self, index: int):
        self._stack.setCurrentIndex(index)

        for i, btn in enumerate(self._nav_buttons):
            btn.setChecked(i == index)

        title, subtitle = self.PAGE_META.get(index, ("", ""))
        self._header_title.setText(title)
        self._header_subtitle.setText(subtitle)

        # Refresh history when switching to it
        if index == 1:
            self._history_view.refresh()

    def _on_inspection_saved(self):
        # Auto-navigate to history after save
        self._navigate(1)
