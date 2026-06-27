from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date, BigInteger
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    briefing_id = Column(Integer, ForeignKey("briefings.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=False)
    priority = Column(Integer, nullable=False, default=1)
    due_date = Column(Date, nullable=True)
    financial_impact = Column(BigInteger, nullable=True)
    source_type = Column(String(50), nullable=False)  # "red" or "amber" only
    source_signal = Column(String(500), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # "pending", "done", "dismissed"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="action_items")
    briefing = relationship("Briefing", back_populates="action_items")
