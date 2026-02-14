
import logging
import pandas as pd
import akshare as ak
from datetime import datetime
from typing import Dict, Any, List
from sqlmodel import Session, select, desc

from app.utils.cache import ttl_cache
from app.db.database import engine
from app.models.sentiment import SentimentRecord

logger = logging.getLogger(__name__)

from app.providers.akshare_provider import AkShareProvider

class MarketSentimentService:
    @staticmethod
    @ttl_cache(ttl=60) # Cache for 1 minute
    def get_market_sentiment() -> Dict[str, Any]:
        """
        Fetch and calculate market sentiment metrics:
        1. Limit Up Count & Fried Board Count (EastMoney) -> Fried Board Rate
        2. Broad Market Up/Down Counts (Legu)
        3. Yesterday Limit Up Performance (EastMoney) -> Premium Rate
        4. Calculate Mood Index
        """
        try:
            date_str = datetime.now().strftime("%Y%m%d")
            
            # --- 1. Broad Market Counts (Legu) ---
            # We use this for Up/Down/Flat counts as it's a good summary
            provider = AkShareProvider()
            legu_data = provider.get_market_activity_data()
            up_count = legu_data.get("up_count", 0)
            down_count = legu_data.get("down_count", 0)
            flat_count = legu_data.get("flat_count", 0)

            # --- 2. Specialized Pools (EastMoney) ---
            # We prefer EastMoney for Limit Up/Fried stats as they are more accurate for "Mood"
            
            # Fetch Limit Up Pool
            try:
                df_zt = ak.stock_zt_pool_em(date=date_str)
                zt_count = len(df_zt) if not df_zt.empty else 0
            except Exception:
                zt_count = legu_data.get("limit_up_count", 0) # Fallback to Legu
                df_zt = pd.DataFrame()

            # Fetch Fried Board Pool
            try:
                df_zb = ak.stock_zt_pool_zbgc_em(date=date_str)
                zb_count = len(df_zb) if not df_zb.empty else 0
            except Exception:
                zb_count = 0 # Legu doesn't have fried board count easily

            # Fetch Limit Down Pool (EastMoney) - More accurate for traders
            try:
                df_dt = ak.stock_zt_pool_dtgc_em(date=date_str)
                dt_count = len(df_dt) if not df_dt.empty else 0
            except Exception:
                dt_count = legu_data.get("limit_down_count", 0) # Fallback to Legu
                df_dt = pd.DataFrame()

            # Calculate Fried Board Rate
            total_attempt = zt_count + zb_count
            fried_rate = (zb_count / total_attempt * 100) if total_attempt > 0 else 0

            # Fetch Yesterday Limit Up Pool Performance
            try:
                df_prev_zt = ak.stock_zt_pool_previous_em(date=date_str)
                if not df_prev_zt.empty and '涨跌幅' in df_prev_zt.columns:
                    premium_rate = df_prev_zt['涨跌幅'].mean()
                    success_count = len(df_prev_zt[df_prev_zt['涨跌幅'] > 9.5])
                    promotion_rate = (success_count / len(df_prev_zt) * 100)
                else:
                    premium_rate = 0
                    promotion_rate = 0
            except Exception:
                premium_rate = 0
                promotion_rate = 0

            # Calculate Mood Index
            mood = 50 + (zt_count / 5) - (fried_rate * 0.5) + (premium_rate * 2)
            mood = max(0, min(100, mood))
            mood = float(round(mood, 1))

            # --- Persistence & Trend Analysis ---
            trend = "flat"
            try:
                with Session(engine) as session:
                    # 1. Get previous record
                    prev_record = session.exec(
                        select(SentimentRecord).order_by(desc(SentimentRecord.timestamp)).limit(1)
                    ).first()
                    
                    if prev_record:
                        if mood > prev_record.mood_index + 0.5:
                            trend = "up"
                        elif mood < prev_record.mood_index - 0.5:
                            trend = "down"
                    
                    # 2. Save current record
                    # Only save if changed significantly? 
                    # For MVP, let's save every time called (but capped by cache 60s)
                    # To avoid spamming DB, we could check if last record was very recent.
                    
                    should_save = True
                    if prev_record:
                        # If less than 60s since last save, skip saving to DB but use calculated trend
                        time_diff = (datetime.utcnow() - prev_record.timestamp).total_seconds()
                        if time_diff < 50: 
                            should_save = False
                    
                    if should_save:
                        record = SentimentRecord(
                            mood_index=mood,
                            up_count=up_count, 
                            down_count=down_count,
                            limit_up_count=zt_count,
                            limit_down_count=dt_count, # Use EastMoney data
                            fried_rate=fried_rate,
                            temperature=mood, # Mood as temp
                            trend=trend
                        )
                        session.add(record)
                        session.commit()
                        
            except Exception as e:
                logger.error(f"DB Error in market sentiment: {e}")

            return {
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "limit_up_count": int(zt_count),
                    "limit_down_count": int(dt_count),
                    "fried_board_count": int(zb_count),
                    "up_count": int(up_count),
                    "down_count": int(down_count),
                    "flat_count": int(flat_count),
                    "fried_rate": float(round(fried_rate, 2)),
                    "premium_rate": float(round(premium_rate, 2)),
                    "promotion_rate": float(round(promotion_rate, 2)),
                    "mood_index": mood,
                    "trend": trend,
                    "temperature": mood, # For frontend compatibility
                    "activity": legu_data.get("activity", 0) # Raw activity from Legu
                },
                # Flattened structure for frontend compatibility
                "up_count": int(up_count),
                "down_count": int(down_count),
                "flat_count": int(flat_count),
                "limit_up_count": int(zt_count),
                "limit_down_count": int(dt_count),
                "activity": legu_data.get("activity", 0),
                "temperature": mood,
                "ts": datetime.now().strftime("%H:%M:%S")
            }
            
        except Exception as e:
            logger.error(f"Error getting market sentiment: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "up_count": 0, "down_count": 0, "flat_count": 0,
                "limit_up_count": 0, "limit_down_count": 0, 
                "activity": 0.0, "temperature": 0.0,
                "ts": ""
            }
