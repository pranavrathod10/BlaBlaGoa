from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("connection_requests.id"), nullable=False)
    user_one_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_two_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # active / ended / abandoned
    status = Column(String, default="active", nullable=False)

    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    user_one = relationship("User", foreign_keys=[user_one_id])
    user_two = relationship("User", foreign_keys=[user_two_id])


# ── Pydantic schemas ────────────────────────────────────────────

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: int
    user_one_id: int
    user_two_id: int
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    expires_at: datetime
    other_user_name: Optional[str] = None