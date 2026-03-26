from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services import connection_service
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/connections", tags=["connections"])


class SendRequestBody(BaseModel):
    receiver_id: int
    message: str


class RespondBody(BaseModel):
    action: str


class ConnectionRequestOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    message: str
    status: str
    created_at: datetime
    expires_at: datetime
    responded_at: Optional[datetime] = None
    sender_name: Optional[str] = None
    sender_bio: Optional[str] = None
    receiver_name: Optional[str] = None

    class Config:
        from_attributes = True


@router.post("/", response_model=ConnectionRequestOut, status_code=201)
@limiter.limit("10/minute")
def send_request(
    body: SendRequestBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return connection_service.send_request(
        db, current_user, body.receiver_id, body.message
    )


@router.get("/pending", response_model=list[ConnectionRequestOut])
def get_pending_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return connection_service.get_pending_requests(db, current_user.id)


@router.get("/sent", response_model=list[ConnectionRequestOut])
def get_sent_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return connection_service.get_sent_requests(db, current_user.id)


@router.patch("/{request_id}/respond")
def respond_to_request(
    request_id: int,
    body: RespondBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if body.action not in ["accept", "reject"]:
        raise HTTPException(
            status_code=400,
            detail="Action must be accept or reject"
        )
    return connection_service.respond_to_request(
        db, request_id, current_user, body.action
    )