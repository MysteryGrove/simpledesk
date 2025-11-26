"""Ticket-related routes."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Comment, Ticket


tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")

STATUS_OPTIONS = ["open", "closed", "cancelled"]
PRIORITY_OPTIONS = ["low", "medium", "high", "urgent"]


def _parse_due_date(raw_value: str) -> Optional[datetime]:
    """Parse an ISO date string to a datetime or return None."""
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return None


def _get_session() -> Session:
    """Helper to retrieve a database session."""
    return get_session()


@tickets_bp.before_request
def require_authentication():
    """Ensure all ticket routes require authentication."""
    if not session.get("user_authenticated"):
        return redirect(url_for("auth.login"))


@tickets_bp.route("/", methods=["GET"])
def list_tickets():
    """Render a list of tickets with optional filtering."""
    session = _get_session()
    query = select(Ticket)

    status = request.args.get("status")
    priority = request.args.get("priority")
    search = request.args.get("search")

    if status and status in STATUS_OPTIONS:
        query = query.where(Ticket.status == status)
    if priority and priority in PRIORITY_OPTIONS:
        query = query.where(Ticket.priority == priority)
    if search:
        like_expr = f"%{search}%"
        query = query.where(
            or_(Ticket.title.ilike(like_expr), Ticket.description.ilike(like_expr))
        )

    tickets = session.scalars(query.order_by(Ticket.created_at.desc())).all()
    return render_template(
        "tickets_list.html",
        tickets=tickets,
        status_options=STATUS_OPTIONS,
        priority_options=PRIORITY_OPTIONS,
        current_status=status,
        current_priority=priority,
        search_term=search or "",
    )


@tickets_bp.route("/new", methods=["GET"])
def new_ticket():
    """Show the new ticket form."""
    return render_template(
        "ticket_form.html",
        ticket=None,
        status_options=STATUS_OPTIONS,
        priority_options=PRIORITY_OPTIONS,
        form_action=url_for("tickets.create_ticket"),
        form_title="Create Ticket",
    )


@tickets_bp.route("/", methods=["POST"])
def create_ticket():
    """Create a new ticket from form data."""
    session = _get_session()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    status = request.form.get("status", "open")
    priority = request.form.get("priority", "medium")
    due_date_raw = request.form.get("due_date", "")

    if not title or not description:
        flash("Title and description are required.", "error")
        return redirect(url_for("tickets.new_ticket"))

    if status not in STATUS_OPTIONS:
        status = "open"
    if priority not in PRIORITY_OPTIONS:
        priority = "medium"

    due_date = _parse_due_date(due_date_raw)
    if due_date_raw and due_date is None:
        flash("Invalid due date format.", "error")
        return redirect(url_for("tickets.new_ticket"))

    ticket = Ticket(
        title=title,
        description=description,
        status=status,
        priority=priority,
        due_date=due_date,
    )
    session.add(ticket)
    session.commit()
    flash("Ticket created successfully.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


def _get_ticket_or_404(session: Session, ticket_id: int) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)
    return ticket


@tickets_bp.route("/<int:ticket_id>", methods=["GET"])
def ticket_detail(ticket_id: int):
    """Show details for a ticket including comments."""
    session = _get_session()
    ticket = _get_ticket_or_404(session, ticket_id)
    comments = (
        session.query(Comment)
        .filter(Comment.ticket_id == ticket.id)
        .order_by(Comment.created_at.asc())
        .all()
    )
    return render_template(
        "ticket_detail.html",
        ticket=ticket,
        comments=comments,
        status_options=STATUS_OPTIONS,
        priority_options=PRIORITY_OPTIONS,
    )


@tickets_bp.route("/<int:ticket_id>/edit", methods=["GET"])
def edit_ticket(ticket_id: int):
    """Render the edit form for an existing ticket."""
    session = _get_session()
    ticket = _get_ticket_or_404(session, ticket_id)
    return render_template(
        "ticket_form.html",
        ticket=ticket,
        status_options=STATUS_OPTIONS,
        priority_options=PRIORITY_OPTIONS,
        form_action=url_for("tickets.update_ticket", ticket_id=ticket.id),
        form_title="Edit Ticket",
    )


@tickets_bp.route("/<int:ticket_id>/update", methods=["POST"])
def update_ticket(ticket_id: int):
    """Update fields on an existing ticket."""
    session = _get_session()
    ticket = _get_ticket_or_404(session, ticket_id)

    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    status = request.form.get("status", ticket.status)
    priority = request.form.get("priority", ticket.priority)
    due_date_raw = request.form.get("due_date", "")

    if not title or not description:
        flash("Title and description are required.", "error")
        return redirect(url_for("tickets.edit_ticket", ticket_id=ticket.id))

    ticket.title = title
    ticket.description = description
    ticket.status = status if status in STATUS_OPTIONS else ticket.status
    ticket.priority = priority if priority in PRIORITY_OPTIONS else ticket.priority

    due_date = _parse_due_date(due_date_raw)
    if due_date_raw and due_date is None:
        flash("Invalid due date format.", "error")
        return redirect(url_for("tickets.edit_ticket", ticket_id=ticket.id))
    ticket.due_date = due_date

    session.add(ticket)
    session.commit()
    flash("Ticket updated successfully.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@tickets_bp.route("/<int:ticket_id>/status", methods=["POST"])
def change_status(ticket_id: int):
    """Change the status of a ticket."""
    session = _get_session()
    ticket = _get_ticket_or_404(session, ticket_id)
    new_status = request.form.get("status", "")
    if new_status not in STATUS_OPTIONS:
        flash("Invalid status value.", "error")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    ticket.status = new_status
    session.commit()
    flash("Status updated.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@tickets_bp.route("/<int:ticket_id>/comments", methods=["POST"])
def add_comment(ticket_id: int):
    """Add a comment to a ticket."""
    session = _get_session()
    ticket = _get_ticket_or_404(session, ticket_id)
    body = request.form.get("body", "").strip()
    if not body:
        flash("Comment cannot be empty.", "error")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    comment = Comment(ticket_id=ticket.id, body=body)
    session.add(comment)
    session.commit()
    flash("Comment added.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))
