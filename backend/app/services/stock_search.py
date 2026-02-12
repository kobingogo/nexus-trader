"""
Stock search service: fuzzy search A-share stocks by code or name.
Uses akshare stock_info_a_code_name() to get the full list, cached for 24h.
"""
import re
import time
import requests
from typing import List, Dict, Any, Optional
from app.services.market_data import Cache

# Direct session (bypass macOS system proxy)
_session = requests.Session()
_session.trust_env = False
_session.headers.update({
    "Referer": "https://finance.sina.com.cn",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
})

# In-memory stock list cache
_stock_list: List[Dict[str, str]] = []
_stock_list_ts: float = 0
_CACHE_TTL = 86400  # 24 hours


def _load_stock_list() -> List[Dict[str, str]]:
    """Load all A-share stock codes and names. Cached for 24h."""
    global _stock_list, _stock_list_ts

    if _stock_list and (time.time() - _stock_list_ts) < _CACHE_TTL:
        return _stock_list

    try:
        import akshare as ak
        df = ak.stock_info_a_code_name()
        _stock_list = [
            {"code": str(row["code"]).zfill(6), "name": str(row["name"]).strip()}
            for _, row in df.iterrows()
        ]
        _stock_list_ts = time.time()
        print(f"[StockSearch] Loaded {len(_stock_list)} stocks")
    except Exception as e:
        print(f"[StockSearch] Failed to load stock list: {e}")
        if not _stock_list:
            _stock_list = []

    return _stock_list


def search_stocks(query: str, limit: int = 10) -> List[Dict[str, str]]:
    """
    Fuzzy search stocks by code or name.
    - If query is all digits: match code prefix
    - If query contains Chinese: match name substring
    - Mixed: try both
    Returns list of {code, name} dicts.
    """
    if not query or not query.strip():
        return []

    query = query.strip()
    stocks = _load_stock_list()

    if not stocks:
        return []

    results = []
    query_lower = query.lower()
    is_digit = query.isdigit()

    # Scoring: exact match > prefix match > substring match
    scored: List[tuple] = []

    for s in stocks:
        code = s["code"]
        name = s["name"]
        score = 0

        if is_digit:
            # Digit query: match code
            if code == query:
                score = 100  # exact
            elif code.startswith(query):
                score = 80  # prefix
            elif query in code:
                score = 50  # substring
        else:
            # Text query: match name or code
            if name == query:
                score = 100
            elif name.startswith(query):
                score = 80
            elif query in name:
                score = 60
            # Also try code match for mixed input
            if query_lower in code:
                score = max(score, 50)

        if score > 0:
            scored.append((score, s))

    # Sort by score desc, then by code
    scored.sort(key=lambda x: (-x[0], x[1]["code"]))

    return [item[1] for item in scored[:limit]]


def get_stock_name(code: str) -> Optional[str]:
    """Look up stock name by exact code."""
    code = code.strip().zfill(6)
    stocks = _load_stock_list()
    for s in stocks:
        if s["code"] == code:
            return s["name"]
    return None


def get_stock_history_sina(code: str, days: int = 30) -> str:
    """
    Get recent stock history from Sina Finance in text format.
    Uses Sina's daily K-line API, no proxy issues.
    Returns markdown table string.
    """
    # Determine market prefix
    if code.startswith(("60", "68", "11")):
        sina_code = f"sh{code}"
    else:
        sina_code = f"sz{code}"

    try:
        # Sina historical daily K-line (80-day)
        url = f"https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        params = {
            "symbol": sina_code,
            "scale": "240",  # daily
            "ma": "no",
            "datalen": str(min(days, 60)),
        }
        r = _session.get(url, params=params, timeout=10)

        if r.status_code != 200 or not r.text.strip():
            return f"无法获取 {code} 的历史数据"

        # Parse Sina's JSON-like response
        import json
        data = json.loads(r.text)

        if not data:
            return f"无法获取 {code} 的历史数据"

        # Format as markdown table
        lines = ["| 日期 | 开盘 | 收盘 | 最高 | 最低 | 成交量 |",
                 "|------|------|------|------|------|--------|"]

        for item in data:  # Return all fetched data
            lines.append(
                f"| {item.get('day','')} | {item.get('open','')} | {item.get('close','')} | "
                f"{item.get('high','')} | {item.get('low','')} | {item.get('volume','')} |"
            )

        return "\n".join(lines)

    except Exception as e:
        return f"获取历史数据失败: {str(e)}"
