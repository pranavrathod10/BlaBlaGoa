from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    # --- Core identity (set at registration, required) ---
    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)

    # --- Extended profile (filled in later, all optional) ---

    # Stored as a URL pointing to S3/Cloudflare R2
    # The actual image file lives in cloud storage, not the DB
    avatar_url = Column(String, nullable=True)

    # Store date of birth, calculate age in Python when needed
    # Never store age directly — it goes stale every birthday
    date_of_birth = Column(Date, nullable=True)

    # Free text bio
    bio = Column(String, nullable=True)

    # --- App state ---
    is_active = Column(Boolean, default=True)

    # Track if they've completed their profile
    # Useful for showing "complete your profile" prompt
    is_profile_complete = Column(Boolean, default=False)

    # --- Timestamps (automatic, never set manually) ---
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())