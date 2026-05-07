"""
Hardware retrieval module for Laptop Inspector.
Fetches system specifications using psutil, wmi (Windows), platform, and uuid.
"""

import platform
import uuid
import subprocess
import sys
import re
from typing import Dict, Any


def _run_wmi_query(query: str, field: str) -> str:
    """Safe WMI query runner. Returns empty string on any failure."""
    try:
        import wmi  # type: ignore
        c = wmi.WMI()
        results = c.query(query)
        if results:
            return str(getattr(results[0], field, "")).strip()
    except Exception:
        pass
    return ""


def get_serial_number() -> str:
    if sys.platform == "win32":
        value = _run_wmi_query(
            "SELECT SerialNumber FROM Win32_BIOS", "SerialNumber"
        )
        if value and value.lower() not in ("", "to be filled by o.e.m.", "default string"):
            return value
    try:
        if sys.platform == "darwin":
            out = subprocess.check_output(
                ["system_profiler", "SPHardwareDataType"], text=True
            )
            match = re.search(r"Serial Number.*?:\s+(\S+)", out)
            if match:
                return match.group(1)
        elif sys.platform.startswith("linux"):
            out = subprocess.check_output(
                ["sudo", "dmidecode", "-s", "system-serial-number"], text=True
            )
            return out.strip()
    except Exception:
        pass
    return "N/A"


def get_cpu_info() -> Dict[str, Any]:
    import psutil

    model = platform.processor() or "Unknown"
    if sys.platform == "win32":
        wmi_model = _run_wmi_query(
            "SELECT Name FROM Win32_Processor", "Name"
        )
        if wmi_model:
            model = wmi_model

    try:
        physical_cores = psutil.cpu_count(logical=False) or 0
        logical_cores = psutil.cpu_count(logical=True) or 0
        freq = psutil.cpu_freq()
        base_clock = f"{freq.max / 1000:.2f} GHz" if freq and freq.max else "N/A"
    except Exception:
        physical_cores = logical_cores = 0
        base_clock = "N/A"

    return {
        "model": model.strip(),
        "physical_cores": physical_cores,
        "logical_cores": logical_cores,
        "base_clock": base_clock,
    }


def get_gpu_info() -> Dict[str, Any]:
    if sys.platform == "win32":
        try:
            import wmi  # type: ignore
            c = wmi.WMI()
            gpus = c.query("SELECT * FROM Win32_VideoController")
            if gpus:
                g = gpus[0]
                vram_bytes = int(getattr(g, "AdapterRAM", 0) or 0)
                vram_gb = round(vram_bytes / (1024 ** 3), 1) if vram_bytes > 0 else 0
                return {
                    "model": str(getattr(g, "Name", "Unknown")).strip(),
                    "vram": f"{vram_gb} GB" if vram_gb > 0 else "Shared/N/A",
                    "driver_version": str(getattr(g, "DriverVersion", "N/A")).strip(),
                }
        except Exception:
            pass

    # Fallback: try subprocess nvidia-smi
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            text=True,
        )
        parts = out.strip().split(",")
        return {
            "model": parts[0].strip() if parts else "Unknown",
            "vram": parts[1].strip() if len(parts) > 1 else "N/A",
            "driver_version": "N/A",
        }
    except Exception:
        pass

    return {"model": "Unknown", "vram": "N/A", "driver_version": "N/A"}


def get_ram_info() -> Dict[str, Any]:
    import psutil

    try:
        vm = psutil.virtual_memory()
        total_gb = round(vm.total / (1024 ** 3), 1)
    except Exception:
        total_gb = 0

    slots_info = []
    if sys.platform == "win32":
        try:
            import wmi  # type: ignore
            c = wmi.WMI()
            for stick in c.query("SELECT * FROM Win32_PhysicalMemory"):
                cap = int(getattr(stick, "Capacity", 0) or 0)
                slots_info.append({
                    "capacity": f"{round(cap / (1024**3), 0):.0f} GB",
                    "speed": f"{getattr(stick, 'Speed', 'N/A')} MHz",
                    "type": str(getattr(stick, "MemoryType", "N/A")),
                    "manufacturer": str(getattr(stick, "Manufacturer", "N/A")).strip(),
                })
        except Exception:
            pass

    return {"total_gb": total_gb, "slots": slots_info}


