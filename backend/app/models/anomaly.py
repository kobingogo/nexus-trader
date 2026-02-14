from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class AnomalyRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    code: str = Field(index=True)
    name: str
    type: str # rocket, dive, big_order_buy, big_order_sell
    change_type: str # 原始类型: 快速反弹, 大笔买入
    price: float
    change_pct: float
    amount: float
    message: str
    severity: str # high, medium, low
