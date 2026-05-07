"""
Inspection Form View — New inspection workflow.
"""

import threading
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QFormLayout, QFrame, QSizePolicy, QMessageBox, QProgressBar,
    QGridLayout, QSpacerItem,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt6.QtGui import QFont, QColor

from app.theme import (
    COLOR_BG_MAIN, COLOR_BG_CARD, COLOR_TEXT_PRIMARY, COLOR_TEXT_SECONDARY,
    COLOR_ACCENT, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_BORDER,
    FONT_FAMILY, FONT_SIZE_SMALL, FONT_SIZE_NORMAL, FONT_SIZE_MEDIUM,
    FONT_SIZE_LARGE, STATUS_COLORS, STATUS_BG_COLORS,
)
from app.widgets import (
    Card, SectionTitle, FieldLabel, StyledLineEdit, StyledTextEdit,
    PrimaryButton, SecondaryButton, StatusBadge, Divider, drop_shadow,
)
import app.database as db
import app.hardware as hw
from app.comparator import compare_specs


# ---------------------------------------------------------------------------
# Background worker for hardware collection
# ---------------------------------------------------------------------------

class HardwareWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def run(self):
        try:
            specs = hw.collect_all_specs()
            self.finished.emit(specs)
        except Exception as exc:
            self.error.emit(str(exc))


# ---------------------------------------------------------------------------
# Spec row widget (field + PASS/FAIL badge + messages)
# ---------------------------------------------------------------------------

