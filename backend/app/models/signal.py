from sqlmodel import Field, SQLModel
from datetime import datetime
from typing import Optional, Dict, Any
import json

class SignalRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now, index=True)
    type: str = Field(index=True)  # sentiment_spike, anomaly_burst, leader_breakout
    level: str = Field(default="info")  # info, warning, critical
    message: str
    analysis_content: Optional[str] = Field(default=None)  # LLM deep analysis
    metadata_json: str = Field(default="{}")  # Stored as JSON string

    @property
    def meta(self) -> Dict[str, Any]:
        return json.loads(self.metadata_json)

    @meta.setter
    def meta(self, value: Dict[str, Any]):
        self.metadata_json = json.dumps(value)
