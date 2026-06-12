"""
Sync SQLAlchemy engine, session factory, and declarative base.
Works identically against SQLite (local dev) and PostgreSQL (Supabase production)
via the DATABASE_URL switch in config.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

# SQLite requires check_same_thread=False for FastAPI's threaded model
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def create_tables():
    """Create all tables if they don't exist. Called from FastAPI lifespan."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency injection for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