class CompareResultRow(QFrame):
    def __init__(self, field_name: str, expected: str, actual: str,
                 status: str, message: str, parent=None):
        super().__init__(parent)
        self.setObjectName("CompareRow")
        fg = STATUS_COLORS.get(status, COLOR_TEXT_SECONDARY)
        bg = STATUS_BG_COLORS.get(status, "#f8fafc")
        self.setStyleSheet(f"""
            QFrame#CompareRow {{
                background-color: {bg};
                border-radius: 6px;
                border: 1px solid {fg}44;
            }}
        """)

        layout = QGridLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(2)

        # Field name
        name_lbl = QLabel(field_name)
        font = QFont(FONT_FAMILY, FONT_SIZE_SMALL)
        font.setWeight(QFont.Weight.DemiBold)
        name_lbl.setFont(font)
        name_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; background: transparent;")

        # Status badge
        badge = StatusBadge(status)

        # Expected / Actual
        exp_lbl = QLabel(f"Expected: {expected}")
        exp_lbl.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: {FONT_SIZE_SMALL}pt; background: transparent;")
        act_lbl = QLabel(f"Detected: {actual}")
        act_lbl.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: {FONT_SIZE_SMALL}pt; background: transparent;")

        layout.addWidget(name_lbl, 0, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(badge, 0, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(exp_lbl, 1, 0, 1, 2)
        layout.addWidget(act_lbl, 2, 0, 1, 2)
        layout.setColumnStretch(1, 1)


# ---------------------------------------------------------------------------
# Main Inspection Form View
# ---------------------------------------------------------------------------

class InspectionFormView(QWidget):
    inspection_saved = pyqtSignal()  # emitted when record is saved

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hardware_specs: Dict[str, Any] = {}
        self._comparison_results = []
        self._overall_status = "WARNING"
        self._worker: Optional[HardwareWorker] = None
        self._build_ui()

    # ------------------------------------------------------------------ UI --

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # Page header
        header_row = QHBoxLayout()
        title = QLabel("New Inspection")
        title_font = QFont(FONT_FAMILY, FONT_SIZE_LARGE)
        title_font.setWeight(QFont.Weight.Bold)
        title.setFont(title_font)
        title.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY};")
        header_row.addWidget(title)
        header_row.addStretch()
        root.addLayout(header_row)

        # Scrollable body
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(16)
        scroll.setWidget(body)
        root.addWidget(scroll)

        # ---- Section 1: Inspection Details ----
        body_layout.addWidget(self._build_details_card())

        # ---- Section 2: Hardware Specs ----
        body_layout.addWidget(self._build_hardware_card())

        # ---- Section 3: Comparison ----
        self._comparison_card = self._build_comparison_card()
        body_layout.addWidget(self._comparison_card)

        # ---- Section 4: Notes ----
        body_layout.addWidget(self._build_notes_card())

        # ---- Action Buttons ----
        body_layout.addLayout(self._build_action_buttons())
        body_layout.addStretch()

    def _build_details_card(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        layout.addWidget(SectionTitle("Inspection Details"))
        layout.addWidget(Divider())

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        # Report Number (auto-generated, read-only)
        self._report_num_edit = StyledLineEdit()
        self._report_num_edit.setText(db.generate_report_number())
        self._report_num_edit.setReadOnly(True)
        self._report_num_edit.setStyleSheet(
            self._report_num_edit.styleSheet() +
            "QLineEdit { background-color: #f1f5f9; color: #64748b; }"
        )

        # PO Number
        self._po_edit = StyledLineEdit("e.g. PO-2024-001")

        # End User
        self._end_user_edit = StyledLineEdit("Full name of end user")

        # Agency
        self._agency_edit = StyledLineEdit("Agency / Department")

        # Office Unit
        self._office_edit = StyledLineEdit("Office or Unit")

        fields = [
            ("Report Number", self._report_num_edit, 0, 0),
            ("PO Number *", self._po_edit, 0, 1),
            ("End User", self._end_user_edit, 1, 0),
            ("Agency", self._agency_edit, 1, 1),
            ("Office / Unit", self._office_edit, 2, 0),
        ]

        for label_text, widget, row, col in fields:
            lbl = FieldLabel(label_text)
            container = QVBoxLayout()
            container.setSpacing(3)
            container.addWidget(lbl)
            container.addWidget(widget)
            grid.addLayout(container, row, col)

        layout.addLayout(grid)
        return card

    def _build_hardware_card(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Header row with scan button
        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Hardware Specifications"))
        hdr.addStretch()
        self._scan_btn = PrimaryButton("Scan Hardware", "⟳")
        self._scan_btn.clicked.connect(self._start_hardware_scan)
        hdr.addWidget(self._scan_btn)
        layout.addLayout(hdr)
        layout.addWidget(Divider())

        # Progress bar (hidden by default)
        self._scan_progress = QProgressBar()
        self._scan_progress.setRange(0, 0)
        self._scan_progress.setFixedHeight(4)
        self._scan_progress.setVisible(False)
        self._scan_progress.setStyleSheet(f"""
            QProgressBar {{
                background-color: {COLOR_BORDER};
                border-radius: 2px;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {COLOR_ACCENT};
                border-radius: 2px;
            }}
        """)
        layout.addWidget(self._scan_progress)

        # Specs grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        spec_fields = [
            ("Serial Number", "_spec_serial"),
            ("Brand / Model", "_spec_brand"),
            ("CPU", "_spec_cpu"),
            ("CPU Cores", "_spec_cores"),
            ("RAM", "_spec_ram"),
            ("GPU", "_spec_gpu"),
            ("GPU VRAM", "_spec_vram"),
            ("Screen Resolution", "_spec_screen"),
            ("Storage", "_spec_storage"),
            ("OS", "_spec_os"),
            ("BIOS UUID", "_spec_bios_uuid"),
            ("Motherboard Serial", "_spec_mb_serial"),
            ("System Uptime", "_spec_uptime"),
        ]

        for i, (label_text, attr) in enumerate(spec_fields):
            row, col = divmod(i, 2)
            lbl = FieldLabel(label_text)
            val_lbl = QLabel("—")
            val_lbl.setStyleSheet(f"""
                color: {COLOR_TEXT_PRIMARY};
                font-size: {FONT_SIZE_NORMAL}pt;
                font-family: "{FONT_FAMILY}";
                background-color: #f8fafc;
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
            """)
            val_lbl.setWordWrap(True)
            setattr(self, attr, val_lbl)
            container = QVBoxLayout()
            container.setSpacing(3)
            container.addWidget(lbl)
            container.addWidget(val_lbl)
            grid.addLayout(container, row, col)

        layout.addLayout(grid)

        # MAC addresses / network info section
        self._network_label = QLabel()
        self._network_label.setWordWrap(True)
        self._network_label.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: {FONT_SIZE_SMALL}pt;")
        layout.addWidget(self._network_label)

        return card

    def _build_comparison_card(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        hdr = QHBoxLayout()
        hdr.addWidget(SectionTitle("Specification Comparison"))
        hdr.addStretch()
        self._overall_badge = StatusBadge("N/A")
        hdr.addWidget(self._overall_badge)
        layout.addLayout(hdr)
        layout.addWidget(Divider())

        # Expected specs input area
        exp_label = FieldLabel("Expected Specs (from PO / Request Form)")
        self._expected_specs_edit = StyledTextEdit(
            "Enter expected specs, one per line.\n"
            "Example:\n"
            "brand: Dell\n"
            "cpu: Core i5-1235U\n"
            "ram: 16GB\n"
            "storage: 512GB\n"
            "gpu: Intel Iris Xe\n"
            "screen: 1920x1080"
        )
        self._expected_specs_edit.setFixedHeight(140)

        run_compare_btn = SecondaryButton("Run Comparison", "⚡")
        run_compare_btn.clicked.connect(self._run_comparison)

        layout.addWidget(exp_label)
        layout.addWidget(self._expected_specs_edit)
        layout.addWidget(run_compare_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # Results container
        self._compare_results_layout = QVBoxLayout()
        self._compare_results_layout.setSpacing(6)
        results_widget = QWidget()
        results_widget.setLayout(self._compare_results_layout)
        results_widget.setStyleSheet("background: transparent;")
        layout.addWidget(results_widget)

        return card

    def _build_notes_card(self) -> QWidget:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(8)
        layout.addWidget(SectionTitle("Notes"))
        layout.addWidget(Divider())
        self._notes_edit = StyledTextEdit("Any additional observations or remarks...")
        self._notes_edit.setFixedHeight(80)
        layout.addWidget(self._notes_edit)
        return card

    def _build_action_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addStretch()
        clear_btn = SecondaryButton("Clear Form")
        clear_btn.clicked.connect(self._clear_form)
        save_btn = PrimaryButton("Save Inspection", "✔")
        save_btn.clicked.connect(self._save_inspection)
        row.addWidget(clear_btn)
        row.addWidget(save_btn)
        return row

    # --------------------------------------------------------- Hardware Scan --

    def _start_hardware_scan(self):
        self._scan_btn.setEnabled(False)
        self._scan_btn.setText("Scanning...")
        self._scan_progress.setVisible(True)
        self._worker = HardwareWorker()
        self._worker.finished.connect(self._on_scan_complete)
        self._worker.error.connect(self._on_scan_error)
        self._worker.start()

    def _on_scan_complete(self, specs: Dict[str, Any]):
        self._hardware_specs = specs
        self._scan_progress.setVisible(False)
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("⟳  Re-scan Hardware")
        self._populate_specs(specs)

    def _on_scan_error(self, msg: str):
        self._scan_progress.setVisible(False)
        self._scan_btn.setEnabled(True)
        self._scan_btn.setText("⟳  Scan Hardware")
        QMessageBox.critical(self, "Scan Error", f"Failed to retrieve hardware specs:\n{msg}")

    def _populate_specs(self, specs: Dict[str, Any]):
        self._spec_serial.setText(specs.get("serial_number", "N/A"))
        brand_model = f"{specs.get('brand', '')} {specs.get('model', '')}".strip()
        self._spec_brand.setText(brand_model or "N/A")
        self._spec_cpu.setText(specs.get("cpu_model", "N/A"))
        self._spec_cores.setText(
            f"{specs.get('cpu_physical_cores', '?')} physical / "
            f"{specs.get('cpu_logical_cores', '?')} logical @ {specs.get('cpu_base_clock', 'N/A')}"
        )
        self._spec_ram.setText(f"{specs.get('ram_total_gb', 'N/A')} GB")
        self._spec_gpu.setText(specs.get("gpu_model", "N/A"))
        self._spec_vram.setText(specs.get("gpu_vram", "N/A"))
        self._spec_screen.setText(specs.get("screen_resolution", "N/A"))

        drives = specs.get("storage", [])
        storage_str = "  |  ".join(
            f"{d.get('device', '')} {d.get('total_gb', '?')} GB" for d in drives
        ) or "N/A"
        self._spec_storage.setText(storage_str)

        self._spec_os.setText(specs.get("os", "N/A"))
        self._spec_bios_uuid.setText(specs.get("bios_uuid", "N/A"))
        self._spec_mb_serial.setText(specs.get("motherboard_serial", "N/A"))
        self._spec_uptime.setText(specs.get("system_uptime", "N/A"))

        # Network
        adapters = specs.get("network_adapters", [])
        net_parts = [
            f"{a['name']} (MAC: {a.get('mac', 'N/A')})"
            for a in adapters if a.get("mac")
        ]
        self._network_label.setText("Network: " + "  |  ".join(net_parts) if net_parts else "")

    # ------------------------------------------------------- Comparison Run --

    def _parse_expected_specs(self) -> Dict[str, Any]:
        """Parse the freeform expected specs text into a dict."""
        text = self._expected_specs_edit.toPlainText().strip()
        result: Dict[str, Any] = {}
        for line in text.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip().lower().replace(" ", "_")
                result[key] = value.strip()
        return result

    def _run_comparison(self):
        if not self._hardware_specs:
            QMessageBox.information(
                self, "No Hardware Data",
                "Please scan the hardware first before running a comparison."
            )
            return

        expected = self._parse_expected_specs()
        if not expected:
            QMessageBox.information(
                self, "No Expected Specs",
                "Please enter the expected specs in the comparison section."
            )
            return

        overall, results = compare_specs(expected, self._hardware_specs)
        self._overall_status = overall
        self._comparison_results = results
        self._overall_badge.set_status(overall)
        self._display_comparison_results(results)

    def _display_comparison_results(self, results):
        # Clear previous results
        while self._compare_results_layout.count():
            child = self._compare_results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for r in results:
            row_widget = CompareResultRow(
                r["display"], r["expected"], r["actual"],
                r["status"], r["message"]
            )
            self._compare_results_layout.addWidget(row_widget)

    # --------------------------------------------------------- Save / Clear --

    def _validate_form(self) -> bool:
        if not self._po_edit.text().strip():
            QMessageBox.warning(self, "Validation Error", "PO Number is required.")
            self._po_edit.setFocus()
            return False
        return True

    def _save_inspection(self):
        if not self._validate_form():
            return

        expected = self._parse_expected_specs()

        # If hardware was scanned but comparison not explicitly run, run it silently
        if self._hardware_specs and expected and not self._comparison_results:
            self._overall_status, self._comparison_results = compare_specs(
                expected, self._hardware_specs
            )

        data = {
            "report_number": self._report_num_edit.text().strip(),
            "po_number": self._po_edit.text().strip(),
            "end_user": self._end_user_edit.text().strip(),
            "agency": self._agency_edit.text().strip(),
            "office_unit": self._office_edit.text().strip(),
            "hardware_serial": self._hardware_specs.get("serial_number", ""),
            "hardware_specs": self._hardware_specs,
            "expected_specs": expected,
            "status": self._overall_status if self._hardware_specs else "WARNING",
            "notes": self._notes_edit.toPlainText().strip(),
        }

        try:
            db.save_inspection(data)
            QMessageBox.information(
                self, "Saved",
                f"Inspection saved successfully.\nReport #: {data['report_number']}"
            )
            self.inspection_saved.emit()
            self._clear_form()
        except Exception as exc:
            QMessageBox.critical(self, "Save Error", f"Failed to save inspection:\n{exc}")

    def _clear_form(self):
        self._report_num_edit.setText(db.generate_report_number())
        for edit in (self._po_edit, self._end_user_edit, self._agency_edit, self._office_edit):
            edit.clear()
        self._expected_specs_edit.clear()
        self._notes_edit.clear()
        self._hardware_specs = {}
        self._comparison_results = []
        self._overall_status = "WARNING"
        self._overall_badge.set_status("N/A")
        self._scan_btn.setText("⟳  Scan Hardware")

        # Reset spec labels
        for attr in ("_spec_serial", "_spec_brand", "_spec_cpu", "_spec_cores",
                     "_spec_ram", "_spec_gpu", "_spec_vram", "_spec_screen",
                     "_spec_storage", "_spec_os", "_spec_bios_uuid",
                     "_spec_mb_serial", "_spec_uptime"):
            getattr(self, attr).setText("—")

        self._network_label.clear()

        while self._compare_results_layout.count():
            child = self._compare_results_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
