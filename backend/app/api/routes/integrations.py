from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.integration import Integration
from app.models.email import Email
from app.models.calendar_event import CalendarEvent
from app.services.google.gmail_service import GmailService
from app.services.google.calendar_service import CalendarService
from app.schemas.integration import SyncRequest

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.get("")
def get_integrations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get all integrations and their connection status for the current user from the database.
    """
    db_integrations = db.query(Integration).filter(Integration.user_id == current_user.id).all()
    int_map = {integration.provider: integration for integration in db_integrations}
    
    gmail_connected = "gmail" in int_map and int_map["gmail"].connected
    calendar_connected = "calendar" in int_map and int_map["calendar"].connected
    
    gmail_last_sync = int_map["gmail"].last_sync.isoformat() if "gmail" in int_map and int_map["gmail"].last_sync else None
    calendar_last_sync = int_map["calendar"].last_sync.isoformat() if "calendar" in int_map and int_map["calendar"].last_sync else None
    
    email_count = db.query(Email).filter(Email.user_id == current_user.id).count() if gmail_connected else 0
    unread_count = db.query(Email).filter(Email.user_id == current_user.id, Email.is_unread == True).count() if gmail_connected else 0
    
    now = datetime.now(timezone.utc)
    upcoming_events_count = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time > now
    ).count() if calendar_connected else 0
    
    return [
        {
            "id": 1,
            "provider": "gmail",
            "connected": gmail_connected,
            "last_sync": gmail_last_sync,
            "email_count": email_count,
            "unread_count": unread_count
        },
        {
            "id": 2,
            "provider": "calendar",
            "connected": calendar_connected,
            "last_sync": calendar_last_sync,
            "upcoming_events_count": upcoming_events_count
        },
        {
            "id": 3,
            "provider": "github",
            "connected": "github" in int_map and int_map["github"].connected,
            "last_sync": int_map["github"].last_sync.isoformat() if "github" in int_map and int_map["github"].last_sync else None
        },
        {
            "id": 4,
            "provider": "notion",
            "connected": "notion" in int_map and int_map["notion"].connected,
            "last_sync": int_map["notion"].last_sync.isoformat() if "notion" in int_map and int_map["notion"].last_sync else None
        }
    ]

@router.post("/{provider}/connect")
def connect_integration(provider: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Connect or toggle connection state for an integration provider.
    """
    if provider not in ["gmail", "calendar", "github", "notion"]:
        raise HTTPException(status_code=400, detail="Unknown integration provider")
        
    integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.provider == provider
    ).first()
    
    if not integration:
        # Try to locate generic google login credentials to copy
        google_int = db.query(Integration).filter(
            Integration.user_id == current_user.id,
            Integration.provider == "google"
        ).first()
        
        access_token = google_int.access_token if google_int else None
        refresh_token = google_int.refresh_token if google_int else None
        
        integration = Integration(
            user_id=current_user.id,
            provider=provider,
            access_token=access_token,
            refresh_token=refresh_token,
            connected=True
        )
        db.add(integration)
        message = f"{provider.capitalize()} connected successfully"
    else:
        # Toggle connected status
        integration.connected = not integration.connected
        message = f"{provider.capitalize()} {'connected' if integration.connected else 'disconnected'} successfully"
        
    db.commit()
    return {"status": "success", "message": message}

