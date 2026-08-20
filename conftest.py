"""Shared pytest fixtures for CareerCopilot AI tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path so `backend.*` imports work
_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parent
