from __future__ import annotations

from typing import Dict, List


FEATURE_COLUMNS = [
    "cpu_usage",
    "ram_usage",
    "disk_usage",
    "process_count",
    "top_process_cpu",
    "top_process_memory",
]


def snapshot_to_vector(snapshot: Dict) -> List[float]:
    return [
        float(snapshot.get("cpu_usage", 0.0)),
        float(snapshot.get("ram_usage", 0.0)),
        float(snapshot.get("disk_usage", 0.0)),
        float(snapshot.get("process_count", 0)),
        float(snapshot.get("top_process_cpu", 0.0)),
        float(snapshot.get("top_process_memory", 0.0)),
    ]
