"""Authentication utilities and routes."""
from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, TypeVar

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

AuthCallable = TypeVar("AuthCallable", bound=Callable[..., Any])

auth_bp = Blueprint("auth", __name__)


def _credentials() -> tuple[str, str]:
    """Return admin credentials from environment with sensible defaults."""
    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "password")
    return username, password


def login_required(view_func: AuthCallable) -> AuthCallable:
    """Decorator to enforce authentication for protected routes."""

    @wraps(view_func)
    def wrapper(*args: Any, **kwargs: Any):
        if not session.get("user_authenticated"):
            return redirect(url_for("auth.login"))
        return view_func(*args, **kwargs)

    return wrapper  # type: ignore[return-value]


@auth_bp.route("/login", methods=["GET"])
def login() -> str:
    """Render the login form."""
    if session.get("user_authenticated"):
        return redirect(url_for("tickets.list_tickets"))
    return render_template("login.html")


@auth_bp.route("/login", methods=["POST"])
def login_post():
    """Validate credentials and establish a session."""
    username_env, password_env = _credentials()
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    if username == username_env and password == password_env:
        session["user_authenticated"] = True
        flash("Logged in successfully.", "success")
        return redirect(url_for("tickets.list_tickets"))

    flash("Invalid username or password.", "error")
    return redirect(url_for("auth.login"))


@auth_bp.route("/logout", methods=["GET"])
def logout():
    """Log the user out and clear the session."""
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("auth.login"))
