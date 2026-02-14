import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import List, Optional
from sqlmodel import Session, select, desc

from app.db.database import engine
from app.models.sentiment import SentimentRecord
from app.models.anomaly import AnomalyRecord
from app.models.signal import SignalRecord
from app.services.market_data import MarketDataService
from app.services.notification_service import NotificationService
from app.services.agent_llm import AgentLLM
import asyncio

logger = logging.getLogger(__name__)

class AgentService:
    """
    The Brain of NEXUS Trader.
    Runs in the background, monitors data, and generates signals.
    """
    _running = False
    _task = None

    @classmethod
    def start(cls):
        if cls._running:
            return
        cls._running = True
        cls._task = asyncio.create_task(cls._loop())
        logger.info("Agent Brain started 🧠")

    @classmethod
    def stop(cls):
        cls._running = False
        if cls._task:
            cls._task.cancel()
        logger.info("Agent Brain stopped 💤")

    @classmethod
    async def _loop(cls):
        """Main monitoring loop."""
        while cls._running:
            try:
                await cls.analyze()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Agent analysis error: {e}")
            
            # Sleep for 60 seconds (MVP)
            await asyncio.sleep(60)

    @classmethod
    async def analyze(cls):
        """Analyze current market state and generate signals."""
        logger.info("Agent analyzing market state...")
        
        with Session(engine) as session:
            # 1. Fetch latest Context
            sentiment = session.exec(
                select(SentimentRecord).order_by(desc(SentimentRecord.timestamp)).limit(1)
            ).first()

            if not sentiment:
                logger.warning("Agent: No sentiment data available yet.")
                return

            # 2. Rule Engine
            # Rule A: Overheating
            if sentiment.mood_index > 80:
                await cls._create_signal(session, "sentiment_spike", "warning", 
                                   f"Market is Overheating! Mood Index: {sentiment.mood_index:.1f}")
            
            # Rule B: High Risk (Fried Board)
            if sentiment.fried_rate > 30:
                await cls._create_signal(session, "risk_alert", "critical", 
                                   f"High Risk Alert! Fried Board Rate: {sentiment.fried_rate:.1f}%")

            # Rule C: Recovery (Trend reversal)
            # Need previous record? For now simple check
            if sentiment.trend == "up" and sentiment.mood_index < 50:
                 await cls._create_signal(session, "recovery_sign", "info", 
                                   f"Market is recovering. Trend is Up.")

            # Rule D: Anomaly Burst
            # Count anomalies in last 5 mins
            five_mins_ago = datetime.now() - timedelta(minutes=5)
            recent_anomalies = session.exec(
                select(AnomalyRecord).where(AnomalyRecord.timestamp >= five_mins_ago)
            ).all()

            rockets = [a for a in recent_anomalies if a.type == "rocket"]
            dives = [a for a in recent_anomalies if a.type == "dive"]

            if len(rockets) > 5:
                 await cls._create_signal(session, "anomaly_burst", "info", 
                                   f"Rocket Burst! {len(rockets)} stocks skyrocketing in last 5 mins.")
            
            if len(dives) > 5:
                 await cls._create_signal(session, "anomaly_burst", "warning", 
                                   f"Dive Burst! {len(dives)} stocks diving in last 5 mins.")

    @classmethod
    async def _create_signal(cls, session: Session, type: str, level: str, message: str, meta: dict = {}):
        """Helper to create and deduplicate signals."""
        # Simple dedupe: Check if same signal type & message exists in last 10 mins
        ten_mins_ago = datetime.now() - timedelta(minutes=10)
        existing = session.exec(
            select(SignalRecord)
            .where(SignalRecord.type == type)
            .where(SignalRecord.message == message)
            .where(SignalRecord.timestamp >= ten_mins_ago)
        ).first()

        if existing:
            return # Skip duplicate

        signal = SignalRecord(
            type=type,
            level=level,
            message=message,
            metadata_json=json.dumps(meta)
        )
        session.add(signal)
        session.commit()
        session.refresh(signal)
        logger.info(f"Generated Signal: {signal.message}")
        
        # Broadcast via NotificationService (First Alert)
        await NotificationService.broadcast(signal.model_dump())

        # Trigger LLM Analysis for Critical/Warning signals
        if level in ["critical", "warning"]:
            try:
                # Run in thread to avoid blocking loop
                analysis = await asyncio.to_thread(AgentLLM.analyze_signal, signal)
                if analysis:
                    signal.analysis_content = analysis
                    session.add(signal)
                    session.commit()
                    logger.info(f"Signal analyzed by LLM: {signal.id}")
            except Exception as e:
                logger.error(f"Failed to analyze signal: {e}")

    @classmethod
    def get_latest_signals(cls, limit: int = 10) -> List[SignalRecord]:
        with Session(engine) as session:
            return session.exec(
                select(SignalRecord).order_by(desc(SignalRecord.timestamp)).limit(limit)
            ).all()
