"""Settings about page and service stats tests."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest


class SettingsAboutTestCase(unittest.TestCase):
    """Validate the settings about page and live stats endpoint."""

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

    def tearDown(self) -> None:
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

    def test_about_page_shows_version_and_author(self) -> None:
        """The about section should render version and author details."""

        with self.client.session_transaction() as flask_session:
            flask_session["user_authenticated"] = True

        response = self.client.get("/settings/about")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Version 1.3", response.data)
        self.assertIn(b"MysteryGrove", response.data)
        self.assertIn(b"Nerd stats", response.data)
        self.assertIn(b"Adjust your SimpleDesk preferences", response.data)

    def test_service_stats_returns_usage_metrics(self) -> None:
        """The stats endpoint should surface CPU and memory usage."""

        with self.client.session_transaction() as flask_session:
            flask_session["user_authenticated"] = True

        response = self.client.get("/settings/stats")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("cpu_percent", payload)
        self.assertIn("memory_mb", payload)
        self.assertGreaterEqual(payload["cpu_percent"], 0)
        self.assertGreaterEqual(payload["memory_mb"], 0)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
