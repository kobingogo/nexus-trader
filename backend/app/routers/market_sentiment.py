
from fastapi import APIRouter
import asyncio
from app.services.market_sentiment import MarketSentimentService

router = APIRouter()

@router.get("/sentiment-radar")
async def get_market_sentiment():
    """
    Get real-time market sentiment metrics.
    """
    # Run synchronous service in thread pool
    data = await asyncio.to_thread(MarketSentimentService.get_market_sentiment)
    return data
