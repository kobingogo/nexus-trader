import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import akshare as ak
from tenacity import retry, stop_after_attempt, wait_fixed
from sqlmodel import Session, select

from app.db.database import engine
from app.models.anomaly import AnomalyRecord

logger = logging.getLogger(__name__)

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
        Also persists new anomalies to DB.
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
            
            # Use current date for timestamp construction
            today_str = datetime.now().strftime("%Y-%m-%d")

            with Session(engine) as session:
                for _, row in df.iterrows():
                    try:
                        change_type = str(row["板块"])
                        code = str(row["代码"])
                        name = str(row["名称"])
                        time_str = str(row["时间"]) # HH:MM usually or HH:MM:SS
                        info_str = str(row.get("相关信息", ""))

                        # Apply filter (but maybe still persist all? For MVP, let's persist everything unique, return filtered)
                        # Actually to save space/time, maybe only persist if matches filter? 
                        # No, persist everything is safer for "Review".
                        
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

                        # Construct basic timestamp (approximate since year/sec might be missing)
                        # EastMoney time usually "10:05" or "10:05:32"
                        if len(time_str) == 5:
                            time_str += ":00"
                        
                        full_dt_str = f"{today_str} {time_str}"
                        dt_obj = datetime.strptime(full_dt_str, "%Y-%m-%d %H:%M:%S")

                        # Dedup check
                        # Check last few records for this code? Or just exact match?
                        # Since we poll every few seconds, we will see same items.
                        # Simple query:
                        existing = session.exec(
                            select(AnomalyRecord)
                            .where(AnomalyRecord.code == code)
                            .where(AnomalyRecord.timestamp == dt_obj)
                            .where(AnomalyRecord.type == internal_type)
                        ).first()

                        if not existing:
                            record = AnomalyRecord(
                                timestamp=dt_obj,
                                code=code,
                                name=name,
                                type=internal_type,
                                change_type=change_type,
                                price=price,
                                change_pct=change_pct,
                                amount=amount,
                                message=msg,
                                severity=severity
                            )
                            session.add(record)
                            session.commit() # Commit each to ensure ID is generated if needed, or commit batch at end? 
                            # Commit each is safer for uniqueness check in same loop if duplicates in same batch? 
                            # Actually list usually has one per event.
                        
                        # Add to return list if passes filter
                        if filter_codes is None or code in filter_codes:
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
                                "ts": int(dt_obj.timestamp()),
                            })

                    except Exception as e:
                        logger.error(f"Error processing anomaly row: {e}")
                        continue

        except Exception as e:
            logger.error(f"Error in anomaly scan: {e}")
            alerts.append({
                "type": "error",
                "message": f"扫描异常: {str(e)}",
                "severity": "low",
                "ts": int(time.time()),
            })

        # Sort by time descending
        alerts.sort(key=lambda x: x.get("ts", 0), reverse=True)

        return alerts


