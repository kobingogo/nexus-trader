from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from app.services.watchlist_service import WatchlistService
from app.services.watchlist_quotes import WatchlistQuoteService
from app.services.stock_search import search_stocks, get_stock_name

router = APIRouter()


class AddStockRequest(BaseModel):
    code: str
    name: Optional[str] = None
    tags: Optional[List[str]] = None


class UpdateTagsRequest(BaseModel):
    tags: List[str]


@router.get("/search")
def search_stock(q: str = Query(..., min_length=1, description="Search query (code or name)")):
    """Fuzzy search stocks by code or name."""
    results = search_stocks(q, limit=10)
    return {"results": results}


@router.get("")
def get_watchlist():
    watchlist = WatchlistService.get_watchlist()
    return {"data": watchlist}


@router.post("")
def add_stock(request: AddStockRequest):
    code = request.code.strip().zfill(6)
    name = request.name
    if not name:
        # Auto-resolve name from code
        name = get_stock_name(code) or code
    result = WatchlistService.add_stock(code, name.strip(), request.tags)
    return result


@router.delete("/{code}")
def remove_stock(code: str):
    result = WatchlistService.remove_stock(code)
    return result


@router.put("/{code}/tags")
def update_tags(code: str, request: UpdateTagsRequest):
    result = WatchlistService.update_tags(code, request.tags)
    return result


import asyncio

@router.get("/quotes")
def get_watchlist_quotes():
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