@router.post("/sync")
async def sync_integrations(request: SyncRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Trigger a sync of data from connected integrations.
    """
    sync_time = datetime.now(timezone.utc).isoformat()
    synced = []
    
    providers_to_sync = request.providers if request.providers else ["gmail", "calendar", "github", "notion"]
    
    # Sync Gmail
    if "gmail" in providers_to_sync:
        gmail_int = db.query(Integration).filter(
            Integration.user_id == current_user.id,
            Integration.provider == "gmail",
            Integration.connected == True
        ).first()
        if gmail_int:
            try:
                service = GmailService(db)
                await service.sync_user_emails(current_user)
                synced.append("gmail")
            except Exception as e:
                print(f"Error syncing gmail: {str(e)}")
                
    # Sync Calendar
    if "calendar" in providers_to_sync:
        cal_int = db.query(Integration).filter(
            Integration.user_id == current_user.id,
            Integration.provider == "calendar",
            Integration.connected == True
        ).first()
        if cal_int:
            try:
                service = CalendarService(db)
                await service.sync_user_calendar(current_user)
                synced.append("calendar")
            except Exception as e:
                print(f"Error syncing calendar: {str(e)}")
                
    return {
        "status": "success",
        "synced_providers": synced,
        "sync_time": sync_time
    }

# --- GMAIL ENDPOINTS ---

@router.post("/gmail/sync")
async def sync_gmail(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Force synchronization of user's Gmail.
    """
    try:
        service = GmailService(db)
        res = await service.sync_user_emails(current_user)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/gmail/messages")
def get_gmail_messages(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get synced email list.
    """
    messages = db.query(Email).filter(Email.user_id == current_user.id).order_by(Email.received_at.desc()).all()
    return messages

@router.get("/gmail/stats")
def get_gmail_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get Gmail statistics.
    """
    total_emails = db.query(Email).filter(Email.user_id == current_user.id).count()
    unread_emails = db.query(Email).filter(Email.user_id == current_user.id, Email.is_unread == True).count()
    integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.provider == "gmail"
    ).first()
    last_sync = integration.last_sync.isoformat() if integration and integration.last_sync else None
    
    latest_email = db.query(Email).filter(Email.user_id == current_user.id).order_by(Email.received_at.desc()).first()
    latest_email_data = None
    if latest_email:
        latest_email_data = {
            "id": latest_email.id,
            "sender": latest_email.sender,
            "subject": latest_email.subject,
            "snippet": latest_email.snippet,
            "received_at": latest_email.received_at.isoformat()
        }
        
    return {
        "total_emails": total_emails,
        "unread_emails": unread_emails,
        "last_sync": last_sync,
        "latest_email": latest_email_data
    }

# --- CALENDAR ENDPOINTS ---

@router.post("/calendar/sync")
async def sync_calendar(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Force synchronization of user's Calendar.
    """
    try:
        service = CalendarService(db)
        res = await service.sync_user_calendar(current_user)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/events")
def get_calendar_events(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get synced events list.
    """
    events = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id).order_by(CalendarEvent.start_time.asc()).all()
    return events

@router.get("/calendar/stats")
def get_calendar_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get Google Calendar statistics.
    """
    now = datetime.now(timezone.utc)
    start_of_week = now - timedelta(days=now.weekday())
    start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_week = start_of_week + timedelta(days=7)

    total_events = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id).count()
    upcoming_events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time > now
    ).count()
    
    events_this_week = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time >= start_of_week,
        CalendarEvent.start_time < end_of_week
    ).count()
    
    integration = db.query(Integration).filter(
        Integration.user_id == current_user.id,
        Integration.provider == "calendar"
    ).first()
    last_sync = integration.last_sync.isoformat() if integration and integration.last_sync else None
    
    next_event = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == current_user.id,
        CalendarEvent.start_time > now
    ).order_by(CalendarEvent.start_time.asc()).first()
    
    next_event_data = None
    if next_event:
        next_event_data = {
            "id": next_event.id,
            "title": next_event.title,
            "start_time": next_event.start_time.isoformat(),
            "end_time": next_event.end_time.isoformat(),
            "location": next_event.location
        }
        
    return {
        "total_events": total_events,
        "upcoming_events": upcoming_events,
        "events_this_week": events_this_week,
        "last_sync": last_sync,
        "next_event": next_event_data
    }

@router.get("/status")
def get_integrations_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get connection status of all integration providers for the current user.
    """
    db_integrations = db.query(Integration).filter(Integration.user_id == current_user.id).all()
    int_map = {integration.provider: integration for integration in db_integrations}
    
    return {
        "gmail": {
            "connected": "gmail" in int_map and int_map["gmail"].connected,
            "last_sync": int_map["gmail"].last_sync.isoformat() if "gmail" in int_map and int_map["gmail"].last_sync else None
        },
        "calendar": {
            "connected": "calendar" in int_map and int_map["calendar"].connected,
            "last_sync": int_map["calendar"].last_sync.isoformat() if "calendar" in int_map and int_map["calendar"].last_sync else None
        },
        "github": {
            "connected": "github" in int_map and int_map["github"].connected,
            "last_sync": int_map["github"].last_sync.isoformat() if "github" in int_map and int_map["github"].last_sync else None
        },
        "notion": {
            "connected": "notion" in int_map and int_map["notion"].connected,
            "last_sync": int_map["notion"].last_sync.isoformat() if "notion" in int_map and int_map["notion"].last_sync else None
        }
    }

