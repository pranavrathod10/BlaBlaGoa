from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings


# The engine is the actual connection to your database
# It reads the URL from your settings (which came from .env)
engine = create_engine(settings.DATABASE_URL)

# SessionLocal is a factory — calling it gives you one database session
# A session is like one conversation with the database
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# Base class for all your database table definitions
# Every model (User, Message, Conversation) will inherit from this
class Base(DeclarativeBase):
    pass


# This is a dependency — FastAPI calls this for every request
# It gives the request a fresh DB session, then closes it when done
def get_db():
    db = SessionLocal()
    try:
        yield db        # hand the session to the route function
    finally:
        db.close()      # always close, even if an error happened