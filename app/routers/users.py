from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth import verify_clerk_token, get_current_user
from app.models.user import UserCreate, UserUpdate, UserResponse, User
from app.services import user_service

router = APIRouter(prefix="/users", tags=["users"])


# ── Public routes (no auth needed) ─────────────────────────────

@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return user_service.create_user(db, user)


@router.post("/register", response_model=UserResponse, status_code=201)
def register_user(
    user: UserCreate,
    clerk_user_id: str = Depends(verify_clerk_token),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.clerk_id == clerk_user_id).first()
    if existing:
        return existing
    new_user = User(
        clerk_id=clerk_user_id,
        email=user.email,
        name=user.name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ── My account routes (requires auth, operates on own account) ──

@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return user_service.update_user(db, current_user.id, user_data)


@router.delete("/me")
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return user_service.delete_user(db, current_user.id)


# ── General routes ──────────────────────────────────────────────

@router.get("/", response_model=list[UserResponse])
def list_users(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    return user_service.get_all_users(db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.get_user_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user: UserUpdate,
    db: Session = Depends(get_db)
):
    return user_service.update_user(db, user_id, user)


@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    return user_service.delete_user(db, user_id)