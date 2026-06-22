from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.briefing import Briefing
from app.models.email import Email
from app.models.calendar_event import CalendarEvent
from app.models.business_context import BusinessContext
from app.services.ai.ai_service import AIService

router = APIRouter(prefix="/briefing", tags=["briefing"])

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
    print("-----------------------------------------------------------------", flush=True)

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
    briefing = Briefing(
        user_id=current_user.id,
        focus=briefing_data.get("focus"),
        headline=briefing_data.get("headline"),
        ignored_count=briefing_data.get("ignored_count", 0),
        about_to_break=briefing_data.get("red", []),
        needs_decision=briefing_data.get("amber", []),
        wins=briefing_data.get("green", [])
    )
    db.add(briefing)
    db.commit()
    db.refresh(briefing)
    print("BRIEFING SAVED", flush=True)
    print("BRIEFING ID:", briefing.id, flush=True)

    return {
        "status": "success",
        "message": "Briefing generated successfully",
        "briefing": briefing
    }
