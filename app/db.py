"""Database setup utilities for the helpdesk application."""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, Session, declarative_base

# Base directory of the project (one level above this file's directory)
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("DATA_DIR", BASE_DIR / "data"))
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
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # Import models to register them with SQLAlchemy's metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def reset_data_dir() -> None:
    """Remove all stored application data and recreate directories."""

    if DATA_DIR.exists():
        for path in DATA_DIR.iterdir():
            if path.is_file() or path.is_symlink():
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            else:
                shutil.rmtree(path)
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def rebuild_engine() -> None:
    """Recreate the database engine and rebind sessions to it."""

    global engine
    SessionLocal.remove()
    engine.dispose()
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    SessionLocal.configure(bind=engine)
