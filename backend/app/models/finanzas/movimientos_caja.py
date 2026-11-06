"""Tabla `movimientos_caja`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_TIPO_MOVIMIENTO_CAJA, XOR_ORIGEN_MOVIMIENTO_CAJA
from app.models.mixins import DINERO, col_id

if TYPE_CHECKING:
    from app.models.finanzas.cuentas_caja import CuentaCaja
    from app.models.finanzas.pagos import Pago
    from app.models.finanzas.pagos_gasto import PagoGasto
    from app.models.finanzas.pagos_proveedor import PagoProveedor


class MovimientoCaja(Base):
    __tablename__ = "movimientos_caja"
    __table_args__ = (
        CheckConstraint(
            f"tipo_movimiento IN ({IN_TIPO_MOVIMIENTO_CAJA})",
            name="ck_movimientos_caja_tipo",
        ),
        CheckConstraint(
            XOR_ORIGEN_MOVIMIENTO_CAJA,
            name="ck_movimientos_caja_un_origen",
        ),
        CheckConstraint("monto > 0", name="ck_movimientos_caja_monto_gt_0"),
        # Anti-duplicados: un pago genera a lo sumo un movimiento
        Index(
            "uq_movimientos_caja_pago_id",
            "pago_id",
            unique=True,
            postgresql_where="pago_id IS NOT NULL",
        ),
        Index(
            "uq_movimientos_caja_pago_proveedor_id",
            "pago_proveedor_id",
            unique=True,
            postgresql_where="pago_proveedor_id IS NOT NULL",
        ),
        Index(
            "uq_movimientos_caja_pago_gasto_id",
            "pago_gasto_id",
            unique=True,
            postgresql_where="pago_gasto_id IS NOT NULL",
        ),
    )

    id: Mapped[int] = col_id()
    cuenta_caja_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cuentas_caja.id"), nullable=False, index=True
    )
    tipo_movimiento: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    monto: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    pago_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pagos.id"), nullable=True
    )
    pago_proveedor_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pagos_proveedor.id"), nullable=True
    )
    pago_gasto_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("pagos_gasto.id"), nullable=True
    )
    fecha_movimiento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)

    cuenta_caja: Mapped[CuentaCaja] = relationship(back_populates="movimientos")
    pago: Mapped[Pago | None] = relationship(back_populates="movimiento_caja")
    pago_proveedor: Mapped[PagoProveedor | None] = relationship(
        back_populates="movimiento_caja"
    )
    pago_gasto: Mapped[PagoGasto | None] = relationship(back_populates="movimiento_caja")
