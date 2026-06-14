"""
server/models.py
================

Data models used throughout LabPulse.

Two categories:
  1. Pydantic models  — FastAPI uses these to validate and serialise API responses.
  2. Plain dataclass  — used internally in the agent and TCP listener; no Pydantic overhead.

Academic note (OOP):
  ResourceSnapshot is a pure value object — it carries data but has no behaviour
  other than serialisation. ComputerResponse, etc. are Data Transfer Objects (DTOs)
  that decouple the HTTP layer from the raw database rows.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic models  (FastAPI response schemas)
# ══════════════════════════════════════════════════════════════════════════════

class ComputerResponse(BaseModel):
    """Represents one lab PC returned by GET /api/v1/computers."""
    id:         int
    pc_name:    str
    ip_address: Optional[str]
    last_seen:  Optional[datetime]
    status:     str

    model_config = {"from_attributes": True}


class ResourceSnapshotResponse(BaseModel):
    """One row from resource_snapshots, returned by GET /api/v1/history/{pc_name}."""
    id:          int
    computer_id: int
    cpu_usage:   float
    ram_usage:   float
    disk_usage:  float
    timestamp:   datetime

    model_config = {"from_attributes": True}


class LatestStatusResponse(BaseModel):
    """
    Aggregated view used by GET /api/v1/latest-status.
    Joins the most recent snapshot onto each computer row.
    """
    pc_name:    str
    ip_address: Optional[str]
    status:     str
    last_seen:  Optional[datetime]
    cpu_usage:  Optional[float]
    ram_usage:  Optional[float]
    disk_usage: Optional[float]

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    """One alert record, returned by GET /api/v1/alerts."""
    id:          int
    pc_name:     str           # joined from computers table
    alert_type:  str
    message:     str
    timestamp:   datetime

    model_config = {"from_attributes": True}


# ══════════════════════════════════════════════════════════════════════════════
# Internal dataclass  (agent → TCP listener)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ResourceSnapshot:
    """
    Value object that travels from the agent to the server as a JSON payload.

    Fields must stay in sync with what agent/collector.py produces and what
    server/main.py's process_agent_payload() expects.
    """
    hostname:   str
    cpu_usage:  float
    ram_usage:  float
    disk_usage: float
    timestamp:  str              # ISO-8601 UTC string

    def to_dict(self) -> dict:
        """Serialise to a plain dict for JSON encoding."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResourceSnapshot":
        """Deserialise from the dict produced by json.loads()."""
        return cls(
            hostname=data["hostname"],
            cpu_usage=float(data["cpu_usage"]),
            ram_usage=float(data["ram_usage"]),
            disk_usage=float(data["disk_usage"]),
            timestamp=data.get("timestamp", ""),
        )
