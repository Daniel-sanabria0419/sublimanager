"""Tabla `pagos` (cobros de pedidos)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_PAGO
from app.models.mixins import DINERO, col_id

if TYPE_CHECKING:
    from app.models.finanzas.cuentas_caja import CuentaCaja
    from app.models.finanzas.metodos_pago import MetodoPago
    from app.models.finanzas.movimientos_caja import MovimientoCaja
    from app.models.pedidos.pedidos import Pedido


class Pago(Base):
    __tablename__ = "pagos"
    __table_args__ = (
        CheckConstraint(f"estado IN ({IN_ESTADO_PAGO})", name="ck_pagos_estado"),
        CheckConstraint("monto > 0", name="ck_pagos_monto_gt_0"),
    )

    id: Mapped[int] = col_id()
    pedido_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pedidos.id"), nullable=False, index=True
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
    referencia: Mapped[str | None] = mapped_column(String(120), nullable=True)
    estado: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    pedido: Mapped[Pedido] = relationship(back_populates="pagos")
    metodo_pago: Mapped[MetodoPago] = relationship(back_populates="pagos")
    cuenta_caja: Mapped[CuentaCaja] = relationship(back_populates="pagos")
    movimiento_caja: Mapped[MovimientoCaja | None] = relationship(
        back_populates="pago",
        uselist=False,
    )
