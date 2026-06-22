from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    gmail_message_id = Column(String, unique=True, index=True, nullable=False)
    thread_id = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    sender = Column(String, nullable=False)
    recipients = Column(String, nullable=True)
    snippet = Column(String, nullable=True)
    body_preview = Column(String, nullable=True)
    body_full = Column(Text, nullable=True)
    labels = Column(JSON, nullable=True)
    is_unread = Column(Boolean, default=True, nullable=False)
    is_excluded = Column(Boolean, default=False, nullable=False)
    relevance_checked = Column(Boolean, default=False, nullable=False)
    is_relevant = Column(Boolean, nullable=True)
    relevance_category = Column(String, nullable=True)
    relevance_reason = Column(String, nullable=True)
    received_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", backref="emails")
