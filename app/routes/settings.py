"""Settings page routes."""
from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth import reset_credentials, set_password, verify_password
from app.db import DATA_DIR, SessionLocal, engine, init_db, rebuild_engine, reset_data_dir

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")

SIDEBAR_SECTIONS = [
    {
        "id": "account",
        "title": "Account",
        "description": "Profile, access, and security",
        "endpoint": "settings.view_settings",
    },
    {
        "id": "notifications",
        "title": "Notifications",
        "description": "Alerts and reminders",
        "endpoint": "settings.view_notifications",
    },
    {
        "id": "appearance",
        "title": "Appearance",
        "description": "Theme and personalization",
        "endpoint": "settings.view_appearance",
    },
    {
        "id": "system",
        "title": "System",
        "description": "Automation and maintenance",
        "endpoint": "settings.view_system",
    },
]

SECTION_CONTENT = {
    "account": {
        "hero_description": "Adjust your SimpleDesk preferences to keep work flowing smoothly.",
        "panel_title": "Account controls",
        "panel_description": "Update your access quickly: change the administrator password or start fresh by resetting the account.",
    },
    "notifications": {
        "hero_description": "Stay tuned for smarter alerts to keep you and your team in sync.",
        "panel_title": "Notifications",
        "panel_description": "Configure reminders, alerts, and summaries when they become available.",
        "coming_soon_detail": "We're building granular notification controls so you can choose when and how you're notified.",
    },
    "appearance": {
        "hero_description": "Personalize your workspace with themes and layout preferences.",
        "panel_title": "Appearance",
        "panel_description": "Fine-tune colors, density, and other visual settings as they're released.",
        "coming_soon_detail": "Theme controls are on the way so you can tailor SimpleDesk to your style.",
    },
    "system": {
        "hero_description": "Set up automations and maintenance windows to keep operations running smoothly.",
        "panel_title": "System",
        "panel_description": "Configure automation, uptime controls, and integrations once they're available.",
        "coming_soon_detail": "We're preparing system management tools to help you automate and maintain SimpleDesk.",
    },
}


@settings_bp.before_request
def require_authentication():
    """Ensure settings pages require authentication."""
    if not session.get("user_authenticated"):
        return redirect(url_for("auth.login"))


def _render_settings_page(active_section: str):
    """Render the settings page for the selected section."""
    section_content = SECTION_CONTENT.get(active_section, SECTION_CONTENT["account"])

    return render_template(
        "settings.html",
        sections=SIDEBAR_SECTIONS,
        active_section=active_section,
        section_content=section_content,
    )


@settings_bp.route("/", methods=["GET"])
def view_settings():
    """Render the account settings page."""
    return _render_settings_page("account")


@settings_bp.route("/notifications", methods=["GET"])
def view_notifications():
    """Render the notifications settings page."""
    return _render_settings_page("notifications")


@settings_bp.route("/appearance", methods=["GET"])
def view_appearance():
    """Render the appearance settings page."""
    return _render_settings_page("appearance")


@settings_bp.route("/system", methods=["GET"])
def view_system():
    """Render the system settings page."""
    return _render_settings_page("system")


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
    session.pop("pending_password_change", None)
    flash("Password updated successfully.", "success")
    return redirect(url_for("settings.view_settings"))


@settings_bp.route("/reset-account", methods=["POST"])
def reset_account():
    """Reset the account by wiping data and credentials."""

    password = request.form.get("reset_password", "").strip()

    if not password:
        flash("Please enter your password to confirm the reset.", "error")
        return redirect(url_for("settings.view_settings"))

    if not verify_password(password):
        flash("Password did not match. Account was not reset.", "error")
        return redirect(url_for("settings.view_settings"))

    SessionLocal.remove()
    engine.dispose()

    reset_data_dir()
    rebuild_engine()
    reset_credentials()
    init_db()
    session.clear()
    flash("Account reset. Log in with the default admin/password credentials.", "success")
    return redirect(url_for("auth.login"))
