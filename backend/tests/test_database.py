"""Tests de integración con PostgreSQL (se omiten sin TEST_DATABASE_URL)."""

import os

import pytest
from sqlalchemy import create_engine, text

_TIENE_TEST_DB = bool(os.getenv("TEST_DATABASE_URL"))


@pytest.mark.skipif(not _TIENE_TEST_DB, reason="TEST_DATABASE_URL no definido")
def test_conexion_postgres(test_database_url: str | None) -> None:
    assert test_database_url is not None
    engine = create_engine(test_database_url, pool_pre_ping=True, future=True)
    with engine.connect() as conn:
        resultado = conn.execute(text("SELECT 1")).scalar_one()
    assert resultado == 1
    engine.dispose()
