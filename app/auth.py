"""Authentication utilities and routes."""
from __future__ import annotations

import os
import json
from functools import wraps
from typing import Any, Callable, TypeVar

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.db import DATA_DIR

AuthCallable = TypeVar("AuthCallable", bound=Callable[..., Any])

auth_bp = Blueprint("auth", __name__)


_CREDENTIALS_FILE = DATA_DIR / "credentials.json"


def _load_persisted_credentials() -> tuple[str, str] | None:
    """Read persisted credentials if they exist and are valid."""

    if not _CREDENTIALS_FILE.exists():
        return None

    try:
        data = json.loads(_CREDENTIALS_FILE.read_text())
    except json.JSONDecodeError:
        return None

    username = data.get("username")
    password = data.get("password")
    if isinstance(username, str) and isinstance(password, str):
        return username, password
    return None


def _write_credentials(username: str, password: str) -> tuple[str, str]:
    """Persist credentials to disk and return them."""

    _CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CREDENTIALS_FILE.write_text(json.dumps({"username": username, "password": password}))
    return username, password


def _credentials() -> tuple[str, str]:
    """Return admin credentials from environment with sensible defaults."""
    persisted = _load_persisted_credentials()
    if persisted:
        return persisted

    username = os.environ.get("ADMIN_USERNAME", "admin")
    password = os.environ.get("ADMIN_PASSWORD", "password")
    return username, password


def set_password(new_password: str) -> tuple[str, str]:
    """Persist a new password while retaining the current username."""

    username, _ = _credentials()
    return _write_credentials(username, new_password)


def verify_password(password: str) -> bool:
    """Check whether the provided password matches the stored credentials."""

    _, current_password = _credentials()
    return password == current_password


def reset_credentials() -> tuple[str, str]:
    """Remove persisted credentials and return the defaults."""

    if _CREDENTIALS_FILE.exists():
        _CREDENTIALS_FILE.unlink()
    return _credentials()


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
