"""Tabla `gastos`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_PAGO_GASTO
from app.models.mixins import DINERO, col_id

if TYPE_CHECKING:
    from app.models.finanzas.categorias_gasto import CategoriaGasto
    from app.models.finanzas.pagos_gasto import PagoGasto
    from app.models.produccion.asientos_costo_produccion import AsientoCostoProduccion


class Gasto(Base):
    __tablename__ = "gastos"
    __table_args__ = (
        CheckConstraint(
            f"estado_pago IN ({IN_ESTADO_PAGO_GASTO})",
            name="ck_gastos_estado_pago",
        ),
        CheckConstraint("monto > 0", name="ck_gastos_monto_gt_0"),
    )

    id: Mapped[int] = col_id()
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categorias_gasto.id"), nullable=False, index=True
    )
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    monto: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    fecha_gasto: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    estado_pago: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    categoria: Mapped[CategoriaGasto] = relationship(back_populates="gastos")
    pagos: Mapped[list[PagoGasto]] = relationship(back_populates="gasto")
    asientos_costo: Mapped[list[AsientoCostoProduccion]] = relationship(
        back_populates="gasto"
    )
