
import pandas as pd
import numpy as np
import requests
import asyncio
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class StockAnalysisService:
    @staticmethod
    def calculate_technicals(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators: MA, MACD, KDJ, RSI.
        Input df must have columns: 'close', 'high', 'low'
        """
        if df.empty:
            return df
        
        # Ensure numeric types
        for col in ['close', 'high', 'low', 'open', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])

        # 1. Moving Averages
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()

        # 2. MACD (12, 26, 9)
        exp12 = df['close'].ewm(span=12, adjust=False).mean()
        exp26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = exp12 - exp26
        df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['hist'] = df['macd'] - df['signal']

        # 3. RSI (6, 12, 24)
        def calc_rsi(series, period):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        df['rsi_6'] = calc_rsi(df['close'], 6)
        df['rsi_12'] = calc_rsi(df['close'], 12)
        df['rsi_24'] = calc_rsi(df['close'], 24)

        # 4. KDJ (9, 3, 3)
        low_min = df['low'].rolling(window=9).min()
        high_max = df['high'].rolling(window=9).max()
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        
        # Pandas ewm is close to SMA for KDJ but not exact matching standard formula. 
        # Using recursive calculation for KDJ is better but for MVP ewm is okay-ish or loop.
        # Standard KDJ uses SMA(1/3).
        
        k_values = []
        d_values = []
        k = 50
        d = 50
        
        for i in range(len(df)):
            if np.isnan(rsv.iloc[i]):
                k_values.append(np.nan)
                d_values.append(np.nan)
            else:
                k = 2/3 * k + 1/3 * rsv.iloc[i]
                d = 2/3 * d + 1/3 * k
                k_values.append(k)
                d_values.append(d)
                
        df['k'] = k_values
        df['d'] = d_values
        df['j'] = 3 * df['k'] - 2 * df['d']

        return df

    @staticmethod
    def get_fundamentals(code: str) -> Dict[str, Any]:
        """
        Fetch fundamental data (PE, PB, MarketCap) from EastMoney.
        """
        try:
            secid = f"1.{code}" if code.startswith("6") else f"0.{code}"
            url = f"http://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f57,f162,f167,f116"
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, timeout=5)
            data = r.json()
            
            if data and 'data' in data and data['data']:
                d = data['data']
                pe = d['f162'] / 100 if d['f162'] != '-' else None
                pb = d['f167'] / 100 if d['f167'] != '-' else None
                mkt_cap = d['f116'] # Raw value
                
                return {
                    "pe_ttm": pe,
                    "pb": pb,
                    "market_cap": mkt_cap
                }
        except Exception as e:
            logger.error(f"Error fetching fundamentals for {code}: {e}")
        
        return {}

    @staticmethod
    def get_stock_news(code: str) -> List[Dict[str, str]]:
        """
        Fetch recent news from EastMoney (unofficial API or similar).
        """
        try:
            # Using EastMoney News Search API which is relatively stable
            url = "https://search-api-web.eastmoney.com/search/jsonp/news_list"
            params = {
                "cb": "jQuery123",
                "param": f"code={code}",
                "pageSize": 5,
                "pageIndex": 1,
                "q": code
            }
            headers = {
                "Referer": "https://so.eastmoney.com/",
                "User-Agent": "Mozilla/5.0"
            }
            r = requests.get(url, params=params, headers=headers, timeout=5)
            content = r.text
            start = content.find('(') + 1
            end = content.rfind(')')
            import json
            data = json.loads(content[start:end])
            
            news_items = []
            if 'result' in data and 'items' in data['result']:
                items = data['result']['items']
                for item in items:
                    news_items.append({
                        "title": item.get('title', '').replace('<em>', '').replace('</em>', ''),
                        "date": item.get('date', ''),
                        "url": item.get('url', ''),
                        "source": item.get('mediaName', '')
                    })
            return news_items
        except Exception as e:
            logger.error(f"Error fetching news for {code}: {e}")
            return []
