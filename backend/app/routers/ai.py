import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_service import AIService

router = APIRouter()

class DiagnoseRequest(BaseModel):
    ticker: str

from fastapi.responses import StreamingResponse

@router.get("/diagnose/{ticker}")
async def diagnose_stock_stream(ticker: str):
    return StreamingResponse(
        AIService.stream_diagnose_stock(ticker),
        media_type="application/x-ndjson"
    )

@router.post("/diagnose")
async def diagnose_stock(request: DiagnoseRequest):
    # Run synchronous LLM call in thread pool to avoid blocking event loop
    report = await asyncio.to_thread(AIService.diagnose_stock, request.ticker)
    return {
        "ticker": request.ticker,
        "report": report
    }
