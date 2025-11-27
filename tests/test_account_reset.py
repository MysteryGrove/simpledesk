"""Account reset behavior tests."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest


class AccountResetTestCase(unittest.TestCase):
    """Ensure resetting the account wipes application data."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATA_DIR"] = self.temp_dir.name

        for module in (
            "app",
            "app.auth",
            "app.db",
            "app.models",
            "app.routes.settings",
            "app.routes.tickets",
        ):
            sys.modules.pop(module, None)

        self.app_module = importlib.import_module("app")
        importlib.reload(self.app_module)
        self.app = self.app_module.create_app()
        self.client = self.app.test_client()

        self.db = importlib.import_module("app.db")
        importlib.reload(self.db)
        self.models = importlib.import_module("app.models")
        importlib.reload(self.models)

        self.db.init_db()
        self.session = self.db.get_session()

    def tearDown(self) -> None:
        self.session.close()
        self.db.engine.dispose()
        self.temp_dir.cleanup()
        os.environ.pop("DATA_DIR", None)
        for module in (
            "app",
            "app.auth",
            "app.db",
            "app.models",
            "app.routes.settings",
            "app.routes.tickets",
        ):
            sys.modules.pop(module, None)

    def test_reset_account_removes_all_tickets(self) -> None:
        """Resetting should clear tickets to mimic a fresh install."""

        ticket = self.models.Ticket(
            title="Example",
            description="Sample ticket to reset",
            status="open",
            priority="medium",
        )
        self.session.add(ticket)
        self.session.commit()

        with self.client.session_transaction() as flask_session:
            flask_session["user_authenticated"] = True

        response = self.client.post(
            "/settings/reset-account",
            data={"reset_password": "change_me"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))

        self.session.close()
        self.session = self.db.get_session()
        ticket_count = self.session.query(self.models.Ticket).count()
        self.assertEqual(ticket_count, 0)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
