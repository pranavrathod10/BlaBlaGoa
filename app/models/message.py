from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, ConfigDict
from datetime import datetime


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(String, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())

    # True = flushed after session ends
    # We mark as deleted rather than actually removing rows
    # A background cleanup can permanently delete after 24 hours
    is_deleted = Column(Boolean, default=False, nullable=False)

    session = relationship("Session")
    sender = relationship("User")


# ── Pydantic schemas ────────────────────────────────────────────

class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    sender_id: int
    content: str
    sent_at: datetime