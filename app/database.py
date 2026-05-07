"""
Database module for Laptop Inspector.
Handles all SQLite operations for storing and retrieving inspection records.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any


DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "inspections.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_database() -> None:
    """Create tables if they do not exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_number TEXT UNIQUE NOT NULL,
                po_number TEXT NOT NULL,
                inspection_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                end_user TEXT,
                agency TEXT,
                office_unit TEXT,
                hardware_serial TEXT,
                hardware_specs TEXT,
                expected_specs TEXT,
                status TEXT CHECK(status IN ('PASS', 'FAIL', 'WARNING')),
                notes TEXT
            )
        """)
        conn.commit()


def generate_report_number() -> str:
    """Generate a unique report number based on timestamp."""
    now = datetime.now()
    prefix = f"RPT-{now.strftime('%Y%m%d')}"
    with get_connection() as conn:
        row = conn.execute(
            "SELECT COUNT(*) as cnt FROM inspections WHERE report_number LIKE ?",
            (f"{prefix}%",)
        ).fetchone()
        seq = (row["cnt"] if row else 0) + 1
    return f"{prefix}-{seq:04d}"


def save_inspection(data: Dict[str, Any]) -> int:
    """Insert a new inspection record. Returns the new row id."""
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO inspections
                (report_number, po_number, inspection_date, end_user, agency,
                 office_unit, hardware_serial, hardware_specs, expected_specs,
                 status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["report_number"],
                data["po_number"],
                data.get("inspection_date", datetime.now().isoformat()),
                data.get("end_user", ""),
                data.get("agency", ""),
                data.get("office_unit", ""),
                data.get("hardware_serial", ""),
                json.dumps(data.get("hardware_specs", {})),
                json.dumps(data.get("expected_specs", {})),
                data.get("status", "WARNING"),
                data.get("notes", ""),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def update_inspection(record_id: int, data: Dict[str, Any]) -> None:
    """Update an existing inspection record."""
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE inspections SET
                po_number = ?, end_user = ?, agency = ?, office_unit = ?,
                hardware_serial = ?, hardware_specs = ?, expected_specs = ?,
                status = ?, notes = ?
            WHERE id = ?
            """,
            (
                data["po_number"],
                data.get("end_user", ""),
                data.get("agency", ""),
                data.get("office_unit", ""),
                data.get("hardware_serial", ""),
                json.dumps(data.get("hardware_specs", {})),
                json.dumps(data.get("expected_specs", {})),
                data.get("status", "WARNING"),
                data.get("notes", ""),
                record_id,
            ),
        )
        conn.commit()


def delete_inspection(record_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM inspections WHERE id = ?", (record_id,))
        conn.commit()


def get_all_inspections(
    search: str = "",
    status_filter: str = "All",
) -> List[Dict[str, Any]]:
    """Return list of inspections, optionally filtered."""
    query = "SELECT * FROM inspections WHERE 1=1"
    params: List[Any] = []

    if search:
        query += " AND (report_number LIKE ? OR po_number LIKE ? OR end_user LIKE ? OR agency LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like, like])

    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)

    query += " ORDER BY inspection_date DESC"

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    results = []
    for row in rows:
        record = dict(row)
        for field in ("hardware_specs", "expected_specs"):
            try:
                record[field] = json.loads(record[field] or "{}")
            except (json.JSONDecodeError, TypeError):
                record[field] = {}
        results.append(record)
    return results


def get_inspection_by_id(record_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM inspections WHERE id = ?", (record_id,)
        ).fetchone()
    if row is None:
        return None
    record = dict(row)
    for field in ("hardware_specs", "expected_specs"):
        try:
            record[field] = json.loads(record[field] or "{}")
        except (json.JSONDecodeError, TypeError):
            record[field] = {}
    return record


def get_stats() -> Dict[str, int]:
    """Return summary stats for dashboard."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) as c FROM inspections").fetchone()["c"]
        passed = conn.execute(
            "SELECT COUNT(*) as c FROM inspections WHERE status='PASS'"
        ).fetchone()["c"]
        failed = conn.execute(
            "SELECT COUNT(*) as c FROM inspections WHERE status='FAIL'"
        ).fetchone()["c"]
        warning = conn.execute(
            "SELECT COUNT(*) as c FROM inspections WHERE status='WARNING'"
        ).fetchone()["c"]
    return {"total": total, "passed": passed, "failed": failed, "warning": warning}
