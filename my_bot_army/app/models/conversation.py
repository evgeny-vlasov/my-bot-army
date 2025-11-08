from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


class MessageBase(BaseModel):
    role: str  # user, assistant, system
    content: str


class MessageCreate(MessageBase):
    conversation_id: int


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ConversationBase(BaseModel):
    bot_id: int
    user_identifier: Optional[str] = None
    source: Optional[str] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationResponse(ConversationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = []

    model_config = ConfigDict(from_attributes=True)
