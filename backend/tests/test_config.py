"""Pruebas de carga de configuración."""

import pytest
from pydantic import ValidationError


def test_settings_carga_valores_por_defecto(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://sublimanager:sublimanager@localhost:5432/sublimanager",
    )

    from app.core.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()
    assert settings.app_name == "SubliManager"
    assert "postgresql" in settings.sqlalchemy_database_url
    assert "+psycopg" in settings.sqlalchemy_database_url
    get_settings.cache_clear()


def test_settings_rechaza_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./test.db")

    from app.core.config import Settings, get_settings

    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        Settings()
    get_settings.cache_clear()


def test_constantes_nomenclatura_espanol() -> None:
    from app.core.constants import (
        API_V1_PREFIX,
        PEDIDO_ID_REQUERIDO_EN_OP,
        RUTAS_RECURSOS_V1,
    )

    assert API_V1_PREFIX == "/api/v1"
    assert RUTAS_RECURSOS_V1["pedidos"] == "/api/v1/pedidos"
    assert RUTAS_RECURSOS_V1["ordenes_produccion"] == "/api/v1/ordenes-produccion"
    assert RUTAS_RECURSOS_V1["movimientos_inventario"] == "/api/v1/movimientos-inventario"
    assert PEDIDO_ID_REQUERIDO_EN_OP is True


def test_settings_normaliza_postgres_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:pass@localhost:5432/db",
    )

    from app.core.config import Settings, get_settings

    get_settings.cache_clear()
    settings = Settings()
    assert settings.sqlalchemy_database_url.startswith("postgresql+psycopg://")
    get_settings.cache_clear()
