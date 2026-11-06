"""Fixtures compartidas de Pytest (Stage 3: cliente + sesión PG)."""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

# Asegura que `app` sea importable al ejecutar pytest desde backend/ o raíz.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _normalizar_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _asegurar_schema(engine, url: str) -> None:
    """Reaplica migraciones si otro test (p. ej. alembic downgrade) vació el schema."""
    with engine.connect() as conn:
        existe = conn.execute(
            text(
                "SELECT 1 FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename = 'materiales'"
            )
        ).scalar()
    if existe:
        return
    from alembic import command
    from alembic.config import Config

    prev = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    from app.core.config import get_settings

    get_settings.cache_clear()
    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(cfg, "head")
    if prev is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = prev
    get_settings.cache_clear()


def _truncar(engine) -> None:
    with engine.begin() as conn:
        tablas = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
            )
        ).fetchall()
        if tablas:
            nombres = ", ".join(f'"{r[0]}"' for r in tablas)
            conn.execute(text(f"TRUNCATE {nombres} RESTART IDENTITY CASCADE"))


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """Cliente HTTP síncrono contra la app FastAPI (sin override de BD)."""
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


@pytest.fixture(scope="session")
def engine_test():
    """Engine de la BD de pruebas (omitido sin TEST_DATABASE_URL)."""
    raw = os.getenv("TEST_DATABASE_URL")
    if not raw:
        pytest.skip("TEST_DATABASE_URL no configurada")
    url = _normalizar_url(raw)
    eng = create_engine(url, pool_pre_ping=True, poolclass=NullPool, future=True)
    from alembic import command
    from alembic.config import Config

    # alembic/env.py toma la URL desde get_settings() (DATABASE_URL), no solo
    # desde Config.set_main_option — forzar el entorno de test.
    prev_db = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    from app.core.config import get_settings

    get_settings.cache_clear()

    cfg = Config(str(BACKEND_ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    command.upgrade(cfg, "head")
    yield eng
    eng.dispose()
    if prev_db is None:
        os.environ.pop("DATABASE_URL", None)
    else:
        os.environ["DATABASE_URL"] = prev_db
    get_settings.cache_clear()


@pytest.fixture()
def db_session(engine_test) -> Generator[Session, None, None]:
    """Sesión limpia por test (TRUNCATE de tablas de negocio)."""
    url = _normalizar_url(os.environ["TEST_DATABASE_URL"])
    _asegurar_schema(engine_test, url)
    _truncar(engine_test)
    SessionTest = sessionmaker(
        bind=engine_test,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def api_client(engine_test) -> Generator[TestClient, None, None]:
    """TestClient con get_db apuntando a la BD de test."""
    from app.core.config import get_settings
    from app.core.database import get_db
    from app.main import create_app

    url = _normalizar_url(os.environ["TEST_DATABASE_URL"])
    _asegurar_schema(engine_test, url)
    _truncar(engine_test)
    get_settings.cache_clear()
    # La app/settings y el override deben usar la misma BD de test.
    os.environ["DATABASE_URL"] = url
    get_settings.cache_clear()
    app = create_app()

    SessionTest = sessionmaker(
        bind=engine_test,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    def _override_db() -> Generator[Session, None, None]:
        session = SessionTest()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()
