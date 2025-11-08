from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any


class BotBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str


class BotCreate(BotBase):
    client_id: int
    config: Optional[Dict[str, Any]] = {}


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    deployment_status: Optional[str] = None


class BotResponse(BotBase):
    id: int
    client_id: int
    config: Dict[str, Any]
    is_active: bool
    deployment_status: str
    created_at: datetime
    updated_at: datetime
    deployed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
