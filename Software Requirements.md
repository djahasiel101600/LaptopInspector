# Laptop Inspector - Python Desktop Application Specification

## Project Overview
**Application Name:** Laptop Inspector  
**Purpose:** Desktop tool for inspecting brand new laptops by retrieving hardware specs, comparing against purchase orders/request forms, authenticating authenticity, and logging inspections with end-user details.  
**Target Platform:** Cross-platform (Windows primary, Mac/Linux secondary)  
**Current Date:** 2026-05-07

## Core Features

### 1. Hardware Retrieval Module
Fetch comprehensive laptop specifications using system APIs:

| Specification | Details | Libraries |
|---------------|---------|-----------|
| **Serial Number** | System serial | `wmi`, `platform` |
| **CPU** | Model, cores, clock speed | `psutil`, `platform` |
| **GPU** | Model, VRAM | `wmi`, `subprocess` |
| **Screen** | Size, resolution | `screeninfo`, `wmi` |
| **Network Card** | WiFi/Ethernet model | `psutil`, `wmi` |
| **Brand/Manufacturer** | OEM brand | `wmi`, `platform` |
| **Authenticity Checks** | BIOS UUID, Motherboard serial, MAC addresses, System uptime | `uuid`, `psutil` |

### 2. Inspection Workflow
**Input Form Fields:**

### 3. Comparison Engine
- **Auto-parse** expected specs vs retrieved hardware
- **PASS/FAIL** verdict with color coding (Green/Red)
- **Mismatch highlighting** for critical fields
- **Summary report** generation

### 4. Data Management
- **SQLite database** for local storage
- **Search/filter** by PO#, Report#, Date, Status
- **Export** to CSV/PDF
- **DataGrid view** of inspection history

## UI Mockup


## Technical Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **UI Framework** | Tkinter or PyQt6 | Desktop interface |
| **Database** | SQLite | Local inspection storage |
| **Hardware APIs** | `psutil`, `wmi`, `platform` | System specs retrieval |
| **Packaging** | PyInstaller | Standalone executable |
| **Reports** | `pandas`, `reportlab` | CSV/PDF export |

## Database Schema

```sql
CREATE TABLE inspections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_number TEXT UNIQUE NOT NULL,
    po_number TEXT NOT NULL,
    inspection_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_user TEXT,
    agency TEXT,
    office_unit TEXT,
    hardware_serial TEXT,
    hardware_specs JSON,
    expected_specs TEXT,
    status TEXT CHECK(status IN ('PASS', 'FAIL', 'WARNING')),
    notes TEXT
);
