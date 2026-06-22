from fastapi import APIRouter, HTTPException, Query

from server.database import DatabaseManager
from server.models import (
    ComputerResponse,
    LatestStatusResponse,
    AlertResponse,
    SnapshotWithHealthResponse,
    MachineDetailResponse,
)

router = APIRouter()
db = DatabaseManager()


@router.get("/computers", response_model=list[ComputerResponse])
def get_computers():
    return db.get_all_computers()


@router.get("/latest-status", response_model=list[LatestStatusResponse])
def get_latest_status():
    return db.get_latest_status()


@router.get("/alerts", response_model=list[AlertResponse])
def get_alerts():
    return db.get_recent_alerts()


@router.get("/history/{pc_name}", response_model=list[SnapshotWithHealthResponse])
def get_history(pc_name: str, limit: int = Query(50, ge=1, le=500)):
    if not db.get_computer_by_name(pc_name):
        raise HTTPException(status_code=404, detail=f"Computer {pc_name} not found")
    return db.get_history(pc_name, limit)


@router.get("/machine/{pc_name}", response_model=MachineDetailResponse)
def get_machine(pc_name: str, limit: int = Query(50, ge=1, le=500)):
    details = db.get_machine_details(pc_name, limit)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Computer {pc_name} not found")
    return details
