"""Fixtures compartidas de Pytest."""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Asegura que `app` sea importable al ejecutar pytest desde backend/ o raíz.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


@pytest.fixture()
def client() -> TestClient:
    """Cliente HTTP síncrono contra la app FastAPI."""
    from app.core.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture()
def test_database_url() -> str | None:
    """URL de PG para tests de integración; None si no está configurada."""
    return os.getenv("TEST_DATABASE_URL") or None
