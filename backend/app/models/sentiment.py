from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class SentimentRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    mood_index: float
    up_count: int
    down_count: int
    limit_up_count: int
    limit_down_count: int
    fried_rate: float
    temperature: float
    # Trend can be calculated on read, or stored. Storing is easier for simple reads.
    trend: str = "flat" # up, down, flat
