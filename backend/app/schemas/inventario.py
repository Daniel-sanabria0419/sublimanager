"""Schemas Pydantic del módulo inventario (campos en español)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.common import OrmModel
from app.utils.decimal_policy import a_decimal, money_round, qty_round


class CategoriaMaterialCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None
    activo: bool = True


class CategoriaMaterialUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = None
    activo: bool | None = None


class CategoriaMaterialOut(OrmModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool
    creado_en: datetime


class UnidadMedidaCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=60)
    abreviatura: str = Field(min_length=1, max_length=16)
    activo: bool = True


class UnidadMedidaUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=60)
    abreviatura: str | None = Field(default=None, min_length=1, max_length=16)
    activo: bool | None = None


class UnidadMedidaOut(OrmModel):
    id: int
    nombre: str
    abreviatura: str
    activo: bool


class BodegaCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=120)
    ubicacion: str | None = Field(default=None, max_length=255)
    activo: bool = True


class BodegaUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    ubicacion: str | None = Field(default=None, max_length=255)
    activo: bool | None = None


class BodegaOut(OrmModel):
    id: int
    nombre: str
    ubicacion: str | None
    activo: bool


class MaterialCreate(OrmModel):
    categoria_id: int
    unidad_id: int
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: str | None = None
    stock_minimo: Decimal = Decimal("0")
    activo: bool = True
    stock_inicial: Decimal | None = None
    bodega_id: int | None = None
    costo_unitario_inicial: Decimal | None = None

    @field_validator("stock_minimo", "stock_inicial", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        if v is None:
            return v
        return qty_round(a_decimal(v))

    @field_validator("costo_unitario_inicial", mode="before")
    @classmethod
    def _money(cls, v):  # noqa: ANN001
        if v is None:
            return v
        return money_round(a_decimal(v))


class MaterialUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = None
    stock_minimo: Decimal | None = None
    activo: bool | None = None
    categoria_id: int | None = None
    unidad_id: int | None = None

    @field_validator("stock_minimo", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        if v is None:
            return v
        return qty_round(a_decimal(v))


class MaterialOut(OrmModel):
    id: int
    categoria_id: int
    unidad_id: int
    nombre: str
    descripcion: str | None
    stock_minimo: Decimal
    costo_promedio: Decimal
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


class ExistenciaOut(OrmModel):
    id: int
    bodega_id: int
    material_id: int | None
    variante_producto_id: int | None
    cantidad: Decimal
    actualizado_en: datetime


class ItemMovimientoCreate(OrmModel):
    material_id: int | None = None
    variante_producto_id: int | None = None
    cantidad: Decimal
    costo_unitario: Decimal = Decimal("0")

    @field_validator("cantidad", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        return qty_round(a_decimal(v))

    @field_validator("costo_unitario", mode="before")
    @classmethod
    def _money(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))

    @model_validator(mode="after")
    def _xor(self) -> ItemMovimientoCreate:
        if (self.material_id is None) == (self.variante_producto_id is None):
            raise ValueError(
                "Debe indicar exactamente uno de material_id o variante_producto_id"
            )
        return self


class MovimientoInventarioCreate(OrmModel):
    tipo_movimiento: str
    bodega_id: int
    items: list[ItemMovimientoCreate] = Field(min_length=1)
    notas: str | None = None
    tipo_referencia: str | None = None
    referencia_id: int | None = None
    confirmar: bool = True


class TransferenciaCreate(OrmModel):
    bodega_origen_id: int
    bodega_destino_id: int
    items: list[ItemMovimientoCreate] = Field(min_length=1)
    notas: str | None = None


class ItemMovimientoOut(OrmModel):
    id: int
    movimiento_id: int
    material_id: int | None
    variante_producto_id: int | None
    cantidad: Decimal
    costo_unitario: Decimal
    costo_total: Decimal


class MovimientoInventarioOut(OrmModel):
    id: int
    tipo_movimiento: str
    estado: str
    grupo_transferencia_id: UUID | None
    tipo_referencia: str | None
    referencia_id: int | None
    bodega_id: int
    fecha_movimiento: datetime
    notas: str | None
    creado_en: datetime
    items: list[ItemMovimientoOut] = []


class AlertaStockBajoOut(OrmModel):
    material_id: int
    nombre: str
    stock_minimo: Decimal
    stock_actual: Decimal
    faltante: Decimal


class TransferenciaOut(OrmModel):
    grupo_transferencia_id: UUID
    salida: MovimientoInventarioOut
    entrada: MovimientoInventarioOut
