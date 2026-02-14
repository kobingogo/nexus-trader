import asyncio
import logging
from sqlmodel import Session, select
from app.db.database import engine, create_db_and_tables
from app.models.signal import SignalRecord
from app.services.agent_llm import AgentLLM
from app.services.market_sentiment import MarketSentimentService
from datetime import datetime
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def trigger_real_analysis():
    print("🚀 Triggering Real Market Analysis...")
    create_db_and_tables()

    # 1. Fetch REAL Market Sentiment
    # This will fetch from Akshare/Sina and calculate metrics
    print("📊 Fetching current market sentiment...")
    try:
        # We use the service directly, which should fetch fresh data
        # Note: get_market_sentiment returns a DICT
        result = MarketSentimentService.get_market_sentiment()
        metrics = result.get("metrics", {})
        mood = metrics.get("mood_index", 50)
        up = metrics.get("limit_up_count", 0) # Using limit up as proxy for up count in summary for now
        down = metrics.get("fried_board_count", 0)
        
        print(f"   Current Mood: {mood}")
    except Exception as e:
        print(f"❌ Failed to fetch market sentiment: {e}")
        return

    # 2. Force an Analysis Signal
    # Even if mood is not > 80, we want to see what LLM thinks of CURRENT market
    print("🧠 Requesting LLM Analysis on current data...")
    
    # Create a temporary signal object just for analysis (not saved yet)
    # We pretend it's a "Market Summary" signal
    temp_signal = SignalRecord(
        type="market_summary",
        level="info", 
        message=f"Market Status: Mood {mood}, LimitUp {up}, Fried {down}",
        metadata_json=json.dumps(result, default=str)
    )

    try:
        analysis = AgentLLM.analyze_signal(temp_signal)
        print("✅ LLM Analysis Generated!")
        # print(analysis[:100] + "...")
    except Exception as e:
        print(f"❌ LLM Analysis failed: {e}")
        return

    # 3. Save to DB
    with Session(engine) as session:
        # Check if we already have a summary for today/recent to avoid spam? 
        # User wants "Real Analysis NOW", so let's just insert.
        
        real_signal = SignalRecord(
            type="market_summary",
            level="info",
            message=temp_signal.message,
            analysis_content=analysis,
            metadata_json=temp_signal.metadata_json,
            timestamp=datetime.now()
        )
        session.add(real_signal)
        session.commit()
        print(f"💾 Signal saved with ID: {real_signal.id}")

if __name__ == "__main__":
    asyncio.run(trigger_real_analysis())
