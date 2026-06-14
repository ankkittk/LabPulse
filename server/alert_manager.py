"""
server/alert_manager.py
=======================

AlertManager evaluates every incoming resource snapshot against configurable
thresholds and writes alert records to the database when a threshold is breached.

Design:
  • Each resource type (CPU / RAM / Disk) has its own private method.
    This makes it easy to add new resource checks without touching existing code
    (Open/Closed Principle).
  • The manager is stateless between calls — it does not remember whether it
    already alerted for a given machine. This keeps the implementation simple at
    the cost of generating repeated alerts every 10 seconds while an overload
    persists.

TODO (Phase 2):
  • Add a cooldown cache (dict: computer_id → last_alert_time per type) so the
    same alert is not written more than once per minute.
  • Add alert severity levels: WARNING (>75%) and CRITICAL (>90%).
  • Trigger external notifications (email/webhook) from here.
"""

import logging
from server.database import DatabaseManager
from config.settings import (
    CPU_ALERT_THRESHOLD,
    RAM_ALERT_THRESHOLD,
    DISK_ALERT_THRESHOLD,
)

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Evaluates resource snapshots and logs alerts to the database.

    Usage (called from server/main.py after every snapshot is stored):
        alert_manager.evaluate(computer_id, pc_name, cpu, ram, disk)
    """

    def __init__(self, db: DatabaseManager) -> None:
        self.db             = db
        self.cpu_threshold  = CPU_ALERT_THRESHOLD
        self.ram_threshold  = RAM_ALERT_THRESHOLD
        self.disk_threshold = DISK_ALERT_THRESHOLD

    # ── Public interface ──────────────────────────────────────────────────────

    def evaluate(
        self,
        computer_id: int,
        pc_name:     str,
        cpu:         float,
        ram:         float,
        disk:        float,
    ) -> None:
        """
        Run all threshold checks for one snapshot.
        Each failing check writes one row to the alerts table.
        """
        self._check_cpu(computer_id, pc_name, cpu)
        self._check_ram(computer_id, pc_name, ram)
        self._check_disk(computer_id, pc_name, disk)

    # ── Private checks ────────────────────────────────────────────────────────

    def _check_cpu(self, computer_id: int, pc_name: str, value: float) -> None:
        if value >= self.cpu_threshold:
            msg = (
                f"{pc_name}: CPU at {value:.1f}% "
                f"(threshold {self.cpu_threshold:.0f}%)"
            )
            logger.warning(f"[ALERT] HIGH_CPU — {msg}")
            self.db.insert_alert(computer_id, "HIGH_CPU", msg)

    def _check_ram(self, computer_id: int, pc_name: str, value: float) -> None:
        if value >= self.ram_threshold:
            msg = (
                f"{pc_name}: RAM at {value:.1f}% "
                f"(threshold {self.ram_threshold:.0f}%)"
            )
            logger.warning(f"[ALERT] HIGH_RAM — {msg}")
            self.db.insert_alert(computer_id, "HIGH_RAM", msg)

    def _check_disk(self, computer_id: int, pc_name: str, value: float) -> None:
        if value >= self.disk_threshold:
            msg = (
                f"{pc_name}: Disk at {value:.1f}% "
                f"(threshold {self.disk_threshold:.0f}%)"
            )
            logger.warning(f"[ALERT] HIGH_DISK — {msg}")
            self.db.insert_alert(computer_id, "HIGH_DISK", msg)

    # TODO: def _check_offline(self, ...) — raise OFFLINE alert when a machine
    #       is flipped to 'offline' by mark_offline_computers().
