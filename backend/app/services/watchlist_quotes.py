import akshare as ak
import time
from typing import List, Dict, Any
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, wait_fixed
from app.services.market_data import Cache


class WatchlistQuoteService:
    """
    Service to fetch real-time quotes and recent history for watchlist stocks.
    Uses stock_zh_a_hist (日K线) which is fast and reliable.
    """

    @staticmethod
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def _fetch_stock_hist(code: str, days: int = 10) -> Dict[str, Any]:
        """Fetch recent daily K-line data for a single stock."""
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days + 15)).strftime("%Y%m%d")  # extra buffer for weekends

        df = ak.stock_zh_a_hist(
            symbol=code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )

        if df.empty:
            return None

        # Get the latest row (today or last trading day)
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest

        # Build sparkline data (last N days close prices)
        sparkline = df["收盘"].tolist()[-days:]

        return {
            "code": code,
            "name": "",  # Will be filled by caller
            "price": float(latest["收盘"]),
            "open": float(latest["开盘"]),
            "high": float(latest["最高"]),
            "low": float(latest["最低"]),
            "prev_close": float(prev["收盘"]),
            "change_pct": float(latest["涨跌幅"]),
            "change_amt": float(latest["涨跌额"]),
            "volume": int(latest["成交量"]),
            "amount": float(latest["成交额"]),
            "turnover": float(latest["换手率"]),
            "amplitude": float(latest["振幅"]),
            "sparkline": sparkline,
            "date": str(latest["日期"]),
        }

    @staticmethod
    def get_quotes(watchlist: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Get quotes for all watchlist stocks.
        Uses cache to avoid hammering the API.
        """
        quotes = []

        for stock in watchlist:
            code = stock["code"]
            name = stock.get("name", "")
            tags = stock.get("tags", [])

            cache_key = f"quote_{code}"
            cached = Cache.get(cache_key)

            if cached:
                cached["name"] = name
                cached["tags"] = tags
                quotes.append(cached)
                continue

            try:
                quote = WatchlistQuoteService._fetch_stock_hist(code, days=10)
                if quote:
                    quote["name"] = name
                    quote["tags"] = tags
                    Cache.set(cache_key, quote, ttl=30)  # Cache 30s
                    quotes.append(quote)
            except Exception as e:
                print(f"Error fetching quote for {code}: {e}")
                # Append a fallback entry
                quotes.append({
                    "code": code,
                    "name": name,
                    "tags": tags,
                    "price": 0,
                    "change_pct": 0,
                    "sparkline": [],
                    "error": str(e),
                })

        return quotes

    @staticmethod
    def get_portfolio_summary(quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate portfolio-level summary stats from quotes.
        """
        valid_quotes = [q for q in quotes if q.get("price", 0) > 0]

        if not valid_quotes:
            return {
                "total_stocks": len(quotes),
                "gainers": 0,
                "losers": 0,
                "flat": 0,
                "avg_change_pct": 0,
                "best_stock": None,
                "worst_stock": None,
                "total_amount": 0,
            }

        gainers = [q for q in valid_quotes if q.get("change_pct", 0) > 0]
        losers = [q for q in valid_quotes if q.get("change_pct", 0) < 0]
        flat = [q for q in valid_quotes if q.get("change_pct", 0) == 0]

        avg_change = sum(q.get("change_pct", 0) for q in valid_quotes) / len(valid_quotes)
        total_amount = sum(q.get("amount", 0) for q in valid_quotes)

        best = max(valid_quotes, key=lambda q: q.get("change_pct", 0))
        worst = min(valid_quotes, key=lambda q: q.get("change_pct", 0))

        return {
            "total_stocks": len(quotes),
            "gainers": len(gainers),
            "losers": len(losers),
            "flat": len(flat),
            "avg_change_pct": round(avg_change, 2),
            "best_stock": {"code": best["code"], "name": best["name"], "change_pct": best["change_pct"]},
            "worst_stock": {"code": worst["code"], "name": worst["name"], "change_pct": worst["change_pct"]},
            "total_amount": round(total_amount, 2),
        }