def get_storage_info() -> list:
    import psutil

    drives = []
    try:
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                drives.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024 ** 3), 1),
                })
            except PermissionError:
                continue
    except Exception:
        pass
    return drives


def get_screen_info() -> Dict[str, Any]:
    if sys.platform == "win32":
        try:
            import wmi  # type: ignore
            c = wmi.WMI()
            monitors = c.query("SELECT * FROM Win32_VideoController")
            if monitors:
                m = monitors[0]
                h_res = getattr(m, "CurrentHorizontalResolution", None)
                v_res = getattr(m, "CurrentVerticalResolution", None)
                if h_res and v_res:
                    return {
                        "resolution": f"{h_res}x{v_res}",
                        "size_inches": "N/A",
                    }
        except Exception:
            pass

    try:
        from screeninfo import get_monitors  # type: ignore
        monitors = get_monitors()
        if monitors:
            m = monitors[0]
            return {
                "resolution": f"{m.width}x{m.height}",
                "size_inches": "N/A",
            }
    except Exception:
        pass

    return {"resolution": "N/A", "size_inches": "N/A"}


def get_network_info() -> list:
    import psutil

    adapters = []
    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        import psutil as _ps
        AF_LINK = _ps.AF_LINK if hasattr(_ps, "AF_LINK") else 17

        for name, stat in stats.items():
            mac = ""
            for addr in addrs.get(name, []):
                if addr.family == AF_LINK:
                    mac = addr.address
                    break
            adapters.append({
                "name": name,
                "is_up": stat.isup,
                "speed": stat.speed,
                "mac": mac,
            })
    except Exception:
        pass
    return adapters


def get_manufacturer_info() -> Dict[str, Any]:
    brand = "Unknown"
    model = "Unknown"

    if sys.platform == "win32":
        brand = _run_wmi_query(
            "SELECT Manufacturer FROM Win32_ComputerSystem", "Manufacturer"
        )
        model = _run_wmi_query(
            "SELECT Model FROM Win32_ComputerSystem", "Model"
        )

    if not brand or brand == "Unknown":
        brand = platform.node()

    return {"brand": brand.strip(), "model": model.strip()}


def get_bios_info() -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "bios_uuid": str(uuid.uuid4()),  # fallback
        "motherboard_serial": "N/A",
        "bios_version": "N/A",
    }

    if sys.platform == "win32":
        mb_serial = _run_wmi_query(
            "SELECT SerialNumber FROM Win32_BaseBoard", "SerialNumber"
        )
        bios_ver = _run_wmi_query(
            "SELECT SMBIOSBIOSVersion FROM Win32_BIOS", "SMBIOSBIOSVersion"
        )
        bios_uuid = _run_wmi_query(
            "SELECT UUID FROM Win32_ComputerSystemProduct", "UUID"
        )

        info["motherboard_serial"] = mb_serial or "N/A"
        info["bios_version"] = bios_ver or "N/A"
        if bios_uuid:
            info["bios_uuid"] = bios_uuid

    return info


def get_uptime() -> str:
    import psutil
    import time

    try:
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    except Exception:
        return "N/A"


def collect_all_specs() -> Dict[str, Any]:
    """Collect all hardware specs and return as a unified dictionary."""
    manufacturer = get_manufacturer_info()
    cpu = get_cpu_info()
    gpu = get_gpu_info()
    ram = get_ram_info()
    storage = get_storage_info()
    screen = get_screen_info()
    network = get_network_info()
    bios = get_bios_info()

    return {
        "serial_number": get_serial_number(),
        "brand": manufacturer["brand"],
        "model": manufacturer["model"],
        "cpu_model": cpu["model"],
        "cpu_physical_cores": cpu["physical_cores"],
        "cpu_logical_cores": cpu["logical_cores"],
        "cpu_base_clock": cpu["base_clock"],
        "gpu_model": gpu["model"],
        "gpu_vram": gpu["vram"],
        "gpu_driver": gpu["driver_version"],
        "ram_total_gb": ram["total_gb"],
        "ram_slots": ram["slots"],
        "storage": storage,
        "screen_resolution": screen["resolution"],
        "screen_size": screen["size_inches"],
        "network_adapters": network,
        "bios_uuid": bios["bios_uuid"],
        "motherboard_serial": bios["motherboard_serial"],
        "bios_version": bios["bios_version"],
        "system_uptime": get_uptime(),
        "os": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "machine_arch": platform.machine(),
    }
