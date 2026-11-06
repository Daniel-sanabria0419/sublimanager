"""Tabla `pagos_gasto`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_PAGO
from app.models.mixins import DINERO, col_id

if TYPE_CHECKING:
    from app.models.finanzas.cuentas_caja import CuentaCaja
    from app.models.finanzas.gastos import Gasto
    from app.models.finanzas.metodos_pago import MetodoPago
    from app.models.finanzas.movimientos_caja import MovimientoCaja


class PagoGasto(Base):
    __tablename__ = "pagos_gasto"
    __table_args__ = (
        CheckConstraint(f"estado IN ({IN_ESTADO_PAGO})", name="ck_pagos_gasto_estado"),
        CheckConstraint("monto > 0", name="ck_pagos_gasto_monto_gt_0"),
    )

    id: Mapped[int] = col_id()
    gasto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("gastos.id"), nullable=False, index=True
    )
    metodo_pago_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("metodos_pago.id"), nullable=False, index=True
    )
    cuenta_caja_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cuentas_caja.id"), nullable=False, index=True
    )
    monto: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    fecha_pago: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    estado: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    referencia: Mapped[str | None] = mapped_column(String(120), nullable=True)

    gasto: Mapped[Gasto] = relationship(back_populates="pagos")
    metodo_pago: Mapped[MetodoPago] = relationship(back_populates="pagos_gasto")
    cuenta_caja: Mapped[CuentaCaja] = relationship(back_populates="pagos_gasto")
    movimiento_caja: Mapped[MovimientoCaja | None] = relationship(
        back_populates="pago_gasto",
        uselist=False,
    )
