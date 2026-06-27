from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.briefing import Briefing
from app.models.email import Email
from app.models.calendar_event import CalendarEvent
from app.models.business_context import BusinessContext
from app.models.action_item import ActionItem
from app.schemas.action_item import ActionItemUpdate
from app.services.ai.ai_service import AIService
from datetime import datetime, timezone
import json

router = APIRouter(prefix="/briefing", tags=["briefing"])

actions_router = APIRouter(prefix="/actions", tags=["actions"])

def save_briefing_with_actions(db: Session, user_id: int, result: dict):
    try:
        # 1. Save briefing first
        briefing = Briefing(
            user_id=user_id,
            focus=result.get("focus"),
            headline=result.get("headline"),
            ignored_count=result.get("ignored_count", 0),
            about_to_break=result.get("red", []),
            needs_decision=result.get("amber", []),
            wins=result.get("green", [])
        )
        db.add(briefing)
        db.flush()  # get briefing.id without committing
        
        # 2. Parse and save actions
        actions = result.get("actions", [])
        for action_data in actions:
            # Convert due_date string to date object
            due_date = None
            if action_data.get("due_date"):
                try:
                    due_date = datetime.strptime(
                        action_data["due_date"], "%Y-%m-%d"
                    ).date()
                except ValueError:
                    due_date = None
            
            # financial_impact must be integer or None
            financial_impact = action_data.get("financial_impact")
            if isinstance(financial_impact, str):
                financial_impact = None  # reject strings
            
            action = ActionItem(
                user_id=user_id,
                briefing_id=briefing.id,
                title=action_data.get("title", ""),
                description=action_data.get("description"),
                priority=action_data.get("priority", 99),
                due_date=due_date,
                financial_impact=financial_impact,
                source_type=action_data.get("source_type"),
                source_signal=action_data.get("source_signal"),
                status="pending"
            )
            db.add(action)
        
        # 3. Commit both together
        db.commit()
        db.refresh(briefing)
        
        print(f"SAVED: briefing_id={briefing.id}, actions_saved={len(actions)}", flush=True)
        return briefing
        
    except Exception as e:
        db.rollback()
        print(f"SAVE FAILED, rolled back: {e}", flush=True)
        raise

@router.get("/latest")
def get_latest_briefing(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get the most recent briefing for the founder from the database.
    """
    briefing = db.query(Briefing).filter(Briefing.user_id == current_user.id).order_by(Briefing.generated_at.desc()).first()
    print("LATEST BRIEFING REQUESTED", flush=True)
    print("FOUND:", briefing is not None, flush=True)
    return briefing

@router.post("/generate")
def generate_briefing(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Triggers briefing generation by fetching context data from the database
    and invoking the LiteLLM/Gemini model abstraction. Saves result to DB.
    """
    user = current_user
    print("BRIEFING GENERATION STARTED", flush=True)
    print("Current User:", user.id, flush=True)

    # 1. Fetch latest 100 emails metadata
    emails = db.query(Email).filter(
        Email.user_id == current_user.id,
        Email.is_excluded == False
    ).order_by(Email.received_at.desc()).limit(100).all()
    
    # 2. Fetch upcoming calendar events
    events = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id).order_by(CalendarEvent.start_time.asc()).all()

    # 2.5 Fetch business context
    business_context = db.query(BusinessContext).filter(BusinessContext.user_id == current_user.id).first()

    print("--- [DIAGNOSTIC] Briefing Generation - Fetched Business Context ---", flush=True)
    if business_context:
        print(f"BusinessContext ID: {business_context.id}", flush=True)
        print(f"User ID: {business_context.user_id}", flush=True)
        print(f"business_type: {business_context.business_type}", flush=True)
        print(f"clients: {business_context.clients}", flush=True)
        print(f"projects: {business_context.projects}", flush=True)
        print(f"team_members: {business_context.team_members}", flush=True)
    else:
        print("No BusinessContext found in the DB for user", flush=True)
    print("---------------------------------------------------------", flush=True)

    # 3. Format user data context
    user_data = {
        "emails": [
            {
                "subject": e.subject,
                "sender": e.sender,
                "received_at": e.received_at.isoformat() if e.received_at else "",
                "is_unread": e.is_unread,
                "labels": e.labels,
                "snippet": e.snippet,
                "body_full": e.body_full
            } for e in emails
        ],
        "calendar_events": [
            {
                "title": evt.title,
                "description": evt.description,
                "start_time": evt.start_time.isoformat() if evt.start_time else "",
                "end_time": evt.end_time.isoformat() if evt.end_time else "",
                "attendees": evt.attendees
            } for evt in events
        ],
        "business_context": {
            "business_type": business_context.business_type if business_context else "",
            "clients": business_context.clients if business_context else [],
            "projects": business_context.projects if business_context else [],
            "team_members": business_context.team_members if business_context else []
        } if business_context else None
    }

    # 4. Invoke the AI Context Builder Service
    briefing_data = AIService.generate_briefing_summary(user_data)

    # 5. Persist the generated briefing in the database
    print("SAVING BRIEFING TO DATABASE", flush=True)
    briefing = save_briefing_with_actions(db, current_user.id, briefing_data)

    return {
        "status": "success",
        "message": "Briefing generated successfully",
        "briefing": briefing
    }

@actions_router.get("")
def get_actions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get all pending actions for the current user, sorted by priority ASC.
    """
    actions = db.query(ActionItem).filter(
        ActionItem.user_id == current_user.id,
        ActionItem.status == "pending"
    ).order_by(ActionItem.priority.asc()).all()
    return actions

@actions_router.patch("/{action_id}")
def update_action_status(
    action_id: int,
    payload: ActionItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the status of an action item. Validate status done/dismissed, record completion time.
    """
    action = db.query(ActionItem).filter(
        ActionItem.id == action_id,
        ActionItem.user_id == current_user.id
    ).first()
    
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found or unauthorized access"
        )
        
    action.status = payload.status
    if payload.status == "done":
        action.completed_at = datetime.now(timezone.utc)
    else:
        action.completed_at = None
        
    db.commit()
    db.refresh(action)
    return action

@actions_router.get("/summary")
def get_actions_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get action items summary metrics.
    """
    total_pending = db.query(ActionItem).filter(
        ActionItem.user_id == current_user.id,
        ActionItem.status == "pending"
    ).count()
    
    total_done = db.query(ActionItem).filter(
        ActionItem.user_id == current_user.id,
        ActionItem.status == "done"
    ).count()
    
    total_dismissed = db.query(ActionItem).filter(
        ActionItem.user_id == current_user.id,
        ActionItem.status == "dismissed"
    ).count()
    
    from sqlalchemy import func
    total_financial = db.query(func.sum(ActionItem.financial_impact)).filter(
        ActionItem.user_id == current_user.id,
        ActionItem.status == "pending"
    ).scalar() or 0
    
    earliest_due_date = db.query(func.min(ActionItem.due_date)).filter(
        ActionItem.user_id == current_user.id,
        ActionItem.status == "pending",
        ActionItem.due_date.isnot(None)
    ).scalar()
    
    return {
        "total_pending": total_pending,
        "total_done": total_done,
        "total_dismissed": total_dismissed,
        "total_financial_at_stake": total_financial,
        "next_due_date": earliest_due_date.isoformat() if earliest_due_date else None
    }


