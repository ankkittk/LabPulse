from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthAssessment:
    score: float
    status: str


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def assess_health(
    cpu_usage: float | None,
    ram_usage: float | None,
    disk_usage: float | None,
    process_count: int | None = None,
    top_process_cpu: float | None = None,
    top_process_memory: float | None = None,
) -> HealthAssessment:
    """
    Simple, explainable health score for monitoring dashboards.

    100 = excellent
    0   = critical
    """
    if cpu_usage is None or ram_usage is None or disk_usage is None:
        return HealthAssessment(score=0.0, status="unknown")

    cpu = _clamp(float(cpu_usage), 0.0, 100.0)
    ram = _clamp(float(ram_usage), 0.0, 100.0)
    disk = _clamp(float(disk_usage), 0.0, 100.0)

    process_penalty = 0.0
    if process_count is not None:
        process_penalty = _clamp(process_count / 250.0, 0.0, 1.0) * 5.0

    top_cpu_penalty = 0.0
    if top_process_cpu is not None:
        top_cpu_penalty = _clamp(float(top_process_cpu) / 100.0, 0.0, 1.0) * 5.0

    top_mem_penalty = 0.0
    if top_process_memory is not None:
        top_mem_penalty = _clamp(float(top_process_memory) / 100.0, 0.0, 1.0) * 5.0

    raw_score = 100.0 - (
        (cpu * 0.35)
        + (ram * 0.35)
        + (disk * 0.20)
        + process_penalty
        + top_cpu_penalty
        + top_mem_penalty
    )

    score = round(_clamp(raw_score, 0.0, 100.0), 2)

    if score >= 80:
        status = "healthy"
    elif score >= 60:
        status = "warning"
    else:
        status = "critical"

    return HealthAssessment(score=score, status=status)
