from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class UsageBase(BaseModel):
    event_type: str  # message, embedding, etc.
    tokens_used: int = 0
    cost: float = 0.0


class UsageCreate(UsageBase):
    client_id: int
    bot_id: Optional[int] = None
    conversation_id: Optional[int] = None


class UsageResponse(UsageBase):
    id: int
    client_id: int
    bot_id: Optional[int] = None
    conversation_id: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
