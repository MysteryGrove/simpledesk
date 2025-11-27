"""Database initialization tests."""
from __future__ import annotations

import importlib
import os
import sys
import tempfile
import unittest


class DatabaseInitializationTestCase(unittest.TestCase):
    """Tests to ensure new databases start empty."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["DATA_DIR"] = self.temp_dir.name
        sys.modules.pop("app.db", None)
        sys.modules.pop("app.models", None)
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
        sys.modules.pop("app.db", None)
        sys.modules.pop("app.models", None)

    def test_ticket_table_empty_on_first_start(self) -> None:
        """Newly initialized database should not contain tickets."""

        ticket_count = self.session.query(self.models.Ticket).count()
        self.assertEqual(ticket_count, 0)


if __name__ == "__main__":  # pragma: no cover - manual execution
    unittest.main()
