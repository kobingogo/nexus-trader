import akshare as ak
import pandas as pd
from typing import List, Dict, Any, Optional
import os
import time
import random
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_fixed
import signal
from contextlib import contextmanager

# Timeout helper using signal (Unix only)
@contextmanager
def timeout(seconds):
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")
    
    # Set the signal handler and alarm
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)  # Disable alarm
        signal.signal(signal.SIGALRM, old_handler)

# Simple in-memory cache with expiry
class Cache:
    _data = {}
    _expiry = {}

    @classmethod
    def get(cls, key):
        if key in cls._data and time.time() < cls._expiry.get(key, 0):
            return cls._data[key]
        return None

    @classmethod
    def set(cls, key, value, ttl=60):
        cls._data[key] = value
        cls._expiry[key] = time.time() + ttl

class MarketDataService:
    @staticmethod
    def _get_mock_heatmap():
        return [
            {"name": "半导体", "code": "BK01", "change_pct": 5.2, "market_cap": 2000, "turnover": 3.5, "leader_name": "中芯国际", "leader_change": 10.1},
            {"name": "人工智能", "code": "BK02", "change_pct": 3.8, "market_cap": 1500, "turnover": 4.1, "leader_name": "科大讯飞", "leader_change": 9.8},
            {"name": "新能源车", "code": "BK03", "change_pct": -1.2, "market_cap": 3000, "turnover": 2.2, "leader_name": "比亚迪", "leader_change": -0.5},
            {"name": "房地产", "code": "BK04", "change_pct": -2.5, "market_cap": 1000, "turnover": 1.5, "leader_name": "万科A", "leader_change": -1.8},
        ]

    @staticmethod
    def _get_mock_leaders():
        return [
            {"code": "600519", "name": "贵州茅台 (Mock)", "price": 1800.00, "change_pct": 1.5, "turnover": 0.5, "volume_ratio": 1.2},
            {"code": "300750", "name": "宁德时代 (Mock)", "price": 200.00, "change_pct": 3.2, "turnover": 1.8, "volume_ratio": 2.5},
            {"code": "002594", "name": "比亚迪 (Mock)", "price": 250.00, "change_pct": -0.5, "turnover": 1.2, "volume_ratio": 0.8},
        ]

    @staticmethod
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def fetch_heatmap_data():
        # Source: Tonghuashun (Faster/Alternative)
        with timeout(10):  # 10 second timeout
            return ak.stock_board_industry_summary_ths()

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
            print(f"Error loading stock codes: {e}")

    @staticmethod
    def get_code_by_name(name: str) -> str:
        MarketDataService._load_stock_codes()
        return MarketDataService._stock_codes_map.get(name, "")

    @staticmethod
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def fetch_leaders_data():
        # Source: EastMoney Popularity Rank (Recent Popular)
        with timeout(10):  # 10 second timeout
            return ak.stock_hot_rank_em()

    @staticmethod
    def get_sector_heatmap() -> List[Dict[str, Any]]:
        cached = Cache.get("heatmap")
        if cached:
            return cached

        try:
            # 获取行业板块行情 (THS)
            df = MarketDataService.fetch_heatmap_data()
            
            result = []
            for _, row in df.iterrows():
                try:
                    result.append({
                        "name": row['板块'],
                        "code": row['板块'],
                        "change_pct": float(row['涨跌幅']),
                        "market_cap": float(row['总成交额']) * 100, 
                        "turnover": 0,
                        "leader_name": row['领涨股'],
                        "leader_change": float(row['领涨股-涨跌幅'])
                    })
                except Exception:
                    continue # Skip rows with bad data
            
            result.sort(key=lambda x: x['change_pct'], reverse=True)
            Cache.set("heatmap", result, ttl=300)  # Extended to 5 minutes
            return result
        except Exception as e:
            print(f"Error fetching heatmap: {e}")
            mock_data = MarketDataService._get_mock_heatmap()
            Cache.set("heatmap", mock_data, ttl=30) # Cache mock data for 30s
            return mock_data

    @staticmethod
    def get_leader_stocks() -> List[Dict[str, Any]]:
        cached = Cache.get("leaders")
        if cached:
            return cached

        try:
            # Use EastMoney Popularity Rank (stock_hot_rank_em)
            # Columns: 当前排名, 代码, 股票名称, 最新价, 涨跌额, 涨跌幅
            df = MarketDataService.fetch_leaders_data()
            
            result = []
            for _, row in df.iterrows():
                try:
                    # Filter for Strong Stocks (Leader/Core) logic:
                    # 1. Must be Popular (Top 100 returned by API usually)
                    # 2. Must be Strong (Change Pct > 3.0 or even higher) to be a "Leader"
                    change_pct = float(row['涨跌幅'])
                    if change_pct < 3.0:
                        continue

                    # Code format "SZ00xxxx", need to strip prefix
                    raw_code = str(row['代码'])
                    code = raw_code[2:] if raw_code.startswith(("SZ", "SH", "BJ")) else raw_code
                    
                    # Rank is essentially volume_ratio here for display or we can put rank in volume_ratio
                    rank = int(row['当前排名'])

                    result.append({
                        "code": code,
                        "name": str(row['股票名称']),
                        "price": float(row['最新价']),
                        "change_pct": change_pct,
                        "turnover": 0, # Hot rank doesn't have turnover, set 0
                        "volume_ratio": rank # Reuse to show Popularity Rank 
                    })
                except Exception:
                    continue

            # Limit to top 30 filtered
            result = result[:30]
            
            Cache.set("leaders", result, ttl=300)  # Extended to 5 minutes
            return result
        except Exception as e:
            print(f"Error fetching leaders: {e}")
            mock_data = MarketDataService._get_mock_leaders()
            Cache.set("leaders", mock_data, ttl=30)
            return mock_data

    @staticmethod
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def fetch_market_activity():
        # Source: Legu Market Activity (Up/Down/LimitUp/LimitDown)
        with timeout(10):  # 10 second timeout
            return ak.stock_market_activity_legu()

    @staticmethod
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def fetch_economic_calendar():
        # Source: Baidu Economic Calendar
        today = time.strftime("%Y%m%d")
        with timeout(10):  # 10 second timeout
            return ak.news_economic_baidu(date=today)

    @staticmethod
    def get_market_sentiment() -> Dict[str, Any]:
        cached = Cache.get("sentiment")
        if cached:
            return cached

        try:
            df = MarketDataService.fetch_market_activity()
            # items: 上涨, 涨停, 下跌, 跌停, 平盘, 活跃度, 统计日期
            # Convert to dict
            data = dict(zip(df['item'], df['value']))
            
            activity_str = data.get("活跃度", "0%").strip('%')
            activity = float(activity_str) if activity_str else 0.0

            result = {
                "up_count": int(float(data.get("上涨", 0))),
                "down_count": int(float(data.get("下跌", 0))),
                "flat_count": int(float(data.get("平盘", 0))),
                "limit_up_count": int(float(data.get("涨停", 0))),
                "limit_down_count": int(float(data.get("跌停", 0))),
                "activity": activity,
                "temperature": activity, # Use activity as temperature for now
                "ts": data.get("统计日期", "")
            }
            Cache.set("sentiment", result, ttl=300)  # Extended to 5 minutes
            return result
        except Exception as e:
            print(f"Error fetching sentiment: {e}")
            error_data = {
                "up_count": 0, "down_count": 0, "flat_count": 0,
                "limit_up_count": 0, "limit_down_count": 0, 
                "activity": 0.0, "temperature": 0.0,
                "error": str(e)
            }
            Cache.set("sentiment", error_data, ttl=10) # Cache error for 10s
            return error_data

    @staticmethod
    def get_macro_events() -> List[Dict[str, Any]]:
        cached = Cache.get("macro")
        if cached:
            return cached

        try:
            df = MarketDataService.fetch_economic_calendar()
            # Columns: 日期, 时间, 地区, 事件, 公布, 预期, 前值, 重要性
            
            # Replace NaN with empty string for JSON compatibility
            df = df.fillna("")
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    "time": row['时间'],
                    "country": row['地区'],
                    "event": row['事件'],
                    "actual": row['公布'],
                    "forecast": row['预期'],
                    "previous": row['前值'],
                    "importance": row['重要性']
                })
            
            # Sort by time? Usually already sorted.
            Cache.set("macro", result, ttl=3600) # Cache for 1 hour
            return result
        except Exception as e:
            print(f"Error fetching macro: {e}")
            return []
