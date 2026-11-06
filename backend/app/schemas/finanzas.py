"""Schemas Pydantic del módulo Finanzas (Stage 5 + Stage 7)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import Field, field_validator

from app.models.enums import EstadoPago, EstadoPagoGasto, TipoCuentaCaja, TipoMovimientoCaja
from app.schemas.common import OrmModel
from app.utils.decimal_policy import a_decimal, money_round


# ---------------------------------------------------------------------------
# Métodos de pago / cuentas de caja
# ---------------------------------------------------------------------------


class MetodoPagoCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=80)
    activo: bool = True


class MetodoPagoUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=80)
    activo: bool | None = None


class MetodoPagoOut(OrmModel):
    id: int
    nombre: str
    activo: bool


class CuentaCajaCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=120)
    tipo_cuenta: TipoCuentaCaja
    activo: bool = True


class CuentaCajaUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    tipo_cuenta: TipoCuentaCaja | None = None
    activo: bool | None = None


class CuentaCajaOut(OrmModel):
    id: int
    nombre: str
    tipo_cuenta: str
    activo: bool


class CuentaCajaSaldoOut(OrmModel):
    cuenta_caja_id: int
    nombre: str
    tipo_cuenta: str
    saldo: Decimal


# ---------------------------------------------------------------------------
# Pagos de clientes
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Categorías de gasto / gastos / pagos de gasto
# ---------------------------------------------------------------------------


class CategoriaGastoCreate(OrmModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None
    activo: bool = True


class CategoriaGastoUpdate(OrmModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=120)
    descripcion: str | None = None
    activo: bool | None = None


class CategoriaGastoOut(OrmModel):
    id: int
    nombre: str
    descripcion: str | None
    activo: bool


class GastoCreate(OrmModel):
    categoria_id: int
    descripcion: str = Field(min_length=1)
    monto: Decimal
    fecha_gasto: datetime | None = None
    notas: str | None = None

    @field_validator("monto", mode="before")
    @classmethod
    def _monto(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))


class GastoUpdate(OrmModel):
    categoria_id: int | None = None
    descripcion: str | None = Field(default=None, min_length=1)
    notas: str | None = None


class GastoOut(OrmModel):
    id: int
    categoria_id: int
    descripcion: str
    monto: Decimal
    fecha_gasto: datetime
    estado_pago: str
    notas: str | None
    total_pagado: Decimal | None = None
    saldo_pendiente: Decimal | None = None


class PagoGastoCreate(OrmModel):
    gasto_id: int
    metodo_pago_id: int
    cuenta_caja_id: int
    monto: Decimal
    referencia: str | None = Field(default=None, max_length=120)
    confirmar: bool = True
    fecha_pago: datetime | None = None

    @field_validator("monto", mode="before")
    @classmethod
    def _monto(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))


class PagoGastoOut(OrmModel):
    id: int
    gasto_id: int
    metodo_pago_id: int
    cuenta_caja_id: int
    monto: Decimal
    fecha_pago: datetime
    estado: str
    referencia: str | None


# ---------------------------------------------------------------------------
# Pagos a proveedores
# ---------------------------------------------------------------------------


class PagoProveedorCreate(OrmModel):
    compra_id: int
    metodo_pago_id: int
    cuenta_caja_id: int
    monto: Decimal
    referencia: str | None = Field(default=None, max_length=120)
    confirmar: bool = True
    fecha_pago: datetime | None = None

    @field_validator("monto", mode="before")
    @classmethod
    def _monto(cls, v):  # noqa: ANN001
        return money_round(a_decimal(v))


class PagoProveedorOut(OrmModel):
    id: int
    compra_id: int
    metodo_pago_id: int
    cuenta_caja_id: int
    monto: Decimal
    fecha_pago: datetime
    estado: str
    referencia: str | None


class SaldoCompraOut(OrmModel):
    compra_id: int
    total: Decimal
    total_pagado: Decimal
    saldo_pendiente: Decimal


# ---------------------------------------------------------------------------
# Movimientos de caja
# ---------------------------------------------------------------------------


class MovimientoCajaOut(OrmModel):
    id: int
    cuenta_caja_id: int
    tipo_movimiento: str
    monto: Decimal
    pago_id: int | None
    pago_proveedor_id: int | None
    pago_gasto_id: int | None
    fecha_movimiento: datetime
    descripcion: str | None


# ---------------------------------------------------------------------------
# CxC / CxP / resumen financiero
# ---------------------------------------------------------------------------


class CuentaPorCobrarOut(OrmModel):
    pedido_id: int
    numero_pedido: str
    cliente_id: int
    estado: str
    total: Decimal
    total_pagado: Decimal
    saldo_pendiente: Decimal


class CuentaPorPagarOut(OrmModel):
    compra_id: int
    proveedor_id: int
    numero_factura: str | None
    estado: str
    total: Decimal
    total_pagado: Decimal
    saldo_pendiente: Decimal


class ResumenFinancieroOut(OrmModel):
    """Resumen §5.10 — distingue ventas, caja, costos y gastos."""

    ventas_reconocidas: Decimal
    dinero_recibido: Decimal
    cuentas_por_cobrar: Decimal
    costos_produccion: Decimal
    gastos_operativos: Decimal
    compras_inventario_pagadas: Decimal
    utilidad_bruta: Decimal
    utilidad_operativa: Decimal
    entradas_caja: Decimal
    salidas_caja: Decimal
    saldo_caja_neto: Decimal
    cuentas_por_pagar: Decimal
    notas: str
