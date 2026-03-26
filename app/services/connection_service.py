from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.connection import ConnectionRequest
from app.models.session import Session as ChatSession
from app.models.user import User
from datetime import datetime, timedelta, timezone


def send_request(
    db: Session,
    sender: User,
    receiver_id: int,
    message: str
) -> ConnectionRequest:

    if sender.id == receiver_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot send a request to yourself"
        )

    receiver = db.query(User).filter(User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(ConnectionRequest).filter(
        ConnectionRequest.sender_id == sender.id,
        ConnectionRequest.receiver_id == receiver_id,
        ConnectionRequest.status == "pending"
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="You already have a pending request to this user"
        )

    message = message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(message) > 200:
        raise HTTPException(status_code=400, detail="Message too long")

    now = datetime.now(timezone.utc)
    request = ConnectionRequest(
        sender_id=sender.id,
        receiver_id=receiver_id,
        message=message,
        status="pending",
        expires_at=now + timedelta(hours=1)
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    request.sender_name = sender.name
    request.sender_bio = sender.bio

    return request


def get_pending_requests(db: Session, user_id: int) -> list:
    now = datetime.now(timezone.utc)

    # Auto-expire old requests
    db.query(ConnectionRequest).filter(
        ConnectionRequest.receiver_id == user_id,
        ConnectionRequest.status == "pending",
        ConnectionRequest.expires_at < now
    ).update({"status": "expired"})
    db.commit()

    requests = db.query(ConnectionRequest).filter(
        ConnectionRequest.receiver_id == user_id,
        ConnectionRequest.status == "pending"
    ).order_by(ConnectionRequest.created_at.desc()).all()

    for req in requests:
        sender = db.query(User).filter(User.id == req.sender_id).first()
        if sender:
            req.sender_name = sender.name
            req.sender_bio = sender.bio

    return requests


def get_sent_requests(db: Session, user_id: int) -> list:
    requests = db.query(ConnectionRequest).filter(
        ConnectionRequest.sender_id == user_id,
    ).order_by(ConnectionRequest.created_at.desc()).all()

    for req in requests:
        receiver = db.query(User).filter(User.id == req.receiver_id).first()
        if receiver:
            req.receiver_name = receiver.name

    return requests


def respond_to_request(
    db: Session,
    request_id: int,
    current_user: User,
    action: str
) -> dict:
    request = db.query(ConnectionRequest).filter(
        ConnectionRequest.id == request_id,
        ConnectionRequest.receiver_id == current_user.id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Request is already {request.status}"
        )

    now = datetime.now(timezone.utc)

    if now > request.expires_at:
        request.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Request has expired")

    request.responded_at = now

    if action == "reject":
        request.status = "rejected"
        db.commit()
        return {"status": "rejected"}

    # Accept — create session
    request.status = "accepted"

    session = ChatSession(
        request_id=request.id,
        user_one_id=request.sender_id,
        user_two_id=current_user.id,
        status="active",
        started_at=now,
        expires_at=now + timedelta(minutes=5)
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "status": "accepted",
        "session_id": session.id,
        "expires_at": session.expires_at.isoformat()
    }