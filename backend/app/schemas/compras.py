"""Schemas Pydantic del módulo compras (campos en español)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator, model_validator

from app.schemas.common import OrmModel
from app.utils.decimal_policy import a_decimal, money_round, qty_round


class ProveedorCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=200)
    identificacion: str | None = Field(default=None, max_length=64)
    telefono: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    direccion: str | None = None
    activo: bool = True


class ProveedorUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    identificacion: str | None = Field(default=None, max_length=64)
    telefono: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    direccion: str | None = None
    activo: bool | None = None


class ProveedorOut(OrmModel):
    id: int
    nombre: str
    identificacion: str | None
    telefono: str | None
    email: str | None
    direccion: str | None
    activo: bool


class ItemCompraCreate(OrmModel):
    material_id: int | None = None
    variante_producto_id: int | None = None
    cantidad: Decimal
    costo_unitario: Decimal

    @field_validator("cantidad", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        return qty_round(a_decimal(v))

    @field_validator("costo_unitario", mode="before")
    @classmethod
    def _money(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))

    @model_validator(mode="after")
    def _xor(self) -> ItemCompraCreate:
        if (self.material_id is None) == (self.variante_producto_id is None):
            raise ValueError(
                "Debe indicar exactamente uno de material_id o variante_producto_id"
            )
        return self


class CompraCreate(OrmModel):
    proveedor_id: int
    items: list[ItemCompraCreate] = Field(min_length=1)
    numero_factura: str | None = Field(default=None, max_length=80)
    fecha_compra: datetime | None = None


class RecepcionItemIn(OrmModel):
    item_compra_id: int
    cantidad: Decimal

    @field_validator("cantidad", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        return qty_round(a_decimal(v))


class CompraRecepcionIn(OrmModel):
    bodega_id: int
    items: list[RecepcionItemIn] | None = None
    notas: str | None = None


class ItemCompraOut(OrmModel):
    id: int
    compra_id: int
    material_id: int | None
    variante_producto_id: int | None
    cantidad: Decimal
    costo_unitario: Decimal
    subtotal: Decimal


class CompraOut(OrmModel):
    id: int
    proveedor_id: int
    fecha_compra: datetime
    numero_factura: str | None
    subtotal: Decimal
    total: Decimal
    estado: str
    creado_en: datetime
    items: list[ItemCompraOut] = []
