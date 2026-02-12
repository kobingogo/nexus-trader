import os
import time
import re
import requests
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_fixed
from app.services.market_data import Cache

# Session with no system proxy for direct connections
_session = requests.Session()
_session.trust_env = False
_session.headers.update({
    "Referer": "https://finance.sina.com.cn",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
})


class WatchlistQuoteService:
    """
    Service to fetch real-time quotes for watchlist stocks.
    Uses Sina Finance API which is fast and reliable.
    
    Sina API returns: name, open, prev_close, price, high, low, bid, ask,
                      volume, amount, ... and more fields.
    """

    @staticmethod
    def _code_to_sina(code: str) -> str:
        """Convert stock code to Sina format (sz/sh prefix)."""
        if code.startswith(("60", "68", "11")):
            return f"sh{code}"
        else:
            return f"sz{code}"

    @staticmethod
    @retry(stop=stop_after_attempt(2), wait=wait_fixed(1))
    def _fetch_batch_quotes(codes: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Fetch real-time quotes from Sina Finance for multiple stocks at once.
        This is very fast — single HTTP request for all codes.
        """
        sina_codes = [WatchlistQuoteService._code_to_sina(c) for c in codes]
        url = f"https://hq.sinajs.cn/list={','.join(sina_codes)}"

        r = _session.get(url, timeout=10)
        r.encoding = "gbk"

        results = {}
        for line in r.text.strip().split("\n"):
            if not line.strip():
                continue
            m = re.match(r'var hq_str_(\w+)="(.*)";', line)
            if not m:
                continue

            sina_code = m.group(1)
            raw_code = sina_code[2:]  # Remove sh/sz prefix
            fields = m.group(2).split(",")

            if len(fields) < 32:
                continue

            # Sina fields:
            # 0:名称, 1:今开, 2:昨收, 3:当前价, 4:最高, 5:最低
            # 6:竞买价, 7:竞卖价, 8:成交量(股), 9:成交额(元)
            # 10-19: 买1-5 量 价
            # 20-29: 卖1-5 量 价
            # 30:日期, 31:时间

            try:
                name = fields[0]
                price = float(fields[3])
                prev_close = float(fields[2])
                open_price = float(fields[1])
                high = float(fields[4])
                low = float(fields[5])
                volume = int(float(fields[8]))
                amount = float(fields[9])

                change_amt = round(price - prev_close, 3)
                change_pct = round((change_amt / prev_close) * 100, 2) if prev_close > 0 else 0
                amplitude = round(((high - low) / prev_close) * 100, 2) if prev_close > 0 else 0
                turnover = 0  # Not available from Sina directly

                results[raw_code] = {
                    "code": raw_code,
                    "name": name,
                    "price": price,
                    "open": open_price,
                    "prev_close": prev_close,
                    "high": high,
                    "low": low,
                    "change_pct": change_pct,
                    "change_amt": change_amt,
                    "volume": volume,
                    "amount": amount,
                    "turnover": turnover,
                    "amplitude": amplitude,
                    "date": fields[30] if len(fields) > 30 else "",
                    "time": fields[31] if len(fields) > 31 else "",
                }
            except (ValueError, IndexError):
                continue

        return results

    @staticmethod
    def get_quotes(watchlist: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Get quotes for all watchlist stocks in a single batch request.
        """
        if not watchlist:
            return []

        codes = [s["code"] for s in watchlist]
        code_to_stock = {s["code"]: s for s in watchlist}

        # Check cache first
        all_cached = True
        cached_quotes = []
        for code in codes:
            cached = Cache.get(f"quote_{code}")
            if cached:
                # Update name/tags from watchlist (may have changed)
                stock = code_to_stock[code]
                cached["name"] = stock.get("name", cached.get("name", ""))
                cached["tags"] = stock.get("tags", [])
                cached_quotes.append(cached)
            else:
                all_cached = False

        if all_cached:
            return cached_quotes

        # Fetch fresh data
        try:
            quote_map = WatchlistQuoteService._fetch_batch_quotes(codes)
        except Exception as e:
            print(f"Error fetching batch quotes: {e}")
            # Return fallback entries and cache them briefly
            fallback = []
            for s in watchlist:
                fallback_item = {
                    "code": s["code"],
                    "name": s.get("name", ""),
                    "tags": s.get("tags", []),
                    "price": 0,
                    "change_pct": 0,
                    "sparkline": [],
                    "error": str(e),
                }
                fallback.append(fallback_item)
                # Cache error state for 10s to prevent rapid retries
                Cache.set(f"quote_{s['code']}", fallback_item, ttl=10)
            return fallback

        quotes = []
        for stock in watchlist:
            code = stock["code"]
            name = stock.get("name", "")
            tags = stock.get("tags", [])

            quote = quote_map.get(code)
            if quote:
                quote["tags"] = tags
                if name:
                    quote["name"] = name  # Use saved name if available
                quote["sparkline"] = []  # Sparkline will be added later if needed
                Cache.set(f"quote_{code}", quote, ttl=15)  # Cache 15s for real-time feel
                quotes.append(quote)
            else:
                quotes.append({
                    "code": code,
                    "name": name,
                    "tags": tags,
                    "price": 0,
                    "change_pct": 0,
                    "sparkline": [],
                    "error": "No data",
                })

        return quotes

    @staticmethod
    def get_portfolio_summary(quotes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate portfolio-level summary stats from quotes."""
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
