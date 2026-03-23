from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import verify_clerk_token, get_current_user
from app.models.user import UserCreate, UserUpdate, UserResponse, User
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


# ── Public routes (no auth needed) ─────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(
    user: UserCreate,
    clerk_user_id: str = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    """
    Called by frontend right after Clerk signup.
    Creates the user in YOUR database linked to their Clerk ID.
    """
    # Check if already registered
    existing = db.query(User).filter(User.clerk_id == clerk_user_id).first()
    if existing:
        return existing  # already registered, just return them

    new_user = User(
        clerk_id=clerk_user_id,
        email=user.email,
        name=user.name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ── Protected routes (auth required) ───────────────────────────

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Returns the currently logged in user's profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates the currently logged in user's own profile."""
    return user_service.update_user(db, current_user.id, user_data)


@router.delete("/me")
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Soft deletes the currently logged in user's account."""
    return user_service.delete_user(db, current_user.id)


# ── Admin style routes (can see other users) ───────────────────

@router.get("/", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: str = Depends(verify_clerk_token)  # must be logged in, but any user
):
    return user_service.get_all_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(verify_clerk_token)
):
    return user_service.get_user_by_id(db, user_id)