"""Tests de migraciones Alembic contra PostgreSQL.

Requieren `TEST_DATABASE_URL` (o se omiten). Ciclo: upgrade head →
verificar 36 tablas → downgrade a 0001 → upgrade head de nuevo.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

_TIENE_TEST_DB = bool(os.getenv("TEST_DATABASE_URL"))

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = BACKEND_ROOT / "alembic.ini"

TABLAS_NEGOCIO = [
    "categorias_material",
    "unidades_medida",
    "materiales",
    "bodegas",
    "existencias",
    "movimientos_inventario",
    "items_movimiento_inventario",
    "categorias_producto",
    "productos",
    "variantes_producto",
    "tecnicas_produccion",
    "tecnicas_producto",
    "recetas_producto",
    "items_receta_producto",
    "perfiles_costo_producto",
    "categorias_costo",
    "clientes",
    "pedidos",
    "items_pedido",
    "disenos_pedido",
    "historial_estado_pedido",
    "ordenes_produccion",
    "items_orden_produccion",
    "consumos_produccion",
    "asientos_costo_produccion",
    "proveedores",
    "compras",
    "items_compra",
    "metodos_pago",
    "cuentas_caja",
    "pagos",
    "categorias_gasto",
    "gastos",
    "pagos_gasto",
    "pagos_proveedor",
    "movimientos_caja",
]


def _alembic_config(database_url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", database_url)
    cfg.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    return cfg


def _tablas_publicas(engine) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT tablename FROM pg_tables "
                "WHERE schemaname = 'public' AND tablename != 'alembic_version'"
            )
        ).fetchall()
    return {r[0] for r in rows}


def _reset_schema(engine) -> None:
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public"))


@pytest.mark.skipif(not _TIENE_TEST_DB, reason="TEST_DATABASE_URL no definido")
def test_alembic_upgrade_head_crea_36_tablas(test_database_url: str | None) -> None:
    assert test_database_url is not None
    engine = create_engine(test_database_url, pool_pre_ping=True, future=True)
    try:
        _reset_schema(engine)
        # Forzar URL en settings vía env (alembic/env.py lee get_settings)
        os.environ["DATABASE_URL"] = test_database_url
        from app.core.config import get_settings

        get_settings.cache_clear()

        cfg = _alembic_config(test_database_url)
        command.upgrade(cfg, "head")

        tablas = _tablas_publicas(engine)
        assert len(tablas) == 36
        assert set(TABLAS_NEGOCIO) == tablas

        with engine.connect() as conn:
            # pedido_id NOT NULL
            nullable = conn.execute(
                text(
                    "SELECT is_nullable FROM information_schema.columns "
                    "WHERE table_name = 'ordenes_produccion' AND column_name = 'pedido_id'"
                )
            ).scalar_one()
            assert nullable == "NO"

            # columnas aprobadas en movimientos
            cols = {
                r[0]
                for r in conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_name = 'movimientos_inventario'"
                    )
                )
            }
            assert "estado" in cols
            assert "grupo_transferencia_id" in cols

            version = conn.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one()
            assert version == "20261106_0002"
    finally:
        engine.dispose()
        from app.core.config import get_settings

        get_settings.cache_clear()


@pytest.mark.skipif(not _TIENE_TEST_DB, reason="TEST_DATABASE_URL no definido")
def test_alembic_downgrade_y_reupgrade(test_database_url: str | None) -> None:
    assert test_database_url is not None
    engine = create_engine(test_database_url, pool_pre_ping=True, future=True)
    try:
        _reset_schema(engine)
        os.environ["DATABASE_URL"] = test_database_url
        from app.core.config import get_settings

        get_settings.cache_clear()
        cfg = _alembic_config(test_database_url)

        command.upgrade(cfg, "head")
        assert len(_tablas_publicas(engine)) == 36

        # Downgrade al stub Stage 1 (sin tablas de negocio)
        command.downgrade(cfg, "20261106_0001")
        assert _tablas_publicas(engine) == set()

        command.upgrade(cfg, "head")
        assert len(_tablas_publicas(engine)) == 36
    finally:
        engine.dispose()
        from app.core.config import get_settings

        get_settings.cache_clear()
