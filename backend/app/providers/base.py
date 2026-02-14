from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class MarketDataProvider(ABC):
    """
    Abstract Base Class for Market Data Providers.
    All data sources (AkShare, Tushare, etc.) must implement this interface.
    """

    @abstractmethod
    def get_sector_heatmap_data(self) -> List[Dict[str, Any]]:
        """
        Fetch sector performance data for heatmap.
        Expected return format: [{"name": str, "change_pct": float, "market_cap": float, "leader_name": str, "leader_change": float}, ...]
        """
        pass

    @abstractmethod
    def get_leader_stocks_data(self) -> List[Dict[str, Any]]:
        """
        Fetch leader/popular stocks.
        Expected return format: [{"code": str, "name": str, "price": float, "change_pct": float, "volume_ratio": float}, ...]
        """
        pass

    @abstractmethod
    def get_market_activity_data(self) -> Dict[str, Any]:
        """
        Fetch market activity metrics (up/down count, limit up/down).
        Expected return format: {"up": int, "down": int, "limit_up": int, "limit_down": int, "flat": int, "activity": float}
        """
        pass

    @abstractmethod
    def get_economic_calendar(self, date_str: str = None) -> List[Dict[str, Any]]:
        """
        Fetch economic calendar events.
        """
        pass

    @abstractmethod
    def get_market_anomalies(self) -> List[Dict[str, Any]]:
        """
        Fetch real-time market anomalies (rocket, dive, big order).
        """
        pass
