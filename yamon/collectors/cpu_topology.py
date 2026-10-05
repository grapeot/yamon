"""Map logical CPU indices to Apple Silicon performance levels."""

import platform
import re
import subprocess
from functools import lru_cache
from typing import Dict, Optional


def parse_ioreg_cpu_types(output: str, cpu_count: int) -> Optional[Dict[int, str]]:
    """Return a complete E/P/M map, or None rather than guessing from core count."""
    entries = list(re.finditer(r"(?m)^.*\+-o cpu(\d+)@[^\n]*$", output))
    types: Dict[int, str] = {}
    for index, match in enumerate(entries):
        end = entries[index + 1].start() if index + 1 < len(entries) else len(output)
        block = output[match.end():end]
        # Only inspect this node's properties, not subsequent non-CPU nodes.
        block = block.split("}", 1)[0]
        kind = re.search(r'"cluster-type"\s*=\s*<"([EPM])">', block)
        logical_id = re.search(r'"logical-cpu-id"\s*=\s*(\d+)', block)
        cpu_id = int(logical_id.group(1)) if logical_id else int(match.group(1))
        if kind and 0 <= cpu_id < cpu_count:
            if cpu_id in types:
                return None
            types[cpu_id] = kind.group(1)
    if len(types) != cpu_count:
        return None
    return types


@lru_cache(maxsize=8)
def cpu_types(cpu_count: int) -> Optional[Dict[int, str]]:
    # Rosetta reports x86_64 even when IODeviceTree describes Apple Silicon.
    if platform.system() != "Darwin":
        return None
    try:
        output = subprocess.run(
            ["ioreg", "-p", "IODeviceTree", "-l", "-w", "0"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout
        types = parse_ioreg_cpu_types(output, cpu_count)
        if types is None:
            return None
        p_count = int(subprocess.check_output(
            ["sysctl", "-n", "hw.perflevel0.physicalcpu"], text=True, timeout=2,
        ))
        secondary_count = int(subprocess.check_output(
            ["sysctl", "-n", "hw.perflevel1.physicalcpu"], text=True, timeout=2,
        ))
        secondary_kind = "M" if "M" in types.values() else "E"
        if (list(types.values()).count("P") != p_count
                or list(types.values()).count(secondary_kind) != secondary_count
                or p_count + secondary_count != cpu_count):
            return None
        return types
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


@lru_cache(maxsize=8)
def cpu_group_label(kind, has_middle):
    if has_middle:
        level = {"P": 0, "M": 1}.get(kind)
        if level is not None:
            try:
                return subprocess.check_output(
                    ["sysctl", "-n", f"hw.perflevel{level}.name"], text=True, timeout=2,
                ).strip() or f"{kind}-Cores"
            except (OSError, subprocess.SubprocessError):
                pass
    return f"{kind}-Cores"


def cpu_groups(per_core, topology):
    if not topology or len(per_core) != len(topology):
        return []
    return [
        {"type": kind, "label": cpu_group_label(kind, "M" in topology.values()),
         "count": sum(value == kind for value in topology.values()),
         "percent": sum(per_core[i] for i, value in topology.items() if value == kind) / len(per_core)}
        for kind in ("P", "E", "M") if kind in topology.values()
    ]


def cpu_group_percentages(per_core, topology):
    """Contributions to total busy time; both values together stay <= 100%."""
    if topology is None or len(per_core) != len(topology):
        return None, None
    count = len(per_core)
    if count == 0:
        return None, None
    return (
        sum(per_core[i] for i, kind in topology.items() if kind == "P") / count if "P" in topology.values() else None,
        sum(per_core[i] for i, kind in topology.items() if kind == "E") / count if "E" in topology.values() else None,
    )
