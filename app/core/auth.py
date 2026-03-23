import httpx
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User


def get_clerk_public_keys():
    """
    Fetches Clerk's public keys (JWKS) used to verify JWT tokens.
    Clerk rotates these keys occasionally so we fetch fresh every time.
    In production you'd cache this — for now fetching is fine.
    """
    url = f"https://api.clerk.com/v1/jwks"
    headers = {"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
    response = httpx.get(url, headers=headers)
    return response.json()


def verify_clerk_token(authorization: str = Header(...)) -> str:
    """
    Extracts and verifies the JWT token from the Authorization header.
    Returns the clerk_user_id if valid.
    Raises 401 if anything is wrong.

    Every protected route calls this via Depends().
    """
    # Header format: "Bearer eyJhbGc..."
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format"
        )

    token = authorization.replace("Bearer ", "")

    try:
        # Fetch Clerk's public keys
        jwks = get_clerk_public_keys()

        # Decode and verify the token
        # Clerk uses RS256 algorithm
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            options={"verify_aud": False}  # Clerk tokens don't always have audience
        )

        # "sub" is the standard JWT field for user ID
        clerk_user_id: str = payload.get("sub")

        if not clerk_user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        return clerk_user_id

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


def get_current_user(
    clerk_user_id: str = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Takes the verified clerk_user_id and returns the actual User from your DB.
    Use this dependency when you need the full user object in a route.
    """
    user = db.query(User).filter(User.clerk_id == clerk_user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Please complete registration."
        )

    return user