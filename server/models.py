"""
server/models.py
================

Pydantic response models and the internal snapshot dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class ComputerResponse(BaseModel):
    id: int
    pc_name: str
    ip_address: Optional[str]
    last_seen: Optional[datetime]
    status: str

    model_config = {"from_attributes": True}


class ResourceSnapshotResponse(BaseModel):
    id: int
    computer_id: int
    cpu_usage: float
    ram_usage: float
    disk_usage: float
    network_sent: Optional[float] = None
    network_recv: Optional[float] = None
    boot_time: Optional[int] = None
    process_count: Optional[int] = None
    top_process_name: Optional[str] = None
    top_process_cpu: Optional[float] = None
    top_process_memory: Optional[float] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class SnapshotWithHealthResponse(ResourceSnapshotResponse):
    health_score: Optional[float] = None
    health_status: Optional[str] = None

    model_config = {"from_attributes": True}


class LatestStatusResponse(BaseModel):
    pc_name: str
    ip_address: Optional[str]
    status: str
    last_seen: Optional[datetime]
    cpu_usage: Optional[float]
    ram_usage: Optional[float]
    disk_usage: Optional[float]
    network_sent: Optional[float] = None
    network_recv: Optional[float] = None
    boot_time: Optional[int] = None
    process_count: Optional[int] = None
    top_process_name: Optional[str] = None
    top_process_cpu: Optional[float] = None
    top_process_memory: Optional[float] = None
    timestamp: Optional[datetime] = None
    health_score: Optional[float] = None
    health_status: Optional[str] = None

    model_config = {"from_attributes": True}


class AlertResponse(BaseModel):
    id: int
    pc_name: str
    alert_type: str
    message: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class MachineDetailResponse(BaseModel):
    computer: ComputerResponse
    latest_snapshot: Optional[SnapshotWithHealthResponse] = None
    history: List[SnapshotWithHealthResponse] = []

    model_config = {"from_attributes": True}


@dataclass
class ResourceSnapshot:
    hostname: str
    cpu_usage: float
    ram_usage: float
    disk_usage: float
    network_sent: float
    network_recv: float
    boot_time: int
    process_count: int
    top_process_name: Optional[str]
    top_process_cpu: float
    top_process_memory: float
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResourceSnapshot":
        return cls(
            hostname=data["hostname"],
            cpu_usage=float(data["cpu_usage"]),
            ram_usage=float(data["ram_usage"]),
            disk_usage=float(data["disk_usage"]),
            network_sent=float(data.get("network_sent", 0.0)),
            network_recv=float(data.get("network_recv", 0.0)),
            boot_time=int(data.get("boot_time", 0)),
            process_count=int(data.get("process_count", 0)),
            top_process_name=data.get("top_process_name"),
            top_process_cpu=float(data.get("top_process_cpu", 0.0)),
            top_process_memory=float(data.get("top_process_memory", 0.0)),
            timestamp=data.get("timestamp", ""),
        )
