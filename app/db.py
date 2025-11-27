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

    _seed_sample_data()


def _seed_sample_data() -> None:
    """Populate the database with starter tickets if it's empty."""

    from app.models import Ticket

    session = SessionLocal()

    try:
        if session.query(Ticket).count() > 0:
            return

        session.add_all(
            [
                Ticket(
                    title="VPN connection is timing out",
                    description=(
                        "Remote staff report frequent disconnects when joining the VPN. "
                        "Investigate gateway logs and connection limits."
                    ),
                    status="open",
                    priority="urgent",
                ),
                Ticket(
                    title="Email digest is missing project updates",
                    description=(
                        "The daily digest stopped including tasks from the Project Phoenix board. "
                        "Check notification rules and integrations."
                    ),
                    status="open",
                    priority="medium",
                ),
                Ticket(
                    title="New hire access checklist",
                    description=(
                        "Provision accounts for the incoming customer success manager, including CRM, "
                        "analytics, and support tools."
                    ),
                    status="closed",
                    priority="low",
                ),
            ]
        )
        session.commit()
    finally:
        session.close()
