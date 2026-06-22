from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class BusinessContext(Base):
    __tablename__ = "business_contexts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    business_type = Column(String, nullable=True)
    clients = Column(JSON, nullable=True)          # List of clients: [{name, value_inr, status, notes}]
    projects = Column(JSON, nullable=True)         # List of projects: [{name, client_name, value_inr, deadline, completion_percent, status}]
    team_members = Column(JSON, nullable=True)     # List of team members: [{name, role, email}]
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationship
    user = relationship("User", backref="business_context_ref")
