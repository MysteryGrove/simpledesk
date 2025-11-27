"""Settings page routes."""
from __future__ import annotations

from flask import Blueprint, redirect, render_template, session, url_for

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

    options = [
        {
            "id": "account",
            "title": "Account profile",
            "description": "Update your name, email, and the details shared with your team.",
            "action": "Manage",
        },
        {
            "id": "notifications",
            "title": "Notifications",
            "description": "Control ticket updates and digest emails so you only get what matters.",
            "action": "Edit",
        },
        {
            "id": "appearance",
            "title": "Appearance",
            "description": "Choose the interface theme and adjust readability preferences.",
            "action": "Customize",
        },
    ]

    return render_template(
        "settings.html",
        sections=sidebar_sections,
        options=options,
        active_section="account",
    )
