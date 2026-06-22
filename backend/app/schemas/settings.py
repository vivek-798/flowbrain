from pydantic import BaseModel
from typing import Optional

class SettingsUpdate(BaseModel):
    name: Optional[str] = None
    email_notifications: Optional[bool] = None
    share_analytics: Optional[bool] = None
    ai_provider: Optional[str] = None

class SettingsResponse(BaseModel):
    name: str
    email: str
    email_notifications: bool
    share_analytics: bool
    ai_provider: str
