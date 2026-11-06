"""Schemas mínimos de finanzas para anticipos de pedidos (Stage 5)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import EstadoPago, TipoCuentaCaja
from app.schemas.common import OrmModel
from app.utils.decimal_policy import a_decimal, money_round


class MetodoPagoCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=80)
    activo: bool = True


class MetodoPagoOut(OrmModel):
    id: int
    nombre: str
    activo: bool


class CuentaCajaCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=120)
    tipo_cuenta: TipoCuentaCaja
    activo: bool = True


class CuentaCajaOut(OrmModel):
    id: int
    nombre: str
    tipo_cuenta: str
    activo: bool


class PagoCreate(OrmModel):
    pedido_id: int
    metodo_pago_id: int
    cuenta_caja_id: int
    monto: Decimal
    referencia: str | None = Field(default=None, max_length=120)
    notas: str | None = None
    confirmar: bool = True
    fecha_pago: datetime | None = None

    @field_validator("monto", mode="before")
    @classmethod
    def _monto(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))


class PagoOut(OrmModel):
    id: int
    pedido_id: int
    metodo_pago_id: int
    cuenta_caja_id: int
    monto: Decimal
    fecha_pago: datetime
    referencia: str | None
    estado: str
    notas: str | None


class PagoEstadoIn(OrmModel):
    estado: EstadoPago
    notas: str | None = None
