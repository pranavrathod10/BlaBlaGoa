from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import date, datetime


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    bio = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    is_profile_complete = Column(Boolean, default=False)

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Online presence
    last_seen = Column(DateTime(timezone=True), nullable=True)

    # Discovery settings
    discovery_radius_km = Column(Integer, default=5)
    is_discoverable = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# ── Pydantic schemas ────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    discovery_radius_km: Optional[int] = None
    is_discoverable: Optional[bool] = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None
    is_active: bool
    is_profile_complete: bool
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    discovery_radius_km: int
    is_discoverable: bool
    last_seen: Optional[datetime] = None
    created_at: datetime