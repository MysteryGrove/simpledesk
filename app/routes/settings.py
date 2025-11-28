"""Settings page routes."""
from __future__ import annotations

import os
import time
from pathlib import Path

try:
    import resource
except ImportError:  # pragma: no cover - platform-specific
    resource = None  # type: ignore[assignment]

from flask import Blueprint, flash, jsonify, redirect, render_template, request, session, url_for

from app.auth import reset_credentials, set_password, verify_password
from app.db import DATA_DIR, reset_database_state

settings_bp = Blueprint("settings", __name__, url_prefix="/settings")
START_TIME = time.time()

HERO_DESCRIPTION = "Adjust your SimpleDesk preferences to keep work flowing smoothly."

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
    {
        "id": "about",
        "title": "About",
        "description": "Version details and diagnostics",
        "endpoint": "settings.view_about",
    },
]

SECTION_CONTENT = {
    "account": {
        "hero_description": HERO_DESCRIPTION,
        "panel_title": "Account",
        "panel_description": "Update your access quickly: change the administrator password or start fresh by resetting the account.",
    },
    "notifications": {
        "hero_description": HERO_DESCRIPTION,
        "panel_title": "Notifications",
        "panel_description": "Configure reminders, alerts, and summaries when they become available.",
        "coming_soon_detail": "We're building granular notification controls so you can choose when and how you're notified.",
    },
    "appearance": {
        "hero_description": HERO_DESCRIPTION,
        "panel_title": "Appearance",
        "panel_description": "Fine-tune colors, density, and other visual settings as they're released.",
        "coming_soon_detail": "Theme controls are on the way so you can tailor SimpleDesk to your style.",
    },
    "system": {
        "hero_description": HERO_DESCRIPTION,
        "panel_title": "System",
        "panel_description": "Configure automation, uptime controls, and integrations once they're available.",
        "coming_soon_detail": "We're preparing system management tools to help you automate and maintain SimpleDesk.",
    },
    "about": {
        "hero_description": HERO_DESCRIPTION,
        "panel_title": "About SimpleDesk",
        "panel_description": "See version details, credits, and live service resource usage.",
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


@settings_bp.route("/about", methods=["GET"])
def view_about():
    """Render the about settings page."""
    return _render_settings_page("about")


@settings_bp.route("/stats", methods=["GET"])
def service_stats():
    """Return live CPU and memory usage for the SimpleDesk service."""

    cpu_percent = _get_cpu_percent()
    memory_mb = _get_memory_usage_mb()
    uptime = _get_uptime()
    db_size_mb = _get_db_size_mb()

    return jsonify({
        "cpu_percent": round(cpu_percent, 2),
        "memory_mb": round(memory_mb, 2),
        "uptime": uptime,
        "db_size_mb": round(db_size_mb, 2),
    })


def _get_cpu_percent() -> float:
    """Return process CPU usage percentage using psutil when available."""

    try:
        import psutil  # type: ignore
    except ImportError:
        return _fallback_cpu_percent()

    process = psutil.Process()
    return process.cpu_percent(interval=0.1)


def _get_memory_usage_mb() -> float:
    """Return process memory usage in MB using psutil when available."""

    try:
        import psutil  # type: ignore
    except ImportError:
        return _fallback_memory_usage_mb()

    process = psutil.Process()
    return process.memory_info().rss / (1024 * 1024)


def _fallback_cpu_percent() -> float:
    """Estimate CPU usage without psutil using system load averages."""

    try:
        load_avg = os.getloadavg()[0]
    except (OSError, ValueError, AttributeError):  # pragma: no cover - platform-specific
        return 0.0

    cpu_count = os.cpu_count() or 1
    return max(0.0, (load_avg / cpu_count) * 100)


def _fallback_memory_usage_mb() -> float:
    """Estimate memory usage without psutil using resource module data."""

    if resource is None:
        return 0.0

    try:
        usage = resource.getrusage(resource.RUSAGE_SELF)
    except (AttributeError, ValueError):  # pragma: no cover - platform-specific
        return 0.0

    rss_kb = getattr(usage, "ru_maxrss", 0) or 0
    return max(0.0, rss_kb / 1024)


def _get_uptime() -> str:
    """Return a human-readable uptime string since the app started."""

    elapsed_seconds = max(0, int(time.time() - START_TIME))
    days, remainder = divmod(elapsed_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")

    return " ".join(parts)


def _get_db_size_mb() -> float:
    """Return the current database file size in megabytes."""

    db_path = Path(DATA_DIR) / "helpdesk.db"
    if not db_path.exists():
        return 0.0

    return db_path.stat().st_size / (1024 * 1024)


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

    reset_database_state()
    reset_credentials()
    session.clear()
    flash("Account reset. Log in with the default admin/password credentials.", "success")
    return redirect(url_for("auth.login"))
