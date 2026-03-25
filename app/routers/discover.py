from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user, verify_clerk_token
from app.models.user import User, UserResponse
from app.services import discovery_service
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/discover", tags=["discover"])


class LocationUpdate(BaseModel):
    latitude: float
    longitude: float


class PresenceUpdate(BaseModel):
    is_discoverable: Optional[bool] = None


class NearbyUserResponse(BaseModel):
    id: int
    name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    distance_km: float
    is_online: bool

    class Config:
        from_attributes = True


@router.patch("/me/location")
def update_location(
    location: LocationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Called when user sets their location on the Connect page.
    Saves their lat/long to the database.
    Also updates last_seen so they appear online.
    """
    current_user.latitude = location.latitude
    current_user.longitude = location.longitude
    current_user.location_updated_at = datetime.now(timezone.utc)
    current_user.last_seen = datetime.now(timezone.utc)
    db.commit()
    return {"status": "location updated"}


@router.patch("/me/presence")
def update_presence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Called every 30 seconds from the frontend as a heartbeat.
    Updates last_seen so other users see you as online.
    If last_seen is more than 1 minute old you appear offline.
    """
    current_user.last_seen = datetime.now(timezone.utc)
    db.commit()
    return {"status": "presence updated"}


@router.get("/nearby", response_model=list[NearbyUserResponse])
def get_nearby_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all online users within current_user's discovery radius.
    Uses the Haversine formula to calculate distances.
    """
    if current_user.latitude is None or current_user.longitude is None:
        return []

    return discovery_service.get_nearby_users(db, current_user)