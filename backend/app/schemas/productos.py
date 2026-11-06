"""Schemas Pydantic del módulo productos (campos en español)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import TipoProducto
from app.schemas.common import OrmModel
from app.utils.decimal_policy import a_decimal, money_round


class CategoriaProductoCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None
    activo: bool = True


class CategoriaProductoUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = None
    activo: bool | None = None


class CategoriaProductoOut(OrmModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool


class ProductoCreate(OrmModel):
    categoria_id: int
    nombre: str = Field(min_length=1, max_length=200)
    descripcion: str | None = None
    tipo_producto: TipoProducto
    activo: bool = True


class ProductoUpdate(OrmModel):
    categoria_id: int | None = None
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    descripcion: str | None = None
    tipo_producto: TipoProducto | None = None
    activo: bool | None = None


class ProductoOut(OrmModel):
    id: int
    categoria_id: int
    nombre: str
    descripcion: str | None
    tipo_producto: str
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


class VarianteProductoCreate(OrmModel):
    producto_id: int
    sku: str = Field(min_length=1, max_length=64)
    talla: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=64)
    precio_venta: Decimal = Decimal("0")
    control_stock: bool = True
    activo: bool = True

    @field_validator("precio_venta", mode="before")
    @classmethod
    def _money(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))


class VarianteProductoUpdate(OrmModel):
    sku: str | None = Field(default=None, min_length=1, max_length=64)
    talla: str | None = Field(default=None, max_length=64)
    color: str | None = Field(default=None, max_length=64)
    precio_venta: Decimal | None = None
    control_stock: bool | None = None
    activo: bool | None = None

    @field_validator("precio_venta", mode="before")
    @classmethod
    def _money(cls, v):  # noqa: ANN001
        if v is None:
            return v
        return money_round(a_decimal(v))


class VarianteProductoOut(OrmModel):
    id: int
    producto_id: int
    sku: str
    talla: str | None
    color: str | None
    precio_venta: Decimal
    control_stock: bool
    activo: bool


class TecnicaProduccionCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None
    activo: bool = True


class TecnicaProduccionUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = None
    activo: bool | None = None


class TecnicaProduccionOut(OrmModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool


class TecnicaProductoCreate(OrmModel):
    producto_id: int
    tecnica_id: int


class TecnicaProductoOut(OrmModel):
    id: int
    producto_id: int
    tecnica_id: int
