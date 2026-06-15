from fastapi import APIRouter

from server.database import DatabaseManager

router = APIRouter()

db = DatabaseManager()


@router.get("/computers")
def get_computers():
    return db.get_all_computers()


@router.get("/latest-status")
def get_latest_status():
    return db.get_latest_status()


@router.get("/alerts")
def get_alerts():
    return db.get_recent_alerts()
