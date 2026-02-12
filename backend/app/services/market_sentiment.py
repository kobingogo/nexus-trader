
import pandas as pd
import akshare as ak
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class MarketSentimentService:
    @staticmethod
    def get_market_sentiment() -> Dict[str, Any]:
        """
        Fetch and calculate market sentiment metrics:
        1. Limit Up Count & Fried Board Count -> Fried Board Rate
        2. Yesterday Limit Up Performance -> Premium Rate
        """
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            
            # Fetch Limit Up Pool
            try:
                df_zt = ak.stock_zt_pool_em(date=date_str)
                zt_count = len(df_zt) if not df_zt.empty else 0
            except Exception:
                zt_count = 0
                df_zt = pd.DataFrame()

            # Fetch Fried Board Pool
            try:
                df_zb = ak.stock_zt_pool_zbgc_em(date=date_str)
                zb_count = len(df_zb) if not df_zb.empty else 0
            except Exception:
                zb_count = 0

            # Calculate Fried Board Rate
            total_attempt = zt_count + zb_count
            fried_rate = (zb_count / total_attempt * 100) if total_attempt > 0 else 0

            # Fetch Yesterday Limit Up Pool Performance
            try:
                df_prev_zt = ak.stock_zt_pool_previous_em(date=date_str)
                if not df_prev_zt.empty and '涨跌幅' in df_prev_zt.columns:
                    premium_rate = df_prev_zt['涨跌幅'].mean()
                    # Success rate: ratio of stocks that are limit up (approx > 9.5%) today
                    # Note: exact limit up varies (10% or 20%), simplified to >9.5%
                    success_count = len(df_prev_zt[df_prev_zt['涨跌幅'] > 9.5])
                    promotion_rate = (success_count / len(df_prev_zt) * 100)
                else:
                    premium_rate = 0
                    promotion_rate = 0
            except Exception:
                premium_rate = 0
                promotion_rate = 0

            # Calculate Mood Index (Simple Algorithm)
            # Base: 50
            # + Limit Up Count / 10 (max 30)
            # - Fried Rate * 0.5 (max 20)
            # + Premium Rate * 2 (max 20)
            mood = 50 + (zt_count / 5) - (fried_rate * 0.5) + (premium_rate * 2)
            mood = max(0, min(100, mood))

            return {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "limit_up_count": int(zt_count),
                    "fried_board_count": int(zb_count),
                    "fried_rate": float(round(fried_rate, 2)),
                    "premium_rate": float(round(premium_rate, 2)),
                    "promotion_rate": float(round(promotion_rate, 2)),
                    "mood_index": float(round(mood, 1))
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "metrics": {
                    "limit_up_count": 0, "fried_board_count": 0, "fried_rate": 0,
                    "premium_rate": 0, "promotion_rate": 0, "mood_index": 50
                }
            }
