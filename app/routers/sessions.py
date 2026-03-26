from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.models.session import Session as ChatSession
from app.models.message import Message
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/sessions", tags=["sessions"])


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    request_id: int
    user_one_id: int
    user_two_id: int
    status: str
    started_at: datetime
    expires_at: datetime
    ended_at: Optional[datetime] = None
    other_user_name: Optional[str] = None


@router.get("/active", response_model=list[SessionOut])
def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all active sessions for the current user.
    Checks expiry and auto-ends any that have passed expires_at.
    """
    now = datetime.now(timezone.utc)

    # Auto-end expired sessions and flush messages
    expired = db.query(ChatSession).filter(
        ChatSession.status == "active",
        ChatSession.expires_at < now,
        (ChatSession.user_one_id == current_user.id) |
        (ChatSession.user_two_id == current_user.id)
    ).all()

    for session in expired:
        session.status = "ended"
        session.ended_at = now
        # Flush messages
        db.query(Message).filter(
            Message.session_id == session.id
        ).update({"is_deleted": True})

    if expired:
        db.commit()

    # Get active sessions
    sessions = db.query(ChatSession).filter(
        ChatSession.status == "active",
        (ChatSession.user_one_id == current_user.id) |
        (ChatSession.user_two_id == current_user.id)
    ).all()

    # Attach other user's name
    for session in sessions:
        other_id = (
            session.user_two_id
            if session.user_one_id == current_user.id
            else session.user_one_id
        )
        other_user = db.query(User).filter(User.id == other_id).first()
        if other_user:
            session.other_user_name = other_user.name

    return sessions


@router.get("/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        (ChatSession.user_one_id == current_user.id) |
        (ChatSession.user_two_id == current_user.id)
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    other_id = (
        session.user_two_id
        if session.user_one_id == current_user.id
        else session.user_one_id
    )
    other_user = db.query(User).filter(User.id == other_id).first()
    if other_user:
        session.other_user_name = other_user.name

    return session