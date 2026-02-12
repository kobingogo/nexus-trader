from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import AIService

router = APIRouter()

class DiagnoseRequest(BaseModel):
    ticker: str

@router.post("/diagnose")
async def diagnose_stock(request: DiagnoseRequest):
    report = AIService.diagnose_stock(request.ticker)
    return {
        "ticker": request.ticker,
        "report": report
    }
