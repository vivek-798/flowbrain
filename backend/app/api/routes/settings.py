from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.settings import SettingsUpdate, SettingsResponse

settings_router = APIRouter(prefix="/settings", tags=["settings"])
insights_router = APIRouter(prefix="/insights", tags=["insights"])

# In-memory mock configuration state
mock_settings = {
    "name": "Alex Founder",
    "email": "founder@flowbrain.ai",
    "email_notifications": True,
    "share_analytics": False,
    "ai_provider": "Claude Haiku"
}

@settings_router.get("", response_model=SettingsResponse)
def get_settings():
    """
    Get application settings for the founder.
    """
    return mock_settings

@settings_router.put("", response_model=SettingsResponse)
def update_settings(payload: SettingsUpdate):
    """
    Update settings.
    """
    if payload.name is not None:
        mock_settings["name"] = payload.name
    if payload.email_notifications is not None:
        mock_settings["email_notifications"] = payload.email_notifications
    if payload.share_analytics is not None:
        mock_settings["share_analytics"] = payload.share_analytics
    if payload.ai_provider is not None:
        mock_settings["ai_provider"] = payload.ai_provider
    return mock_settings

@insights_router.get("")
def get_insights(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get dynamic database-backed operational metrics for the insights dashboard.
    """
    from app.models.integration import Integration
    from app.models.email import Email
    from app.models.calendar_event import CalendarEvent

    db_integrations = db.query(Integration).filter(Integration.user_id == current_user.id).all()
    int_map = {integration.provider: integration for integration in db_integrations}

    gmail_connected = "gmail" in int_map and int_map["gmail"].connected
    calendar_connected = "calendar" in int_map and int_map["calendar"].connected

    email_count = db.query(Email).filter(Email.user_id == current_user.id).count() if gmail_connected else 0
    calendar_count = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id).count() if calendar_connected else 0

    gmail_summary = f"{email_count} emails scanned" if gmail_connected else "Connect Gmail to begin analysis"
    calendar_summary = f"{calendar_count} calendar events synced" if calendar_connected else "Connect Google Calendar to track events"
    github_summary = "GitHub connected" if ("github" in int_map and int_map["github"].connected) else "No GitHub repositories connected"
    notion_summary = "Notion connected" if ("notion" in int_map and int_map["notion"].connected) else "No Notion workspace connected"

    return {
        "business_risk_score": 0,
        "open_risks": 0,
        "upcoming_deadlines": [],
        "activity_summary": {
            "gmail": gmail_summary,
            "calendar": calendar_summary,
            "github": github_summary,
            "notion": notion_summary
        }
    }
