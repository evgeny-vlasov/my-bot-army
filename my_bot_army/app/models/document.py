from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class DocumentBase(BaseModel):
    title: Optional[str] = None
    content: str
    source: Optional[str] = None


class DocumentCreate(DocumentBase):
    bot_id: int


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: int
    bot_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
