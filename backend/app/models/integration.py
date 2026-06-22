from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String, nullable=False, index=True)  # e.g., 'gmail', 'calendar', 'github', 'notion'
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    connected = Column(Boolean, default=False)
    last_sync = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="integrations")
