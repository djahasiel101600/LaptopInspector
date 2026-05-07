"""
History View — DataGrid of all past inspections with search, filter, and export.
"""

import os
from typing import List, Dict, Any, Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QFrame, QAbstractItemView,
    QMessageBox, QFileDialog, QMenu, QDialog, QScrollArea,
    QGridLayout, QApplication,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush, QCursor

from app.theme import (
    COLOR_BG_MAIN, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_BORDER,
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
    FONT_SIZE_LARGE, STATUS_COLORS, STATUS_BG_COLORS,
)
from app.widgets import (
    Card, SectionTitle, FieldLabel, StyledLineEdit, StyledComboBox,
    PrimaryButton, SecondaryButton, DangerButton, StatusBadge,
    Divider, StatCard, drop_shadow,
)
import app.database as db
from app.exporter import export_to_csv, export_to_pdf


# ---------------------------------------------------------------------------
# Detail dialog
# ---------------------------------------------------------------------------

class InspectionDetailDialog(QDialog):
    def __init__(self, record: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Inspection — {record.get('report_number', '')}")
        self.setMinimumSize(640, 520)
        self.setModal(True)
        self._record = record
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)

        # Title row
        hdr = QHBoxLayout()
        title = QLabel(self._record.get("report_number", ""))
        title_font = QFont(FONT_FAMILY, FONT_SIZE_MEDIUM)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        hdr.addWidget(title)
        hdr.addStretch()
        badge = StatusBadge(self._record.get("status", "N/A"))
        hdr.addWidget(badge)
        root.addLayout(hdr)
        root.addWidget(Divider())

        # Scrollable content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)
        scroll.setWidget(content)
        root.addWidget(scroll)

        # Metadata
        meta_card = Card(shadow=False)
        meta_layout = QGridLayout(meta_card)
        meta_layout.setContentsMargins(16, 12, 16, 12)
        meta_layout.setHorizontalSpacing(16)
        meta_layout.setVerticalSpacing(8)

        meta_fields = [
            ("PO Number", "po_number"), ("Inspection Date", "inspection_date"),
            ("End User", "end_user"), ("Agency", "agency"),
            ("Office / Unit", "office_unit"), ("Serial Number", "hardware_serial"),
        ]
        for i, (label, key) in enumerate(meta_fields):
            row, col = divmod(i, 2)
            lbl = FieldLabel(label)
            val = QLabel(str(self._record.get(key, "N/A") or "N/A"))
            val.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: {FONT_SIZE_NORMAL}pt;")
            col_base = col * 2
            meta_layout.addWidget(lbl, row, col_base)
            meta_layout.addWidget(val, row, col_base + 1)

        content_layout.addWidget(meta_card)

        # Hardware specs
        specs = self._record.get("hardware_specs", {})
        if specs:
            content_layout.addWidget(SectionTitle("Hardware Specifications"))
            spec_card = Card(shadow=False)
            spec_grid = QGridLayout(spec_card)
            spec_grid.setContentsMargins(16, 12, 16, 12)
            spec_grid.setHorizontalSpacing(16)
            spec_grid.setVerticalSpacing(6)

            display_specs = [
                ("CPU", specs.get("cpu_model", "N/A")),
                ("RAM", f"{specs.get('ram_total_gb', 'N/A')} GB"),
                ("GPU", specs.get("gpu_model", "N/A")),
                ("GPU VRAM", specs.get("gpu_vram", "N/A")),
                ("Screen", specs.get("screen_resolution", "N/A")),
                ("OS", specs.get("os", "N/A")),
                ("BIOS UUID", specs.get("bios_uuid", "N/A")),
                ("MB Serial", specs.get("motherboard_serial", "N/A")),
                ("Uptime", specs.get("system_uptime", "N/A")),
            ]
            for i, (label, value) in enumerate(display_specs):
                row, col = divmod(i, 2)
                lbl = FieldLabel(label)
                val = QLabel(str(value))
                val.setWordWrap(True)
                val.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: {FONT_SIZE_SMALL}pt;")
                col_base = col * 2
                spec_grid.addWidget(lbl, row, col_base)
                spec_grid.addWidget(val, row, col_base + 1)

            content_layout.addWidget(spec_card)

        # Notes
        notes = self._record.get("notes", "").strip()
        if notes:
            content_layout.addWidget(SectionTitle("Notes"))
            notes_lbl = QLabel(notes)
            notes_lbl.setWordWrap(True)
            notes_lbl.setStyleSheet(f"""
                background: #f8fafc;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 8px 12px;
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE_NORMAL}pt;
            """)
            content_layout.addWidget(notes_lbl)

        content_layout.addStretch()

        # Export PDF button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        export_btn = SecondaryButton("Export PDF", "⬇")
        export_btn.clicked.connect(self._export_pdf)
        btn_row.addWidget(export_btn)
        close_btn = PrimaryButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _export_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", f"{self._record.get('report_number', 'report')}.pdf",
            "PDF Files (*.pdf)"
        )
        if path:
            try:
                export_to_pdf(self._record, path)
                QMessageBox.information(self, "Exported", f"PDF saved to:\n{path}")
            except Exception as exc:
                QMessageBox.critical(self, "Export Error", str(exc))


