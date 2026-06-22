from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.email import Email

router = APIRouter(prefix="/emails", tags=["emails"])

@router.post("/{gmail_message_id}/exclude")
def exclude_email(
    gmail_message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Excludes a specific email by its gmail_message_id from future briefings and syncs.
    """
    email_record = db.query(Email).filter(
        Email.gmail_message_id == gmail_message_id,
        Email.user_id == current_user.id
    ).first()
    
    if not email_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found"
        )
        
    email_record.is_excluded = True
    db.commit()
    db.refresh(email_record)
    
    return {
        "status": "success",
        "message": f"Email {gmail_message_id} has been permanently excluded",
        "email": {
            "gmail_message_id": email_record.gmail_message_id,
            "subject": email_record.subject,
            "is_excluded": email_record.is_excluded
        }
    }
