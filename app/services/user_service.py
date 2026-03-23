from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.user import User, UserCreate, UserUpdate


def create_user(db: Session, user_data: UserCreate) -> User:
    # Check if email already exists before trying to insert
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user_data.email,
        name=user_data.name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)   # reload from DB so created_at is populated
    return new_user


def get_user_by_id(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_user_by_email(db: Session, email: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 20) -> list[User]:
    return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
    user = get_user_by_id(db, user_id)

    # Only update fields that were actually sent
    # exclude_unset=True means "ignore fields the client didn't include"
    update_data = user_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> dict:
    user = get_user_by_id(db, user_id)

    # Soft delete — mark inactive, don't actually remove the row
    # Their data is preserved, they just can't log in
    user.is_active = False
    db.commit()
    return {"message": "User deleted successfully"}