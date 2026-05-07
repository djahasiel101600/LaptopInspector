"""
Comparison engine for Laptop Inspector.
Parses expected specs and compares against retrieved hardware specs.
"""

import re
from typing import Dict, Any, List, Tuple


# ---------------------------------------------------------------------------
# Comparison result codes
# ---------------------------------------------------------------------------
PASS = "PASS"
FAIL = "FAIL"
WARNING = "WARNING"
SKIP = "SKIP"


def _normalize(value: str) -> str:
    return str(value).strip().lower()


def _extract_number(text: str) -> float:
    """Extract first numeric value from a string."""
    match = re.search(r"[\d.]+", str(text))
    return float(match.group()) if match else 0.0


# ---------------------------------------------------------------------------
# Individual field comparators
# ---------------------------------------------------------------------------

def _compare_cpu(expected: str, actual: str) -> Tuple[str, str]:
    exp = _normalize(expected)
    act = _normalize(actual)
    if not exp:
        return SKIP, "Not specified"
    # Check keyword presence (e.g. "i5-1235U" or "core i5")
    keywords = [k.strip() for k in re.split(r"[,/]", exp) if k.strip()]
    for kw in keywords:
        if kw in act:
            return PASS, f"Expected '{expected}' found in '{actual}'"
    return FAIL, f"Expected '{expected}', got '{actual}'"


def _compare_ram(expected: str, actual_gb: float) -> Tuple[str, str]:
    exp = _normalize(expected)
    if not exp:
        return SKIP, "Not specified"
    expected_gb = _extract_number(exp)
    if expected_gb == 0:
        return SKIP, "Could not parse expected RAM"
    if actual_gb >= expected_gb:
        return PASS, f"Expected {expected_gb} GB, got {actual_gb} GB"
    return FAIL, f"Expected {expected_gb} GB, got {actual_gb} GB"


def _compare_storage(expected: str, actual_drives: list) -> Tuple[str, str]:
    exp = _normalize(expected)
    if not exp:
        return SKIP, "Not specified"
    expected_gb = _extract_number(exp)
    total_actual = sum(_extract_number(str(d.get("total_gb", 0))) for d in actual_drives)
    if expected_gb == 0:
        return SKIP, "Could not parse expected storage"
    # Allow 10% tolerance for reported vs marketed capacity
    if total_actual >= expected_gb * 0.88:
        return PASS, f"Expected {expected_gb} GB, total detected {total_actual:.0f} GB"
    return FAIL, f"Expected {expected_gb} GB, total detected {total_actual:.0f} GB"


def _compare_screen(expected: str, actual_res: str) -> Tuple[str, str]:
    exp = _normalize(expected)
    act = _normalize(actual_res)
    if not exp:
        return SKIP, "Not specified"
    keywords = [k.strip() for k in re.split(r"[,/]", exp) if k.strip()]
    for kw in keywords:
        if kw in act:
            return PASS, f"Expected '{expected}' found in resolution '{actual_res}'"
    # Check numeric resolution
    exp_nums = re.findall(r"\d+", exp)
    act_nums = re.findall(r"\d+", act)
    if exp_nums and act_nums and set(exp_nums).issubset(set(act_nums)):
        return PASS, f"Resolution match: '{actual_res}'"
    return WARNING, f"Expected '{expected}', detected '{actual_res}' — verify manually"


def _compare_gpu(expected: str, actual: str) -> Tuple[str, str]:
    exp = _normalize(expected)
    act = _normalize(actual)
    if not exp:
        return SKIP, "Not specified"
    keywords = [k.strip() for k in re.split(r"[,/]", exp) if k.strip()]
    for kw in keywords:
        if kw in act:
            return PASS, f"Expected '{expected}' found in '{actual}'"
    return FAIL, f"Expected '{expected}', got '{actual}'"


def _compare_serial(expected: str, actual: str) -> Tuple[str, str]:
    exp = _normalize(expected)
    act = _normalize(actual)
    if not exp:
        return SKIP, "Not specified"
    if exp == act:
        return PASS, "Serial numbers match"
    return FAIL, f"Expected '{expected}', got '{actual}'"


def _compare_brand(expected: str, actual: str) -> Tuple[str, str]:
    exp = _normalize(expected)
    act = _normalize(actual)
    if not exp:
        return SKIP, "Not specified"
    if exp in act or act in exp:
        return PASS, f"Brand matches: '{actual}'"
    return FAIL, f"Expected brand '{expected}', got '{actual}'"


# ---------------------------------------------------------------------------
# Main comparison function
# ---------------------------------------------------------------------------

def compare_specs(
    expected: Dict[str, Any],
    actual: Dict[str, Any],
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Compare expected specs dict against actual hardware specs dict.

    Returns:
        overall_status: 'PASS', 'FAIL', or 'WARNING'
        results: list of per-field comparison result dicts
    """
    results: List[Dict[str, Any]] = []

    def add(field: str, display: str, status: str, message: str,
            expected_val: str = "", actual_val: str = "") -> None:
        results.append({
            "field": field,
            "display": display,
            "status": status,
            "message": message,
            "expected": expected_val,
            "actual": actual_val,
        })

    # Serial Number
    if expected.get("serial_number"):
        st, msg = _compare_serial(
            expected["serial_number"], actual.get("serial_number", "")
        )
        add("serial_number", "Serial Number", st, msg,
            expected.get("serial_number", ""), actual.get("serial_number", ""))

    # Brand
    if expected.get("brand"):
        st, msg = _compare_brand(expected["brand"], actual.get("brand", ""))
        add("brand", "Brand / Manufacturer", st, msg,
            expected.get("brand", ""), actual.get("brand", ""))

    # CPU
    if expected.get("cpu"):
        st, msg = _compare_cpu(expected["cpu"], actual.get("cpu_model", ""))
        add("cpu", "CPU Model", st, msg,
            expected.get("cpu", ""), actual.get("cpu_model", ""))

    # RAM
    if expected.get("ram"):
        st, msg = _compare_ram(expected["ram"], actual.get("ram_total_gb", 0))
        add("ram", "RAM", st, msg,
            expected.get("ram", ""), f"{actual.get('ram_total_gb', 0)} GB")

    # Storage
    if expected.get("storage"):
        st, msg = _compare_storage(expected["storage"], actual.get("storage", []))
        add("storage", "Storage", st, msg,
            expected.get("storage", ""),
            ", ".join(f"{d.get('total_gb')} GB" for d in actual.get("storage", [])))

    # GPU
    if expected.get("gpu"):
        st, msg = _compare_gpu(expected["gpu"], actual.get("gpu_model", ""))
        add("gpu", "GPU Model", st, msg,
            expected.get("gpu", ""), actual.get("gpu_model", ""))

    # Screen
    if expected.get("screen"):
        st, msg = _compare_screen(
            expected["screen"], actual.get("screen_resolution", "")
        )
        add("screen", "Screen Resolution", st, msg,
            expected.get("screen", ""), actual.get("screen_resolution", ""))

    # Determine overall status
    statuses = [r["status"] for r in results if r["status"] != SKIP]
    if not statuses:
        overall = WARNING
    elif FAIL in statuses:
        overall = FAIL
    elif WARNING in statuses:
        overall = WARNING
    else:
        overall = PASS

    return overall, results
