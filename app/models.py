"""Database models for the helpdesk application."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Ticket(Base):
    """Represents a helpdesk ticket."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="open")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="medium")
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="ticket", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ticket id={self.id} title={self.title!r}>"


class Comment(Base):
    """Represents a comment attached to a ticket."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    ticket: Mapped[Ticket] = relationship("Ticket", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment id={self.id} ticket_id={self.ticket_id}>"


class DocumentationSection(Base):
    """Top-level documentation section containing subsections."""

    __tablename__ = "documentation_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    subsections: Mapped[List["DocumentationSubsection"]] = relationship(
        "DocumentationSubsection",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="DocumentationSubsection.id",
    )

    def __repr__(self) -> str:  # pragma: no cover - repr
        return f"<DocumentationSection id={self.id} title={self.title!r}>"


class DocumentationSubsection(Base):
    """Subsection nested under a documentation section."""

    __tablename__ = "documentation_subsections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    section_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documentation_sections.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    section: Mapped[DocumentationSection] = relationship(
        "DocumentationSection", back_populates="subsections"
    )
    pages: Mapped[List["DocumentationPage"]] = relationship(
        "DocumentationPage",
        back_populates="subsection",
        cascade="all, delete-orphan",
        order_by="DocumentationPage.id",
    )

    def __repr__(self) -> str:  # pragma: no cover - repr
        return f"<DocumentationSubsection id={self.id} title={self.title!r}>"


class DocumentationPage(Base):
    """Individual documentation page content within a subsection."""

    __tablename__ = "documentation_pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subsection_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("documentation_subsections.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    author: Mapped[str] = mapped_column(String(100), nullable=False, default="You")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    subsection: Mapped[DocumentationSubsection] = relationship(
        "DocumentationSubsection", back_populates="pages"
    )

    def __repr__(self) -> str:  # pragma: no cover - repr
        return f"<DocumentationPage id={self.id} title={self.title!r}>"
