from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.briefing import Briefing

router = APIRouter(prefix="/briefing", tags=["briefing"])

@router.get("/history")
def get_briefing_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Retrieve past briefings generated for the founder from the database.
    """
    briefings = db.query(Briefing).filter(Briefing.user_id == current_user.id).order_by(Briefing.generated_at.desc()).all()
    
    result = []
    for b in briefings:
        result.append({
            "id": b.id,
            "user_id": b.user_id,
            "generated_at": b.generated_at.isoformat(),
            "focus": b.focus,
            "wins_count": len(b.wins) if b.wins else 0,
            "breaks_count": len(b.about_to_break) if b.about_to_break else 0,
            "decisions_count": len(b.needs_decision) if b.needs_decision else 0
        })
    return result
