"""Smoke tests de importación y metadata de modelos (Stage 2)."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect

from app.core.database import Base
from app.models import (
    TABLAS_NEGOCIO,
    OrdenProduccion,
    Pedido,
    MovimientoInventario,
)
from app.models.enums import (
    EstadoMovimientoInventario,
    EstadoPedido,
    TipoMovimientoInventario,
)


TABLAS_ESPERADAS = {
    # A
    "categorias_material",
    "unidades_medida",
    "materiales",
    "bodegas",
    "existencias",
    "movimientos_inventario",
    "items_movimiento_inventario",
    # B
    "categorias_producto",
    "productos",
    "variantes_producto",
    "tecnicas_produccion",
    "tecnicas_producto",
    # C
    "recetas_producto",
    "items_receta_producto",
    "perfiles_costo_producto",
    "categorias_costo",
    # D
    "clientes",
    "pedidos",
    "items_pedido",
    "disenos_pedido",
    "historial_estado_pedido",
    # E
    "ordenes_produccion",
    "items_orden_produccion",
    "consumos_produccion",
    "asientos_costo_produccion",
    # F
    "proveedores",
    "compras",
    "items_compra",
    # G
    "metodos_pago",
    "cuentas_caja",
    "pagos",
    "categorias_gasto",
    "gastos",
    "pagos_gasto",
    "pagos_proveedor",
    "movimientos_caja",
}


def test_conteo_36_tablas_negocio() -> None:
    assert len(TABLAS_NEGOCIO) == 36
    assert set(TABLAS_NEGOCIO) == TABLAS_ESPERADAS


def test_metadata_registra_todas_las_tablas() -> None:
    assert set(Base.metadata.tables.keys()) == TABLAS_ESPERADAS


def test_pedido_id_not_null_en_orden_produccion() -> None:
    col = OrdenProduccion.__table__.c.pedido_id
    assert col.nullable is False


def test_movimientos_tienen_estado_y_grupo_transferencia() -> None:
    cols = MovimientoInventario.__table__.c
    assert "estado" in cols
    assert "grupo_transferencia_id" in cols
    assert cols.estado.nullable is False
    assert cols.grupo_transferencia_id.nullable is True


def test_descuento_pedido_es_columna_monetaria() -> None:
    col = Pedido.__table__.c.descuento
    assert col.type.precision == 14
    assert col.type.scale == 2


@pytest.mark.parametrize(
    ("enum_cls", "esperado"),
    [
        (EstadoPedido, "PENDIENTE"),
        (EstadoMovimientoInventario, "CONFIRMADO"),
        (TipoMovimientoInventario, "TRANSFERENCIA_ENTRADA"),
    ],
)
def test_enums_espanol(enum_cls: type, esperado: str) -> None:
    assert esperado in {m.value for m in enum_cls}


def test_check_constraints_existencias_xor() -> None:
    table = Base.metadata.tables["existencias"]
    nombres = {c.name for c in table.constraints if getattr(c, "name", None)}
    assert "ck_existencias_xor_articulo" in nombres
    assert "ck_existencias_cantidad_ge_0" in nombres


def test_mapper_inspection_ok() -> None:
    """Todos los mapeadores se construyen sin error (relaciones ORM)."""
    insp = inspect(OrdenProduccion)
    assert "pedido" in insp.relationships.keys()
    assert "items" in insp.relationships.keys()
