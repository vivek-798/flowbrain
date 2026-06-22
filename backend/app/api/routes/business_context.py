from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.business_context import BusinessContext
from app.models.user import User
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/business-context", tags=["business-context"])

# Pydantic validation schemas
class ClientSchema(BaseModel):
    name: str
    value_inr: float
    status: str  # active/at-risk/lost
    notes: Optional[str] = None

class ProjectSchema(BaseModel):
    name: str
    client_name: str
    value_inr: float
    deadline: Optional[str] = None
    completion_percent: float
    status: str

class TeamMemberSchema(BaseModel):
    name: str
    role: str
    email: Optional[str] = None

class BusinessContextUpdate(BaseModel):
    business_type: str
    clients: List[ClientSchema]
    projects: List[ProjectSchema]
    team_members: List[TeamMemberSchema]

@router.get("/{user_id}")
def get_business_context(user_id: int, db: Session = Depends(get_db)):
    """
    Fetch the current business context for the user.
    """
    context = db.query(BusinessContext).filter(BusinessContext.user_id == user_id).first()
    if not context:
        return {
            "user_id": user_id,
            "business_type": "",
            "clients": [],
            "projects": [],
            "team_members": []
        }
    return {
        "user_id": context.user_id,
        "business_type": context.business_type,
        "clients": context.clients or [],
        "projects": context.projects or [],
        "team_members": context.team_members or []
    }

@router.put("/{user_id}")
def update_business_context(user_id: int, payload: BusinessContextUpdate, db: Session = Depends(get_db)):
    """
    Update/Save the business context for the user (full replace).
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    context = db.query(BusinessContext).filter(BusinessContext.user_id == user_id).first()
    if not context:
        context = BusinessContext(
            user_id=user_id,
            business_type=payload.business_type,
            clients=[c.model_dump() for c in payload.clients],
            projects=[p.model_dump() for p in payload.projects],
            team_members=[t.model_dump() for t in payload.team_members]
        )
        db.add(context)
    else:
        context.business_type = payload.business_type
        context.clients = [c.model_dump() for c in payload.clients]
        context.projects = [p.model_dump() for p in payload.projects]
        context.team_members = [t.model_dump() for t in payload.team_members]
        context.updated_at = datetime.now(timezone.utc)
        
    print("--- [DIAGNOSTIC] Saving Business Context to DB ---", flush=True)
    print(f"User ID: {user_id}", flush=True)
    print(f"Payload business_type: {payload.business_type}", flush=True)
    print(f"Payload clients: {[c.model_dump() for c in payload.clients]}", flush=True)
    print(f"Payload projects: {[p.model_dump() for p in payload.projects]}", flush=True)
    print(f"Payload team_members: {[t.model_dump() for t in payload.team_members]}", flush=True)
    print(f"Model BusinessContext - business_type: {context.business_type}", flush=True)
    print(f"Model BusinessContext - clients: {context.clients}", flush=True)
    print(f"Model BusinessContext - projects: {context.projects}", flush=True)
    print(f"Model BusinessContext - team_members: {context.team_members}", flush=True)
    print("--------------------------------------------------", flush=True)

    db.commit()
    db.refresh(context)
    return {
        "status": "success",
        "message": "Business context updated successfully",
        "business_context": {
            "user_id": context.user_id,
            "business_type": context.business_type,
            "clients": context.clients,
            "projects": context.projects,
            "team_members": context.team_members
        }
    }
