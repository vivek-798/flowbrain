from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any

class BriefingBase(BaseModel):
    about_to_break: Optional[List[Any]] = None
    needs_decision: Optional[List[Any]] = None
    wins: Optional[List[Any]] = None
    focus: Optional[str] = None

class BriefingCreate(BriefingBase):
    user_id: int

class BriefingResponse(BriefingBase):
    id: int
    user_id: int
    generated_at: datetime

    class Config:
        from_attributes = True
