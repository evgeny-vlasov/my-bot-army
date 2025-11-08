from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional


class ClientBase(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    is_active: Optional[bool] = None
    subscription_tier: Optional[str] = None


class ClientResponse(ClientBase):
    id: int
    is_active: bool
    subscription_tier: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
