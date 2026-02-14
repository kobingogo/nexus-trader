import logging
import pandas as pd
from typing import List, Dict, Any, Optional
import os
import time
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_fixed
from app.utils.cache import ttl_cache

# Import Provider
from app.providers.akshare_provider import AkShareProvider

logger = logging.getLogger(__name__)

# Mock Data (Keep for fallback)
def _get_mock_heatmap():
    return [
        {"name": "半导体", "code": "BK01", "change_pct": 5.2, "market_cap": 2000, "turnover": 3.5, "leader_name": "中芯国际", "leader_change": 10.1},
        {"name": "人工智能", "code": "BK02", "change_pct": 3.8, "market_cap": 1500, "turnover": 4.1, "leader_name": "科大讯飞", "leader_change": 9.8},
        {"name": "新能源车", "code": "BK03", "change_pct": -1.2, "market_cap": 3000, "turnover": 2.2, "leader_name": "比亚迪", "leader_change": -0.5},
        {"name": "房地产", "code": "BK04", "change_pct": -2.5, "market_cap": 1000, "turnover": 1.5, "leader_name": "万科A", "leader_change": -1.8},
    ]

def _get_mock_leaders():
    return [
        {"code": "600519", "name": "贵州茅台 (Mock)", "price": 1800.00, "change_pct": 1.5, "turnover": 0.5, "volume_ratio": 1.2},
        {"code": "300750", "name": "宁德时代 (Mock)", "price": 200.00, "change_pct": 3.2, "turnover": 1.8, "volume_ratio": 2.5},
        {"code": "002594", "name": "比亚迪 (Mock)", "price": 250.00, "change_pct": -0.5, "turnover": 1.2, "volume_ratio": 0.8},
    ]

class MarketDataService:
    # Initialize Provider
    _provider = AkShareProvider()
    
    # Cache for stock codes map
    _stock_codes_map = {}

    @staticmethod
    def _load_stock_codes():
        if MarketDataService._stock_codes_map:
            return
        try:
            csv_path = os.path.join(os.path.dirname(__file__), "../stock_codes.csv")
            if os.path.exists(csv_path):
                df = pd.read_csv(csv_path, dtype=str)
                # Map name to code
                MarketDataService._stock_codes_map = dict(zip(df['name'], df['code']))
        except Exception as e:
            logger.error(f"Error loading stock codes: {e}")

    @staticmethod
    def get_code_by_name(name: str) -> str:
        MarketDataService._load_stock_codes()
        return MarketDataService._stock_codes_map.get(name, "")

    @staticmethod
    @ttl_cache(ttl=300) # Cache 5 mins
    def get_sector_heatmap() -> List[Dict[str, Any]]:
        try:
            data = MarketDataService._provider.get_sector_heatmap_data()
            if not data:
                return _get_mock_heatmap()
            return data
        except Exception as e:
            logger.error(f"Error serving heatmap: {e}")
            return _get_mock_heatmap()

    @staticmethod
    @ttl_cache(ttl=60) # Cache 1 min
    def get_leader_stocks() -> List[Dict[str, Any]]:
        try:
            data = MarketDataService._provider.get_leader_stocks_data()
            
            # Post-processing filter (logic moved here or keep in provider? Provider gave raw-ish data)
            # Provider returns {code, name, price, change_pct, volume_ratio}
            # We filter for strong stocks (> 3%)
            
            filtered = [s for s in data if s['change_pct'] >= 3.0]
            
            # Limit to top 30
            return filtered[:30] if filtered else _get_mock_leaders()
        except Exception as e:
            logger.error(f"Error serving leaders: {e}")
            return _get_mock_leaders()

    @staticmethod
    @ttl_cache(ttl=60)
    def get_market_sentiment() -> Dict[str, Any]:
        """
        Get market sentiment metrics.
        """
        try:
            data = MarketDataService._provider.get_market_activity_data()
            if not data:
                 return {
                    "up_count": 0, "down_count": 0, "flat_count": 0,
                    "limit_up_count": 0, "limit_down_count": 0, 
                    "activity": 0.0, "temperature": 0.0,
                    "ts": ""
                }
            
            # Add temperature alias
            data["temperature"] = data.get("activity", 0.0)
            return data
        except Exception as e:
             logger.error(f"Error serving sentiment: {e}")
             return {}

    @staticmethod
    @ttl_cache(ttl=3600)
    def get_macro_events() -> List[Dict[str, Any]]:
        try:
            return MarketDataService._provider.get_economic_calendar()
        except Exception as e:
            logger.error(f"Error serving macro events: {e}")
            return []

