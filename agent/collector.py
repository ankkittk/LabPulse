from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import socket
import time
from typing import Dict, Tuple, Optional

import psutil

from server.models import ResourceSnapshot


class SystemCollector:
    """
    Collects richer telemetry from the local machine.

    The collector now captures:
    - CPU / RAM / Disk
    - Network I/O totals
    - Boot time
    - Process count
    - Top process by CPU usage trend
    """

    def __init__(self) -> None:
        self.hostname = socket.gethostname()
        self._last_process_cpu_times: Dict[int, float] = {}
        self._last_collection_ts = time.time()

    def get_cpu_usage(self) -> float:
        return float(psutil.cpu_percent(interval=1))

    def get_ram_usage(self) -> float:
        return float(psutil.virtual_memory().percent)

    def get_disk_usage(self) -> float:
        return float(psutil.disk_usage("/").percent)

    def get_network_io(self) -> Tuple[float, float]:
        net = psutil.net_io_counters()
        return float(net.bytes_sent), float(net.bytes_recv)

    def get_boot_time(self) -> int:
        return int(psutil.boot_time())

    def get_process_count(self) -> int:
        return len(psutil.pids())

    def get_top_process(self) -> Tuple[Optional[str], float, float]:
        """
        Returns the process with the highest estimated CPU consumption
        since the previous collection.
        """
        now = time.time()
        elapsed = max(now - self._last_collection_ts, 1e-6)

        top_name: Optional[str] = None
        top_cpu: float = 0.0
        top_mem: float = 0.0
        current_cpu_times: Dict[int, float] = {}

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                pid = int(proc.info["pid"])
                name = proc.info.get("name") or f"pid_{pid}"

                cpu_time = proc.cpu_times().user + proc.cpu_times().system
                mem_percent = float(proc.memory_percent() or 0.0)

                prev_cpu_time = self._last_process_cpu_times.get(pid)
                cpu_percent = 0.0
                if prev_cpu_time is not None:
                    cpu_percent = max(0.0, ((cpu_time - prev_cpu_time) / elapsed) * 100.0)

                current_cpu_times[pid] = cpu_time

                if (cpu_percent > top_cpu) or (cpu_percent == top_cpu and mem_percent > top_mem):
                    top_name = name
                    top_cpu = float(cpu_percent)
                    top_mem = float(mem_percent)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        self._last_process_cpu_times = current_cpu_times
        self._last_collection_ts = now
        return top_name, top_cpu, top_mem

    def collect(self) -> ResourceSnapshot:
        network_sent, network_recv = self.get_network_io()
        top_process_name, top_process_cpu, top_process_memory = self.get_top_process()

        return ResourceSnapshot(
            hostname=self.hostname,
            cpu_usage=self.get_cpu_usage(),
            ram_usage=self.get_ram_usage(),
            disk_usage=self.get_disk_usage(),
            network_sent=network_sent,
            network_recv=network_recv,
            boot_time=self.get_boot_time(),
            process_count=self.get_process_count(),
            top_process_name=top_process_name,
            top_process_cpu=top_process_cpu,
            top_process_memory=top_process_memory,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def collect_dict(self) -> dict:
        return asdict(self.collect())
