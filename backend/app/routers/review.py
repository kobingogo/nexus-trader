from fastapi import APIRouter
from app.services.review_service import DailyReviewService

router = APIRouter()

@router.get("/daily")
async def get_daily_review():
    result = DailyReviewService.generate_review()
    return {"data": result}
