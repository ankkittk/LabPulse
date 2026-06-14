from dataclasses import asdict
from datetime import datetime, timezone
import socket

import psutil

from server.models import ResourceSnapshot


class SystemCollector:
    def __init__(self) -> None:
        self.hostname = socket.gethostname()

    def get_cpu_usage(self) -> float:
        return float(psutil.cpu_percent(interval=1))

    def get_ram_usage(self) -> float:
        return float(psutil.virtual_memory().percent)

    def get_disk_usage(self) -> float:
        return float(psutil.disk_usage("/").percent)

    def collect(self) -> ResourceSnapshot:
        return ResourceSnapshot(
            hostname=self.hostname,
            cpu_usage=self.get_cpu_usage(),
            ram_usage=self.get_ram_usage(),
            disk_usage=self.get_disk_usage(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def collect_dict(self) -> dict:
        return asdict(self.collect())
