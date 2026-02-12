from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.watchlist_service import WatchlistService
from app.services.watchlist_quotes import WatchlistQuoteService

router = APIRouter()


class AddStockRequest(BaseModel):
    code: str
    name: str
    tags: Optional[List[str]] = None


class UpdateTagsRequest(BaseModel):
    tags: List[str]


@router.get("")
async def get_watchlist():
    watchlist = WatchlistService.get_watchlist()
    return {"data": watchlist}


@router.post("")
async def add_stock(request: AddStockRequest):
    result = WatchlistService.add_stock(request.code, request.name, request.tags)
    return result


@router.delete("/{code}")
async def remove_stock(code: str):
    result = WatchlistService.remove_stock(code)
    return result


@router.put("/{code}/tags")
async def update_tags(code: str, request: UpdateTagsRequest):
    result = WatchlistService.update_tags(code, request.tags)
    return result


@router.get("/quotes")
async def get_watchlist_quotes():
    """Get real-time quotes and portfolio summary for all watchlist stocks."""
    watchlist = WatchlistService.get_watchlist()
    if not watchlist:
        return {
            "quotes": [],
            "summary": {
                "total_stocks": 0,
                "gainers": 0,
                "losers": 0,
                "flat": 0,
                "avg_change_pct": 0,
                "best_stock": None,
                "worst_stock": None,
                "total_amount": 0,
            }
        }

    quotes = WatchlistQuoteService.get_quotes(watchlist)
    summary = WatchlistQuoteService.get_portfolio_summary(quotes)
    return {"quotes": quotes, "summary": summary}
