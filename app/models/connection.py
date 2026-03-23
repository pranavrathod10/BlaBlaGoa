from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ConnectionRequest(Base):
    __tablename__ = "connection_requests"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # pending / accepted / rejected / expired
    status = Column(String, default="pending", nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Set when receiver responds
    responded_at = Column(DateTime(timezone=True), nullable=True)

    # Expires 1 hour after creation if no response
    expires_at = Column(DateTime(timezone=True), nullable=False)

    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])


# ── Pydantic schemas ────────────────────────────────────────────

class ConnectionRequestCreate(BaseModel):
    receiver_id: int

class ConnectionRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    receiver_id: int
    status: str
    created_at: datetime
    responded_at: Optional[datetime] = None
    expires_at: datetime