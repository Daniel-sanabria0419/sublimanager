"""Schemas Pydantic del módulo clientes y pedidos (campos en español)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import EstadoAprobacionDiseno, EstadoPedido
from app.schemas.common import OrmModel
from app.utils.decimal_policy import a_decimal, money_round, qty_round


class ClienteCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=200)
    identificacion: str | None = Field(default=None, max_length=64)
    telefono: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    direccion: str | None = None
    notas: str | None = None
    activo: bool = True


class ClienteUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=200)
    identificacion: str | None = Field(default=None, max_length=64)
    telefono: str | None = Field(default=None, max_length=40)
    email: str | None = Field(default=None, max_length=120)
    direccion: str | None = None
    notas: str | None = None
    activo: bool | None = None


class ClienteOut(OrmModel):
    id: int
    nombre: str
    identificacion: str | None
    telefono: str | None
    email: str | None
    direccion: str | None
    notas: str | None
    activo: bool
    creado_en: datetime


class ItemPedidoCreate(OrmModel):
    producto_id: int
    variante_id: int | None = None
    descripcion: str | None = None
    cantidad: Decimal
    precio_venta_unitario: Decimal | None = None

    @field_validator("cantidad", mode="before")
    @classmethod
    def _qty(cls, v):  # noqa: ANN001
        return qty_round(a_decimal(v))

    @field_validator("precio_venta_unitario", mode="before")
    @classmethod
    def _precio(cls, v):  # noqa: ANN001
        if v is None:
            return v
        return money_round(a_decimal(v))


class ItemPedidoOut(OrmModel):
    id: int
    pedido_id: int
    producto_id: int
    variante_id: int | None
    descripcion: str | None
    cantidad: Decimal
    precio_venta_unitario: Decimal
    costo_unitario_estimado: Decimal
    subtotal: Decimal


class PedidoCreate(OrmModel):
    cliente_id: int
    items: list[ItemPedidoCreate] = Field(min_length=1)
    numero_pedido: str | None = Field(default=None, min_length=1, max_length=40)
    fecha_pedido: datetime | None = None
    fecha_entrega: datetime | None = None
    descuento: Decimal = Decimal("0")
    notas: str | None = None

    @field_validator("descuento", mode="before")
    @classmethod
    def _descuento(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))


class PedidoUpdate(OrmModel):
    fecha_entrega: datetime | None = None
    descuento: Decimal | None = None
    notas: str | None = None

    @field_validator("descuento", mode="before")
    @classmethod
    def _descuento(cls, v):  # noqa: ANN001
        if v is None:
            return v
        return money_round(a_decimal(v))


class PedidoOut(OrmModel):
    id: int
    numero_pedido: str
    cliente_id: int
    fecha_pedido: datetime
    fecha_entrega: datetime | None
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    estado: str
    notas: str | None
    creado_en: datetime
    actualizado_en: datetime
    items: list[ItemPedidoOut] = Field(default_factory=list)
    total_pagado: Decimal = Decimal("0.00")
    saldo_pendiente: Decimal = Decimal("0.00")


class PedidoEstadoIn(OrmModel):
    estado_nuevo: EstadoPedido
    notas: str | None = None
    bodega_id: int | None = Field(
        default=None,
        description=(
            "Requerido al pasar a ENTREGADO si hay ítems REVENTA con control_stock"
        ),
    )


class HistorialEstadoPedidoOut(OrmModel):
    id: int
    pedido_id: int
    estado_anterior: str | None
    estado_nuevo: str
    cambiado_en: datetime
    notas: str | None


class DisenoPedidoCreate(OrmModel):
    item_pedido_id: int
    ruta_archivo: str = Field(min_length=1, max_length=1024)
    estado_aprobacion: EstadoAprobacionDiseno = EstadoAprobacionDiseno.BORRADOR
    notas: str | None = None
    version: int | None = Field(default=None, ge=1)


class DisenoPedidoUpdate(OrmModel):
    ruta_archivo: str | None = Field(default=None, min_length=1, max_length=1024)
    estado_aprobacion: EstadoAprobacionDiseno | None = None
    notas: str | None = None


class DisenoPedidoOut(OrmModel):
    id: int
    item_pedido_id: int
    ruta_archivo: str
    version: int
    estado_aprobacion: str
    notas: str | None
    creado_en: datetime
