"""Account reset behavior tests."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
import threading
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

    def test_reset_account_clears_existing_sessions(self) -> None:
        """Resetting should invalidate any stale sessions holding ticket data."""

        ready = threading.Event()
        proceed = threading.Event()
        results: dict[str, object] = {}

        def create_ticket_in_thread() -> None:
            worker_session = self.db.get_session()
            ticket = self.models.Ticket(
                title="Threaded Ticket",
                description="Created in background thread",
                status="open",
                priority="medium",
            )
            worker_session.add(ticket)
            worker_session.commit()
            results["worker_session"] = worker_session
            ready.set()
            proceed.wait()
            try:
                results["count_after_reset"] = worker_session.query(self.models.Ticket).count()
            except Exception as exc:  # pragma: no cover - defensive capture
                results["error"] = exc
            finally:
                worker_session.close()

        thread = threading.Thread(target=create_ticket_in_thread)
        thread.start()
        ready.wait()

        with self.client.session_transaction() as flask_session:
            flask_session["user_authenticated"] = True

        response = self.client.post(
            "/settings/reset-account",
            data={"reset_password": "change_me"},
            follow_redirects=False,
        )

        proceed.set()
        thread.join()

        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers.get("Location", ""))

        verification_session = self.db.get_session()
        ticket_count = verification_session.query(self.models.Ticket).count()
        verification_session.close()

        # The session created before reset should not be able to surface old data
        # after the reset completes.
        self.assertNotEqual(results.get("count_after_reset"), 1)
        self.assertEqual(ticket_count, 0)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
