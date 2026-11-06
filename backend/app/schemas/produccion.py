"""Schemas Pydantic del módulo órdenes de producción (campos en español)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import EstadoOrdenProduccion, EtapaCosto
from app.schemas.common import OrmModel
from app.utils.decimal_policy import a_decimal, money_round, qty_round


class ItemOrdenProduccionCreate(OrmModel):
    item_pedido_id: int
    cantidad_planificada: Decimal | None = None

    @field_validator("cantidad_planificada", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        if v is None:
            return v
        return qty_round(a_decimal(v))


class OrdenProduccionCreate(OrmModel):
    pedido_id: int
    items: list[ItemOrdenProduccionCreate] = Field(min_length=1)
    numero_produccion: str | None = Field(default=None, min_length=1, max_length=40)
    notas: str | None = None
    bodega_id: int | None = None


class ConsumoProduccionCreate(OrmModel):
    material_id: int
    cantidad_consumida: Decimal
    es_desperdicio: bool = False
    notas: str | None = None
    costo_unitario_snapshot: Decimal | None = None

    @field_validator("cantidad_consumida", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        return qty_round(a_decimal(v))

    @field_validator("costo_unitario_snapshot", mode="before")
    @classmethod
    def _costo(cls, v):  # noqa: ANN001
        if v is None:
            return v
        return money_round(a_decimal(v))


class AsientoCostoCreate(OrmModel):
    categoria_costo_id: int
    cantidad: Decimal = Decimal("1")
    costo_unitario: Decimal
    descripcion: str | None = None
    gasto_id: int | None = None
    etapa_costo: EtapaCosto = EtapaCosto.REAL

    @field_validator("cantidad", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        return qty_round(a_decimal(v))

    @field_validator("costo_unitario", mode="before")
    @classmethod
    def _costo(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))


class CantidadesProduccionIn(OrmModel):
    cantidad_producida: Decimal
    cantidad_rechazada: Decimal = Decimal("0")
    bodega_producto_id: int | None = None

    @field_validator("cantidad_producida", "cantidad_rechazada", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        return qty_round(a_decimal(v))


class CompletarOrdenIn(OrmModel):
    bodega_producto_id: int | None = None


class ConsumoProduccionOut(OrmModel):
    id: int
    item_orden_produccion_id: int
    material_id: int
    cantidad_consumida: Decimal
    costo_unitario_snapshot: Decimal
    costo_total: Decimal
    consumido_en: datetime
    es_desperdicio: bool
    notas: str | None


class AsientoCostoProduccionOut(OrmModel):
    id: int
    item_orden_produccion_id: int
    categoria_costo_id: int
    gasto_id: int | None
    descripcion: str | None
    etapa_costo: str
    cantidad: Decimal
    costo_unitario: Decimal
    costo_total: Decimal
    creado_en: datetime


class ItemOrdenProduccionOut(OrmModel):
    id: int
    orden_produccion_id: int
    item_pedido_id: int
    cantidad_planificada: Decimal
    cantidad_producida: Decimal
    cantidad_rechazada: Decimal
    consumos: list[ConsumoProduccionOut] = Field(default_factory=list)
    asientos_costo: list[AsientoCostoProduccionOut] = Field(default_factory=list)


class OrdenProduccionOut(OrmModel):
    id: int
    pedido_id: int
    numero_produccion: str
    estado: str
    fecha_inicio: datetime | None
    fecha_fin: datetime | None
    notas: str | None
    items: list[ItemOrdenProduccionOut] = Field(default_factory=list)


class MaterialRequeridoOut(OrmModel):
    material_id: int
    nombre_material: str
    cantidad_requerida: Decimal
    cantidad_disponible: Decimal
    costo_promedio: Decimal
    costo_estimado: Decimal
    suficiente: bool
    receta_id: int
    item_orden_produccion_id: int
    item_pedido_id: int


class MaterialesRequeridosOut(OrmModel):
    orden_produccion_id: int
    bodega_id: int
    materiales: list[MaterialRequeridoOut]
    todos_suficientes: bool


class ComparacionCostoItemOut(OrmModel):
    item_orden_produccion_id: int
    item_pedido_id: int
    costo_estimado_total: Decimal
    costo_real_total: Decimal
    diferencia: Decimal
    estimado_por_tipo: dict[str, Decimal]
    real_por_tipo: dict[str, Decimal]
    costo_materiales_consumos: Decimal


class ComparacionCostoOrdenOut(OrmModel):
    orden_produccion_id: int
    items: list[ComparacionCostoItemOut]
    costo_estimado_total: Decimal
    costo_real_total: Decimal
    diferencia: Decimal


class EstadoOrdenIn(OrmModel):
    estado: EstadoOrdenProduccion | None = None
