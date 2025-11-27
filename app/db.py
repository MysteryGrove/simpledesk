"""Database setup utilities for the helpdesk application."""
from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session, declarative_base

# Base directory of the project (one level above this file's directory)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DATABASE_URL = f"sqlite:///{DATA_DIR / 'helpdesk.db'}"

# SQLAlchemy base and engine configuration
Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False)
)


def get_session() -> Session:
    """Return a new SQLAlchemy session."""
    return SessionLocal()


def init_db() -> None:
    """Initialize database tables."""
    # Import models to register them with SQLAlchemy's metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
