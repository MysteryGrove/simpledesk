"""Test configuration for ensuring project imports."""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repository root is on sys.path so `app` can be imported during tests.
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
