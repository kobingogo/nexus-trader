from fastapi import APIRouter
from app.services.agent_service import AgentService

router = APIRouter()

@router.get("/signals")
def get_signals(limit: int = 10):
    """Get latest agent signals."""
    signals = AgentService.get_latest_signals(limit=limit)
    return {"data": signals}
