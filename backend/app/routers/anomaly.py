from fastapi import APIRouter, Query
from app.services.anomaly_service import AnomalyDetector

router = APIRouter()

@router.get("/scan")
async def scan_anomalies(filter: str = Query("all", description="Filter mode: all, watchlist, leaders")):
    alerts = AnomalyDetector.scan_all(filter_mode=filter)
    return {"data": alerts, "count": len(alerts), "filter": filter}
