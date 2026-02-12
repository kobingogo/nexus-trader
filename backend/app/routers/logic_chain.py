
from fastapi import APIRouter, HTTPException, Query
from app.services.logic_chain import LogicChainService
from typing import List, Dict, Any
import asyncio

router = APIRouter()

@router.get("/search")
async def search_concepts(q: str = Query(..., min_length=1)):
    """
    Search for concepts matching the query.
    """
    # Run in thread pool to avoid blocking
    concepts = await asyncio.to_thread(LogicChainService.search_concepts, q)
    return {"concepts": concepts}

@router.get("/analyze")
async def analyze_logic(q: str = Query(..., min_length=1)):
    """
    Analyze the logic chain for a given query (concept or news keyword).
    Returns matched concept and leading stocks.
    """
    result = await asyncio.to_thread(LogicChainService.analyze_logic_chain, q)
    return result

@router.get("/concepts")
async def get_all_concepts():
    """
    Get all available concepts (cached).
    """
    concepts = await asyncio.to_thread(LogicChainService.get_all_concepts)
    return {"count": len(concepts), "concepts": concepts[:100]} # Limit to 100 for preview
