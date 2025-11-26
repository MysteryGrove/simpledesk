"""Flask application factory."""
from __future__ import annotations

import os
from flask import Flask, redirect, session, url_for

from app.db import DATABASE_URL, SessionLocal, init_db
from app.auth import auth_bp
from app.routes.tickets import tickets_bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
    app.config["DATABASE_URL"] = str(DATABASE_URL)

    # Ensure database tables exist on startup
    init_db()

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)

    @app.route("/")
    def index():
        if session.get("user_authenticated"):
            return redirect(url_for("tickets.list_tickets"))
        return redirect(url_for("auth.login"))

    @app.teardown_appcontext
    def remove_session(exception: Exception | None = None) -> None:  # pragma: no cover - teardown
        """Remove scoped session when app context tears down."""
        SessionLocal.remove()

    return app
