import akshare as ak
import time
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed


# Mapping EastMoney anomaly types to our internal types
TYPE_MAP = {
    "火箭发射": "rocket",
    "快速反弹": "rocket",
    "封涨停板": "rocket",
    "大笔买入": "big_order_buy",
    "加速下跌": "dive",
    "高台跳水": "dive",
    "封跌停板": "dive",
    "大笔卖出": "big_order_sell",
    "打开涨停板": "dive",
    "打开跌停板": "rocket",
    "有大买盘": "big_order_buy",
    "有大卖盘": "big_order_sell",
    "竞价上涨": "rocket",
    "竞价下跌": "dive",
}

EMOJI_MAP = {
    "rocket": "🚀",
    "big_order_buy": "💰",
    "dive": "☢️",
    "big_order_sell": "💸",
}

SEVERITY_MAP = {
    "火箭发射": "high",
    "快速反弹": "medium",
    "封涨停板": "high",
    "大笔买入": "medium",
    "加速下跌": "high",
    "高台跳水": "high",
    "封跌停板": "high",
    "大笔卖出": "medium",
    "打开涨停板": "high",
    "打开跌停板": "medium",
    "有大买盘": "medium",
    "有大卖盘": "medium",
    "竞价上涨": "low",
    "竞价下跌": "low",
}


class AnomalyDetector:
    """
    Anomaly Detector using EastMoney's built-in anomaly stream (stock_changes_em).
    This is far more reliable than manually computing deltas from full market snapshots.
    """

    @staticmethod
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def _fetch_changes():
        """Fetch EastMoney real-time anomaly data."""
        return ak.stock_changes_em()

    @staticmethod
    def _parse_info(info_str: str, change_type: str) -> Dict[str, Any]:
        """
        Parse the '相关信息' field.
        Format varies by type, typically: volume,price,change_pct,amount
        """
        extra = {}
        try:
            parts = info_str.split(",")
            if len(parts) >= 4:
                extra["volume"] = int(float(parts[0]))       # 成交量(股)
                extra["price"] = float(parts[1])              # 成交价
                extra["change_pct"] = float(parts[2]) * 100   # 涨跌幅 (已是小数, 转百分比)
                extra["amount"] = float(parts[3])             # 成交额(元)
            elif len(parts) >= 2:
                extra["price"] = float(parts[0])
                extra["change_pct"] = float(parts[1]) * 100
        except Exception:
            pass
        return extra

    @staticmethod
    def scan_all(filter_mode: str = "all") -> List[Dict[str, Any]]:
        """
        Main scan: fetches EastMoney anomaly stream and formats it.
        
        filter_mode:
          - "all": return all anomalies
          - "watchlist": only return anomalies for watched stocks
          - "leaders": only return anomalies for current leader stocks
          
        Results are sorted by time descending (newest first).
        """
        alerts: List[Dict[str, Any]] = []

        # Pre-load filter sets
        filter_codes: set | None = None
        if filter_mode == "watchlist":
            from app.services.watchlist_service import WatchlistService
            filter_codes = WatchlistService.get_codes()
            if not filter_codes:
                return []  # No watchlist stocks
        elif filter_mode == "leaders":
            from app.services.market_data import MarketDataService
            leaders = MarketDataService.get_leader_stocks()
            filter_codes = {str(l["code"]) for l in leaders} if leaders else set()

        try:
            df = AnomalyDetector._fetch_changes()

            for _, row in df.iterrows():
                try:
                    change_type = str(row["板块"])
                    code = str(row["代码"])
                    name = str(row["名称"])
                    time_str = str(row["时间"])
                    info_str = str(row.get("相关信息", ""))

                    # Apply filter
                    if filter_codes is not None and code not in filter_codes:
                        continue

                    internal_type = TYPE_MAP.get(change_type, "rocket")
                    severity = SEVERITY_MAP.get(change_type, "low")
                    emoji = EMOJI_MAP.get(internal_type, "⚡")

                    extra = AnomalyDetector._parse_info(info_str, change_type)
                    price = extra.get("price", 0)
                    change_pct = extra.get("change_pct", 0)
                    amount = extra.get("amount", 0)

                    # Build human-readable message
                    if internal_type == "rocket":
                        msg = f"{emoji} {change_type}！{name}({code}) 涨幅 {change_pct:+.1f}%，现价 ¥{price}"
                    elif internal_type == "dive":
                        msg = f"{emoji} {change_type}！{name}({code}) 跌幅 {change_pct:+.1f}%，现价 ¥{price}"
                    elif internal_type == "big_order_buy":
                        amount_wan = amount / 10000
                        msg = f"{emoji} {change_type}！{name}({code}) 成交额 {amount_wan:.0f}万，涨幅 {change_pct:+.1f}%"
                    elif internal_type == "big_order_sell":
                        amount_wan = amount / 10000
                        msg = f"{emoji} {change_type}！{name}({code}) 成交额 {amount_wan:.0f}万，跌幅 {change_pct:+.1f}%"
                    else:
                        msg = f"⚡ {change_type}！{name}({code})"

                    alerts.append({
                        "type": internal_type,
                        "change_type": change_type,
                        "code": code,
                        "name": name,
                        "price": price,
                        "change_pct": round(change_pct, 2),
                        "amount": round(amount, 2),
                        "message": msg,
                        "severity": severity,
                        "time": time_str,
                        "ts": int(time.time()),
                    })
                except Exception:
                    continue

            # Sort by time descending (newest first)
            alerts.sort(key=lambda x: x.get("time", ""), reverse=True)

            # Limit to top 100 for "all", 50 for filtered
            limit = 50 if filter_mode != "all" else 100
            alerts = alerts[:limit]

        except Exception as e:
            print(f"Error in anomaly scan: {e}")
            alerts.append({
                "type": "error",
                "message": f"扫描异常: {str(e)}",
                "severity": "low",
                "ts": int(time.time()),
            })

        return alerts

