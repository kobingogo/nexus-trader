from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.review_service import DailyReviewService

router = APIRouter()

@router.get("/daily")
async def get_daily_review():
    return StreamingResponse(
        DailyReviewService.stream_review(),
        media_type="application/x-ndjson"
    )
