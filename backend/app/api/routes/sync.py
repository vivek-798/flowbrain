from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.google.gmail_service import GmailService
from app.services.google.calendar_service import CalendarService

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/gmail")
async def sync_gmail(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Force synchronization of user's Gmail emails from the last 30 days.
    """
    try:
        service = GmailService(db)
        res = await service.sync_user_emails(current_user)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/calendar")
async def sync_calendar(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Force synchronization of user's Google Calendar events for the current month.
    """
    try:
        service = CalendarService(db)
        res = await service.sync_user_calendar(current_user)
        return {"events_synced": res.get("synced", 0)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
