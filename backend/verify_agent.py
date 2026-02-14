import asyncio
from sqlmodel import Session, select, delete
from app.db.database import engine, create_db_and_tables
from app.models.sentiment import SentimentRecord
from app.models.signal import SignalRecord
from app.services.agent_service import AgentService
from datetime import datetime

async def main():
    print("Verifying Agent Logic...")
    create_db_and_tables()
    
    with Session(engine) as session:
        # 1. Clean up old test data
        session.exec(delete(SignalRecord))
        session.commit()

        # 2. Insert High Mood Record
        print("Inserting high sentiment record (Mood=90)...")
        record = SentimentRecord(
            mood_index=90.0,
            up_count=4000,
            down_count=1000,
            limit_up_count=100,
            limit_down_count=5,
            fried_rate=10.0,
            temperature=35.0,
            trend="up",
            timestamp=datetime.now()
        )
        session.add(record)
        session.commit()
    
    # 3. Trigger Analysis
    print("Triggering Agent Analysis...")
    await AgentService.analyze()

    # 4. Check for Signal
    # Wait a bit longer for LLM analysis
    print("Waiting for Agent analysis (including LLM)...")
    await asyncio.sleep(5) 

    with Session(engine) as session:
        signals = session.exec(select(SignalRecord)).all()
        if signals:
            print(f"SUCCESS! Found {len(signals)} signals:")
            for s in signals:
                print(f" - [{s.level.upper()}] {s.type}: {s.message}")
                if s.analysis_content:
                    print(f"   [LLM Analysis]: {s.analysis_content[:100]}...")
                else:
                    print("   [LLM Analysis]: None (Might be slow or not triggered)")
        else:
            print("FAILURE! No signals generated.")

if __name__ == "__main__":
    asyncio.run(main())
