import calendar
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.email import Email
from app.models.calendar_event import CalendarEvent
from app.models.integration import Integration

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/overview")
def get_dashboard_overview(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get dynamic founder dashboard overview metrics backed strictly by the database records.
    """
    now_dt = datetime.now(timezone.utc)

    # 1. Fetch integrations status
    gmail_int = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.provider == "gmail"
    ).first()

    calendar_int = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.provider == "calendar"
    ).first()

    gmail_connected = bool(gmail_int and gmail_int.connected)
    calendar_connected = bool(calendar_int and calendar_int.connected)

    # Calculate last sync time
    sync_times = [i.last_sync for i in [gmail_int, calendar_int] if i and i.last_sync]
    last_sync = max(sync_times).isoformat() if sync_times else ""

    # 2. Query Email stats
    emails_total = db.query(Email).filter(Email.user_id == current_user.id).count() if gmail_connected else 0
    emails_unread = db.query(Email).filter(Email.user_id == current_user.id, Email.is_unread == True).count() if gmail_connected else 0

    # 3. Query Calendar events for the current month
    start_of_month = datetime(now_dt.year, now_dt.month, 1, 0, 0, 0, tzinfo=timezone.utc)
    _, last_day = calendar.monthrange(now_dt.year, now_dt.month)
    end_of_month = datetime(now_dt.year, now_dt.month, last_day, 23, 59, 59, tzinfo=timezone.utc)

    calendar_events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time >= start_of_month,
        CalendarEvent.start_time <= end_of_month
    ).count() if calendar_connected else 0

    # 4. Fetch the next upcoming meeting
    upcoming_events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time > now_dt
    ).order_by(CalendarEvent.start_time.asc()).all()

    personal_keywords = ["birthday", "anniversary", "aniversary", "reminder", "holiday", "vacation", "personal"]
    next_event = None
    for event in upcoming_events:
        title = (event.title or "").lower()
        desc = (event.description or "").lower()
        text = f"{title} {desc}"
        if any(pk in text for pk in personal_keywords):
            continue
        next_event = event
        break

    next_meeting = {}
    if next_event and calendar_connected:
        next_meeting = {
            "id": next_event.id,
            "title": next_event.title,
            "description": next_event.description,
            "start_time": next_event.start_time.isoformat(),
            "end_time": next_event.end_time.isoformat(),
            "location": next_event.location,
            "meeting_link": next_event.meeting_link,
            "organizer": next_event.organizer
        }

    return {
        "emails_total": emails_total,
        "emails_unread": emails_unread,
        "calendar_events": calendar_events,
        "next_meeting": next_meeting,
        "gmail_connected": gmail_connected,
        "calendar_connected": calendar_connected,
        "last_sync": last_sync
    }
