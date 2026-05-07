"""
Export module for Laptop Inspector.
Handles CSV and PDF report generation.
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Any


def export_to_csv(records: List[Dict[str, Any]], filepath: str) -> None:
    """Export inspection records to a CSV file."""
    fieldnames = [
        "report_number", "po_number", "inspection_date", "end_user",
        "agency", "office_unit", "hardware_serial", "status", "notes",
    ]

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({k: record.get(k, "") for k in fieldnames})


def _status_color(status: str):
    """Return RGB tuple for a status value."""
    mapping = {
        "PASS": (0.18, 0.65, 0.34),
        "FAIL": (0.85, 0.19, 0.19),
        "WARNING": (0.95, 0.61, 0.07),
    }
    return mapping.get(status, (0.4, 0.4, 0.4))


def export_to_pdf(record: Dict[str, Any], filepath: str) -> None:
    """Export a single inspection record to a PDF report."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
    except ImportError as e:
        raise ImportError("reportlab is required for PDF export. Run: pip install reportlab") from e

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # Header
    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        fontSize=20, textColor=colors.HexColor("#1a3a5c"),
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "Sub", parent=styles["Normal"],
        fontSize=10, textColor=colors.grey,
        alignment=TA_CENTER, spaceAfter=12,
    )
    elements.append(Paragraph("Laptop Inspector", title_style))
    elements.append(Paragraph("Hardware Inspection Report", sub_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a3a5c")))
    elements.append(Spacer(1, 0.4 * cm))

    # Status badge
    status = record.get("status", "WARNING")
    r, g, b = _status_color(status)
    status_color = colors.Color(r, g, b)

    status_style = ParagraphStyle(
        "Status", parent=styles["Normal"],
        fontSize=14, textColor=status_color,
        alignment=TA_CENTER, spaceAfter=12,
        fontName="Helvetica-Bold",
    )
    elements.append(Paragraph(f"Status: {status}", status_style))
    elements.append(Spacer(1, 0.3 * cm))

    # Inspection metadata
    label_style = ParagraphStyle("label", parent=styles["Normal"], fontSize=9, textColor=colors.grey)
    value_style = ParagraphStyle("val", parent=styles["Normal"], fontSize=10, fontName="Helvetica-Bold")

    meta_data = [
        ["Report Number", record.get("report_number", "N/A"),
         "PO Number", record.get("po_number", "N/A")],
        ["Inspection Date", str(record.get("inspection_date", ""))[:19],
         "End User", record.get("end_user", "N/A")],
        ["Agency", record.get("agency", "N/A"),
         "Office / Unit", record.get("office_unit", "N/A")],
    ]

    meta_table = Table(meta_data, colWidths=[3.5 * cm, 6.5 * cm, 3.5 * cm, 4 * cm])
    meta_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.grey),
        ("TEXTCOLOR", (2, 0), (2, -1), colors.grey),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (3, 0), (3, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f9f9f9")),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 0.5 * cm))

    # Hardware specs section
    elements.append(Paragraph("Hardware Specifications", styles["Heading2"]))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elements.append(Spacer(1, 0.2 * cm))

    hardware_specs = record.get("hardware_specs", {})
    if isinstance(hardware_specs, str):
        try:
            hardware_specs = json.loads(hardware_specs)
        except Exception:
            hardware_specs = {}

    spec_rows = [
        ["Field", "Value"],
        ["Serial Number", hardware_specs.get("serial_number", "N/A")],
        ["Brand / Model", f"{hardware_specs.get('brand', '')} {hardware_specs.get('model', '')}".strip()],
        ["CPU", hardware_specs.get("cpu_model", "N/A")],
        ["CPU Cores", f"{hardware_specs.get('cpu_physical_cores', 'N/A')} physical / {hardware_specs.get('cpu_logical_cores', 'N/A')} logical"],
        ["RAM", f"{hardware_specs.get('ram_total_gb', 'N/A')} GB"],
        ["GPU", hardware_specs.get("gpu_model", "N/A")],
        ["GPU VRAM", hardware_specs.get("gpu_vram", "N/A")],
        ["Screen Resolution", hardware_specs.get("screen_resolution", "N/A")],
        ["OS", hardware_specs.get("os", "N/A")],
        ["BIOS UUID", hardware_specs.get("bios_uuid", "N/A")],
        ["Motherboard Serial", hardware_specs.get("motherboard_serial", "N/A")],
        ["System Uptime", hardware_specs.get("system_uptime", "N/A")],
    ]

    # Add storage
    for i, drive in enumerate(hardware_specs.get("storage", []), 1):
        spec_rows.append([f"Storage [{i}]", f"{drive.get('device', '')} — {drive.get('total_gb', 'N/A')} GB"])

    spec_table = Table(spec_rows, colWidths=[5 * cm, 12.5 * cm])
    spec_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4f8")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(spec_table)
    elements.append(Spacer(1, 0.5 * cm))

    # Notes
    notes = record.get("notes", "").strip()
    if notes:
        elements.append(Paragraph("Notes", styles["Heading2"]))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
        elements.append(Spacer(1, 0.2 * cm))
        elements.append(Paragraph(notes, styles["Normal"]))
        elements.append(Spacer(1, 0.3 * cm))

    # Footer
    footer_style = ParagraphStyle(
        "footer", parent=styles["Normal"],
        fontSize=8, textColor=colors.grey, alignment=TA_CENTER,
    )
    elements.append(Spacer(1, 1 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elements.append(Paragraph(
        f"Generated by Laptop Inspector on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        footer_style,
    ))

    doc.build(elements)
