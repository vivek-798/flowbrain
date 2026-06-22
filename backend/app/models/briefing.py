from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Briefing(Base):
    __tablename__ = "briefings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # JSON columns to store list of cards/items
    about_to_break = Column(JSON, nullable=True)   # List of issues, e.g. [{"id": 1, "text": "Production API down"}]
    needs_decision = Column(JSON, nullable=True)   # List of decisions, e.g. [{"id": 1, "text": "Approve budget"}]
    wins = Column(JSON, nullable=True)             # List of wins, e.g. [{"id": 1, "text": "Signed 3 new clients"}]
    focus = Column(String, nullable=True)          # Text representing focus
    headline = Column(String, nullable=True)
    ignored_count = Column(Integer, default=0, nullable=True)

    # Relationships
    user = relationship("User", back_populates="briefings")
