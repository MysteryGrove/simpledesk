"""Settings page routes."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth import reset_credentials, set_password
from app.db import DATA_DIR, SessionLocal, init_db, engine

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")


@settings_bp.before_request
def require_authentication():
    """Ensure settings pages require authentication."""
    if not session.get("user_authenticated"):
        return redirect(url_for("auth.login"))


@settings_bp.route("/", methods=["GET"])
def view_settings():
    """Render the settings overview page."""
    sidebar_sections = [
        {"id": "account", "title": "Account", "description": "Profile, access, and security"},
        {"id": "notifications", "title": "Notifications", "description": "Alerts and reminders"},
        {"id": "appearance", "title": "Appearance", "description": "Theme and personalization"},
    ]

    return render_template(
        "settings.html",
        sections=sidebar_sections,
        active_section="account",
    )


@settings_bp.route("/change-password", methods=["POST"])
def change_password():
    """Handle password updates from the settings page."""

    new_password = request.form.get("new_password", "").strip()
    confirm_password = request.form.get("confirm_password", "").strip()

    if not new_password or not confirm_password:
        flash("Both password fields are required.", "error")
        return redirect(url_for("settings.view_settings"))

    if new_password != confirm_password:
        flash("Passwords must match.", "error")
        return redirect(url_for("settings.view_settings"))

    set_password(new_password)
    flash("Password updated successfully.", "success")
    return redirect(url_for("settings.view_settings"))


@settings_bp.route("/reset-account", methods=["POST"])
def reset_account():
    """Reset the account by wiping data and credentials."""

    SessionLocal.remove()
    engine.dispose()

    db_path = DATA_DIR / "helpdesk.db"
    if db_path.exists():
        db_path.unlink()

    reset_credentials()
    init_db()
    session.clear()
    flash("Account reset. Log in with the default admin/password credentials.", "success")
    return redirect(url_for("auth.login"))
