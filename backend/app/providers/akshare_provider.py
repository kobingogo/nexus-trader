import akshare as ak
import pandas as pd
import time
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_fixed
from app.providers.base import MarketDataProvider

class AkShareProvider(MarketDataProvider):
    """
    Implementation of MarketDataProvider using AkShare (Open Source Financial Data).
    """

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def get_sector_heatmap_data(self) -> List[Dict[str, Any]]:
        """
        Fetch sector performance data for heatmap.
        Source: Tonghuashun (stock_board_industry_summary_ths)
        """
        try:
            df = ak.stock_board_industry_summary_ths()
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
                    continue 
            result.sort(key=lambda x: x['change_pct'], reverse=True)
            return result
        except Exception as e:
            print(f"[AkShareProvider] Error fetching heatmap: {e}")
            return []

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def get_leader_stocks_data(self) -> List[Dict[str, Any]]:
        """
        Fetch leader/popular stocks.
        Source: EastMoney Popularity Rank (stock_hot_rank_em)
        """
        try:
            df = ak.stock_hot_rank_em()
            result = []
            for _, row in df.iterrows():
                try:
                    change_pct = float(row['涨跌幅'])
                    raw_code = str(row['代码'])
                    code = raw_code[2:] if raw_code.startswith(("SZ", "SH", "BJ")) else raw_code
                    rank = int(row['当前排名'])

                    result.append({
                        "code": code,
                        "name": str(row['股票名称']),
                        "price": float(row['最新价']),
                        "change_pct": change_pct,
                        "turnover": 0, 
                        "volume_ratio": rank 
                    })
                except Exception:
                    continue
            return result
        except Exception as e:
            print(f"[AkShareProvider] Error fetching leaders: {e}")
            return []

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def get_market_activity_data(self) -> Dict[str, Any]:
        """
        Fetch market activity metrics (up/down count, limit up/down).
        Source: Legu (stock_market_activity_legu)
        """
        try:
            df = ak.stock_market_activity_legu()
            data = dict(zip(df['item'], df['value']))
            
            activity_str = data.get("活跃度", "0%").strip('%')
            activity = float(activity_str) if activity_str else 0.0

            return {
                "up_count": int(float(data.get("上涨", 0))),
                "down_count": int(float(data.get("下跌", 0))),
                "flat_count": int(float(data.get("平盘", 0))),
                "limit_up_count": int(float(data.get("涨停", 0))),
                "limit_down_count": int(float(data.get("跌停", 0))),
                "activity": activity,
                "ts": data.get("统计日期", "")
            }
        except Exception as e:
            print(f"[AkShareProvider] Error fetching market activity: {e}")
            return {}

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def get_economic_calendar(self, date_str: str = None) -> List[Dict[str, Any]]:
        """
        Fetch economic calendar events.
        Source: Baidu Economic Calendar (news_economic_baidu)
        """
        try:
            if not date_str:
                date_str = time.strftime("%Y%m%d")
            df = ak.news_economic_baidu(date=date_str)
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
            return result
        except Exception as e:
            print(f"[AkShareProvider] Error fetching macro events: {e}")
            return []

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def get_market_anomalies(self) -> List[Dict[str, Any]]:
        """
        Fetch real-time market anomalies.
        Source: EastMoney Anomaly (stock_changes_em)
        """
        try:
            df = ak.stock_changes_em()
            # We return raw records here, processing should happen in service
            result = []
            for _, row in df.iterrows():
                result.append({
                    "type": str(row["板块"]),
                    "code": str(row["代码"]),
                    "name": str(row["名称"]),
                    "time": str(row["时间"]),
                    "info": str(row.get("相关信息", ""))
                })
            return result
        except Exception as e:
            print(f"[AkShareProvider] Error fetching anomalies: {e}")
            return []
