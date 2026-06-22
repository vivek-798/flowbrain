from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class IntegrationBase(BaseModel):
    provider: str
    connected: bool

class IntegrationCreate(IntegrationBase):
    user_id: int
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class IntegrationResponse(IntegrationBase):
    id: int
    user_id: int
    last_sync: Optional[datetime] = None

    class Config:
        from_attributes = True

class SyncRequest(BaseModel):
    providers: Optional[List[str]] = None
