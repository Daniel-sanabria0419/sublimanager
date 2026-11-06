"""Tabla `cuentas_caja`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_TIPO_CUENTA_CAJA
from app.models.mixins import col_activo, col_id

if TYPE_CHECKING:
    from app.models.finanzas.movimientos_caja import MovimientoCaja
    from app.models.finanzas.pagos import Pago
    from app.models.finanzas.pagos_gasto import PagoGasto
    from app.models.finanzas.pagos_proveedor import PagoProveedor


class CuentaCaja(Base):
    __tablename__ = "cuentas_caja"
    __table_args__ = (
        CheckConstraint(
            f"tipo_cuenta IN ({IN_TIPO_CUENTA_CAJA})",
            name="ck_cuentas_caja_tipo",
        ),
    )

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    tipo_cuenta: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    activo: Mapped[bool] = col_activo()

    pagos: Mapped[list[Pago]] = relationship(back_populates="cuenta_caja")
    pagos_gasto: Mapped[list[PagoGasto]] = relationship(back_populates="cuenta_caja")
    pagos_proveedor: Mapped[list[PagoProveedor]] = relationship(
        back_populates="cuenta_caja"
    )
    movimientos: Mapped[list[MovimientoCaja]] = relationship(back_populates="cuenta_caja")
