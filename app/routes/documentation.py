"""Documentation routes and views."""
from __future__ import annotations

from flask import Blueprint, redirect, render_template, session, url_for


documentation_bp = Blueprint("documentation", __name__, url_prefix="/documentation")


@documentation_bp.before_request
def require_authentication():
    """Ensure documentation pages are available only to authenticated users."""
    if not session.get("user_authenticated"):
        return redirect(url_for("auth.login"))
    return None


@documentation_bp.route("/", methods=["GET"])
def view_documentation() -> str:
    """Render the documentation workspace."""
    return render_template("documentation.html")
