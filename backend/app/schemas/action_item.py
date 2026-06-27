from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import Optional

class ActionItemUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["done", "dismissed"]:
            raise ValueError("Status must be either 'done' or 'dismissed'")
        return v

class ActionItemResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    priority: int
    due_date: Optional[date] = None
    financial_impact: Optional[int] = None
    source_type: Optional[str] = None
    source_signal: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
