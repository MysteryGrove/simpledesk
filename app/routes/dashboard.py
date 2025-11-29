"""Dashboard route and helpers for the home experience."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from flask import Blueprint, redirect, render_template, session, url_for
from sqlalchemy import select

from app.db import get_session
from app.models import Comment, Ticket


dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


def _get_session():
    """Helper to retrieve a database session."""

    return get_session()


@dashboard_bp.before_request
def require_authentication():
    """Ensure dashboard routes require authentication."""

    if not session.get("user_authenticated"):
        return redirect(url_for("auth.login"))
    return None


def _summaries(db_session) -> dict[str, int]:
    """Calculate counts for the overview cards."""

    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), datetime.min.time())
    today_end = datetime.combine(now.date(), datetime.max.time())
    week_end = now + timedelta(days=7)
    start_of_week = datetime.combine(
        (now - timedelta(days=now.weekday())).date(), datetime.min.time()
    )
    end_of_week = start_of_week + timedelta(days=7)

    open_tickets = db_session.query(Ticket).filter(Ticket.status == "open").count()
    closed_this_week = (
        db_session.query(Ticket)
        .filter(
            Ticket.status == "closed",
            Ticket.updated_at >= start_of_week,
            Ticket.updated_at < end_of_week,
        )
        .count()
    )
    due_this_week = (
        db_session.query(Ticket)
        .filter(
            Ticket.due_date.is_not(None),
            Ticket.due_date > today_end,
            Ticket.due_date <= week_end,
            Ticket.status != "closed",
        )
        .count()
    )
    overdue = (
        db_session.query(Ticket)
        .filter(
            Ticket.due_date.is_not(None),
            Ticket.due_date < now,
            Ticket.status == "open",
        )
        .count()
    )

    return {
        "open_tickets": open_tickets,
        "closed_this_week": closed_this_week,
        "due_this_week": due_this_week,
        "overdue": overdue,
    }


def _recent_activity(db_session) -> List[dict]:
    """Combine recent ticket updates and comments into a single timeline."""

    ticket_events = db_session.scalars(
        select(Ticket).order_by(Ticket.updated_at.desc()).limit(10)
    ).all()
    comment_events = db_session.scalars(
        select(Comment).order_by(Comment.created_at.desc()).limit(10)
    ).all()

    events: List[dict] = []

    for ticket in ticket_events:
        action = "created" if ticket.created_at == ticket.updated_at else "updated"
        events.append(
            {
                "timestamp": ticket.updated_at,
                "ticket_id": ticket.id,
                "ticket_title": ticket.title,
                "action": action,
            }
        )

    for comment in comment_events:
        ticket = comment.ticket
        events.append(
            {
                "timestamp": comment.created_at,
                "ticket_id": comment.ticket_id,
                "ticket_title": ticket.title if ticket else "Ticket",
                "action": "commented",
            }
        )

    events.sort(key=lambda item: item["timestamp"], reverse=True)
    return events[:10]


@dashboard_bp.route("/", methods=["GET"])
def view_dashboard():
    """Render the dashboard overview."""

    db_session = _get_session()

    summary = _summaries(db_session)
    my_tickets = db_session.scalars(
        select(Ticket).order_by(Ticket.updated_at.desc()).limit(5)
    ).all()
    due_soon = db_session.scalars(
        select(Ticket)
        .where(Ticket.due_date.is_not(None), Ticket.status != "closed")
        .order_by(Ticket.due_date.asc())
        .limit(5)
    ).all()
    activity = _recent_activity(db_session)

    current_user = session.get("username", "Admin")

    return render_template(
        "dashboard.html",
        user_name=current_user,
        summary=summary,
        my_tickets=my_tickets,
        due_soon=due_soon,
        activity=activity,
    )

