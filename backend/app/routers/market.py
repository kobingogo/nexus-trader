from fastapi import APIRouter, HTTPException
from app.services.market_data import MarketDataService

router = APIRouter()

import asyncio

@router.get("/heatmap")
async def get_sector_heatmap():
    data = await asyncio.to_thread(MarketDataService.get_sector_heatmap)
    if not data:
        return {"data": [], "message": "No data available or fetch failed"}
    return {"data": data}

@router.get("/leaders")
async def get_leader_stocks():
    data = await asyncio.to_thread(MarketDataService.get_leader_stocks)
    if not data:
        return {"data": [], "message": "No data available or fetch failed"}
    return {"data": data}

@router.get("/sentiment")
async def get_market_sentiment():
    data = await asyncio.to_thread(MarketDataService.get_market_sentiment)
    return {"data": data}

@router.get("/macro")
async def get_macro_events():
    data = await asyncio.to_thread(MarketDataService.get_macro_events)
    return {"data": data}
