from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.session import Session as ChatSession
from app.models.message import Message
from app.models.user import User
from jose import jwt, JWTError
from app.core.config import settings
import httpx
import json
from datetime import datetime, timezone

router = APIRouter()


class ConnectionManager:
    """
    Tracks all active WebSocket connections.
    Key: session_id
    Value: list of (user_id, websocket) tuples

    Lives in memory — resets if server restarts.
    Fine for our use case since sessions are only 5 minutes.
    """
    def __init__(self):
        # session_id → list of (user_id, WebSocket)
        self.active: dict[int, list[tuple[int, WebSocket]]] = {}

    async def connect(self, session_id: int, user_id: int, ws: WebSocket):
        await ws.accept()
        if session_id not in self.active:
            self.active[session_id] = []
        self.active[session_id].append((user_id, ws))

    def disconnect(self, session_id: int, user_id: int):
        if session_id in self.active:
            self.active[session_id] = [
                (uid, ws) for uid, ws in self.active[session_id]
                if uid != user_id
            ]
            if not self.active[session_id]:
                del self.active[session_id]

    async def broadcast(self, session_id: int, message: dict, exclude_user_id: int = None):
        """Send message to all connections in a session."""
        if session_id not in self.active:
            return
        for user_id, ws in self.active[session_id]:
            if exclude_user_id and user_id == exclude_user_id:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def send_to_session(self, session_id: int, message: dict):
        """Send message to ALL users in a session including sender."""
        await self.broadcast(session_id, message)


# Single instance — shared across all requests
manager = ConnectionManager()


def get_clerk_public_keys():
    url = "https://api.clerk.com/v1/jwks"
    headers = {"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
    response = httpx.get(url, headers=headers)
    return response.json()


def verify_token(token: str) -> int | None:
    """Verify Clerk JWT and return user_id from DB."""
    try:
        jwks = get_clerk_public_keys()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        return payload.get("sub")  # clerk_id
    except JWTError:
        return None


@router.websocket("/ws/session/{session_id}")
async def websocket_session(
    session_id: int,
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for a chat session.

    Token is passed as a query parameter because WebSocket
    connections cannot have custom headers in most browsers.
    So we use: ws://api/ws/session/1?token=eyJ...
    """

    # Step 1 — Verify the token
    clerk_id = verify_token(token)
    if not clerk_id:
        await websocket.close(code=4001)
        return

    # Step 2 — Find the user in our DB
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    if not user:
        await websocket.close(code=4001)
        return

    # Step 3 — Verify this user belongs to this session
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.status == "active",
        (ChatSession.user_one_id == user.id) |
        (ChatSession.user_two_id == user.id)
    ).first()

    if not session:
        await websocket.close(code=4003)
        return

    # Step 4 — Check session hasn't expired
    now = datetime.now(timezone.utc)
    if now > session.expires_at:
        await websocket.close(code=4004)
        return

    # Step 5 — Connect
    await manager.connect(session_id, user.id, websocket)

    # Step 6 — Send session info to this user
    await websocket.send_json({
        "type": "session_info",
        "session_id": session_id,
        "expires_at": session.expires_at.isoformat(),
        "your_user_id": user.id
    })

    # Step 7 — Load and send message history
    history = db.query(Message).filter(
        Message.session_id == session_id,
        Message.is_deleted == False
    ).order_by(Message.sent_at.asc()).all()

    for msg in history:
        await websocket.send_json({
            "type": "message",
            "id": msg.id,
            "sender_id": msg.sender_id,
            "content": msg.content,
            "sent_at": msg.sent_at.isoformat()
        })

    # Step 8 — Notify other user that this user joined
    await manager.broadcast(session_id, {
        "type": "user_joined",
        "user_id": user.id,
        "user_name": user.name
    }, exclude_user_id=user.id)

    try:
        # Step 9 — Listen for messages
        while True:
            # Check if session expired every loop
            now = datetime.now(timezone.utc)
            if now > session.expires_at:
                # Flush messages
                db.query(Message).filter(
                    Message.session_id == session_id
                ).update({"is_deleted": True})

                session.status = "ended"
                session.ended_at = now
                db.commit()

                # Notify both users
                await manager.send_to_session(session_id, {
                    "type": "session_ended",
                    "message": "Your 5 minutes are up. This chat has ended."
                })
                break

            # Receive message from this user
            data = await websocket.receive_text()

            try:
                parsed = json.loads(data)
                content = parsed.get("content", "").strip()
            except json.JSONDecodeError:
                content = data.strip()

            if not content:
                continue

            if len(content) > 500:
                await websocket.send_json({
                    "type": "error",
                    "message": "Message too long"
                })
                continue

            # Save to database
            message = Message(
                session_id=session_id,
                sender_id=user.id,
                content=content
            )
            db.add(message)
            db.commit()
            db.refresh(message)

            # Broadcast to everyone in session including sender
            await manager.send_to_session(session_id, {
                "type": "message",
                "id": message.id,
                "sender_id": user.id,
                "sender_name": user.name,
                "content": content,
                "sent_at": message.sent_at.isoformat()
            })

    except WebSocketDisconnect:
        # User closed their browser or navigated away
        manager.disconnect(session_id, user.id)
        await manager.broadcast(session_id, {
            "type": "user_left",
            "user_id": user.id,
            "user_name": user.name
        })