# ---------------------------------------------------------------------------
# History View
# ---------------------------------------------------------------------------

class HistoryView(QWidget):
    COLUMNS = ["Report #", "PO Number", "Date", "End User", "Agency", "Status"]
    COL_WIDTHS = [130, 120, 150, 150, 150, 90]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: List[Dict[str, Any]] = []
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Inspection History")
        title_font = QFont(FONT_FAMILY, FONT_SIZE_LARGE)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        hdr.addWidget(title)
        hdr.addStretch()
        export_csv_btn = SecondaryButton("Export CSV", "⬇")
        export_csv_btn.clicked.connect(self._export_csv)
        hdr.addWidget(export_csv_btn)
        root.addLayout(hdr)

        # Stats row
        self._stat_total = StatCard("Total Inspections", "0", COLOR_ACCENT)
        self._stat_pass = StatCard("Passed", "0", COLOR_SUCCESS)
        self._stat_fail = StatCard("Failed", "0", COLOR_DANGER)
        self._stat_warn = StatCard("Warnings", "0", COLOR_WARNING)

        stats_row = QHBoxLayout()
        stats_row.setSpacing(12)
        for card in (self._stat_total, self._stat_pass, self._stat_fail, self._stat_warn):
            stats_row.addWidget(card)
        root.addLayout(stats_row)

        # Filters
        filter_card = Card()
        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(16, 10, 16, 10)
        filter_layout.setSpacing(10)

        search_lbl = FieldLabel("Search:")
        self._search_edit = StyledLineEdit("Report #, PO, User, Agency…")
        self._search_edit.setMinimumWidth(250)
        self._search_edit.textChanged.connect(self._refresh_table)

        status_lbl = FieldLabel("Status:")
        self._status_combo = StyledComboBox()
        self._status_combo.addItems(["All", "PASS", "FAIL", "WARNING"])
        self._status_combo.setFixedWidth(110)
        self._status_combo.currentTextChanged.connect(self._refresh_table)

        refresh_btn = SecondaryButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_table)

        filter_layout.addWidget(search_lbl)
        filter_layout.addWidget(self._search_edit)
        filter_layout.addWidget(status_lbl)
        filter_layout.addWidget(self._status_combo)
        filter_layout.addStretch()
        filter_layout.addWidget(refresh_btn)
        root.addWidget(filter_card)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.horizontalHeader().setStretchLastSection(False)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        self._table.doubleClicked.connect(self._open_detail)
        self._table.setSortingEnabled(True)

        for i, w in enumerate(self.COL_WIDTHS):
            self._table.setColumnWidth(i, w)
        self._table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch
        )

        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLOR_BG_CARD};
                border: 1px solid {COLOR_BORDER};
                border-radius: 8px;
                gridline-color: transparent;
                outline: none;
                font-size: {FONT_SIZE_NORMAL}pt;
                font-family: "{FONT_FAMILY}";
            }}
            QTableWidget::item {{
                padding: 8px 12px;
                color: {COLOR_TEXT_PRIMARY};
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: #eff6ff;
                color: {COLOR_TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: #f8fafc;
                color: {COLOR_TEXT_SECONDARY};
                font-weight: 600;
                font-size: {FONT_SIZE_SMALL}pt;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid {COLOR_BORDER};
            }}
            QTableWidget::item:alternate {{
                background-color: #f8fafc;
            }}
        """)
        drop_shadow(self._table, blur=8)
        root.addWidget(self._table)

        # Status bar
        self._status_bar = QLabel("0 records")
        self._status_bar.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: {FONT_SIZE_SMALL}pt;")
        root.addWidget(self._status_bar)

    # ---------------------------------------------------------- Data Loading --

    def refresh(self):
        """Public method to reload data from database."""
        self._refresh_table()

    def _refresh_table(self):
        search = self._search_edit.text().strip()
        status_filter = self._status_combo.currentText()
        self._records = db.get_all_inspections(search=search, status_filter=status_filter)
        self._populate_table()
        self._update_stats()

    def _populate_table(self):
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        for record in self._records:
            row = self._table.rowCount()
            self._table.insertRow(row)

            # Store record id in first column
            report_item = QTableWidgetItem(record.get("report_number", ""))
            report_item.setData(Qt.ItemDataRole.UserRole, record.get("id"))
            self._table.setItem(row, 0, report_item)

            self._table.setItem(row, 1, QTableWidgetItem(record.get("po_number", "")))

            date_str = str(record.get("inspection_date", ""))[:19]
            self._table.setItem(row, 2, QTableWidgetItem(date_str))
            self._table.setItem(row, 3, QTableWidgetItem(record.get("end_user", "")))
            self._table.setItem(row, 4, QTableWidgetItem(record.get("agency", "")))

            # Status cell with color
            status = record.get("status", "N/A")
            status_item = QTableWidgetItem(status)
            fg = QColor(STATUS_COLORS.get(status, COLOR_TEXT_SECONDARY))
            bg = QColor(STATUS_BG_COLORS.get(status, "#f1f5f9"))
            status_item.setForeground(QBrush(fg))
            status_item.setBackground(QBrush(bg))
            font = QFont(FONT_FAMILY, FONT_SIZE_SMALL)
            font.setWeight(QFont.Weight.Bold)
            status_item.setFont(font)
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 5, status_item)

            self._table.setRowHeight(row, 42)

        self._table.setSortingEnabled(True)
        self._status_bar.setText(f"{len(self._records)} record{'s' if len(self._records) != 1 else ''}")

    def _update_stats(self):
        stats = db.get_stats()
        self._stat_total.update_value(str(stats["total"]))
        self._stat_pass.update_value(str(stats["passed"]))
        self._stat_fail.update_value(str(stats["failed"]))
        self._stat_warn.update_value(str(stats["warning"]))

    # -------------------------------------------------------- Context Menu --

    def _show_context_menu(self, pos):
        row = self._table.rowAt(pos.y())
        if row < 0:
            return

        record = self._get_record_at_row(row)
        if not record:
            return

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: white;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 20px;
                border-radius: 4px;
                font-size: {FONT_SIZE_NORMAL}pt;
            }}
            QMenu::item:selected {{
                background-color: #eff6ff;
                color: {COLOR_ACCENT};
            }}
        """)

        view_action = menu.addAction("View Details")
        export_pdf_action = menu.addAction("Export as PDF")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        delete_action.setIcon(menu.style().standardIcon(
            menu.style().StandardPixmap.SP_TrashIcon
        ))

        action = menu.exec(self._table.viewport().mapToGlobal(pos))
        if action == view_action:
            self._open_detail_for_record(record)
        elif action == export_pdf_action:
            self._export_pdf_for_record(record)
        elif action == delete_action:
            self._delete_record(record)

    def _open_detail(self, index):
        row = index.row()
        record = self._get_record_at_row(row)
        if record:
            self._open_detail_for_record(record)

    def _get_record_at_row(self, row: int) -> Optional[Dict[str, Any]]:
        item = self._table.item(row, 0)
        if item is None:
            return None
        record_id = item.data(Qt.ItemDataRole.UserRole)
        return db.get_inspection_by_id(record_id)

    def _open_detail_for_record(self, record: Dict[str, Any]):
        dlg = InspectionDetailDialog(record, self)
        dlg.exec()

    def _export_pdf_for_record(self, record: Dict[str, Any]):
        default_name = f"{record.get('report_number', 'report')}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", default_name, "PDF Files (*.pdf)"
        )
        if path:
            try:
                export_to_pdf(record, path)
                QMessageBox.information(self, "Exported", f"PDF saved to:\n{path}")
            except Exception as exc:
                QMessageBox.critical(self, "Export Error", str(exc))

    def _delete_record(self, record: Dict[str, Any]):
        reply = QMessageBox.question(
            self, "Delete Inspection",
            f"Delete inspection {record.get('report_number', '')}?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_inspection(record["id"])
            self._refresh_table()

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "inspections.csv", "CSV Files (*.csv)"
        )
        if path:
            try:
                records = db.get_all_inspections(
                    search=self._search_edit.text().strip(),
                    status_filter=self._status_combo.currentText(),
                )
                export_to_csv(records, path)
                QMessageBox.information(self, "Exported", f"CSV saved to:\n{path}")
            except Exception as exc:
                QMessageBox.critical(self, "Export Error", str(exc))
