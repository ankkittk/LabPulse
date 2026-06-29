"""
severity.py

Responsible for calculating the severity of an incident.

This file contains NO database logic.

Input:
    snapshot
    anomaly score

Output:
    LOW
    MEDIUM
    HIGH
    CRITICAL
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeverityResult:
    severity: str
    score: int


class SeverityCalculator:

    @staticmethod
    def calculate(snapshot: dict, anomaly_score: float) -> SeverityResult:

        cpu = float(snapshot.get("cpu_usage", 0))
        ram = float(snapshot.get("ram_usage", 0))
        disk = float(snapshot.get("disk_usage", 0))

        process_cpu = float(snapshot.get("top_process_cpu", 0))

        score = 0

        # ------------------------
        # CPU
        # ------------------------

        if cpu >= 95:
            score += 40
        elif cpu >= 85:
            score += 25
        elif cpu >= 70:
            score += 15

        # ------------------------
        # RAM
        # ------------------------

        if ram >= 95:
            score += 35
        elif ram >= 85:
            score += 20
        elif ram >= 70:
            score += 10

        # ------------------------
        # Disk
        # ------------------------

        if disk >= 95:
            score += 25
        elif disk >= 85:
            score += 15

        # ------------------------
        # Top process
        # ------------------------

        if process_cpu >= 70:
            score += 15

        # ------------------------
        # AI confidence
        # ------------------------

        score += int(anomaly_score * 30)

        # ------------------------

        if score >= 90:
            return SeverityResult(
                severity="CRITICAL",
                score=score,
            )

        if score >= 65:
            return SeverityResult(
                severity="HIGH",
                score=score,
            )

        if score >= 40:
            return SeverityResult(
                severity="MEDIUM",
                score=score,
            )

        return SeverityResult(
            severity="LOW",
            score=score,
        )
