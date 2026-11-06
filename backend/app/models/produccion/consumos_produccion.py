"""Tabla `consumos_produccion`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CANTIDAD, DINERO, col_id

if TYPE_CHECKING:
    from app.models.inventario.materiales import Material
    from app.models.produccion.items_orden_produccion import ItemOrdenProduccion


class ConsumoProduccion(Base):
    __tablename__ = "consumos_produccion"
    __table_args__ = (
        CheckConstraint(
            "cantidad_consumida > 0",
            name="ck_consumos_cantidad_gt_0",
        ),
        CheckConstraint(
            "costo_unitario_snapshot >= 0",
            name="ck_consumos_costo_unitario_ge_0",
        ),
        CheckConstraint("costo_total >= 0", name="ck_consumos_costo_total_ge_0"),
    )

    id: Mapped[int] = col_id()
    item_orden_produccion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("items_orden_produccion.id"),
        nullable=False,
        index=True,
    )
    material_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("materiales.id"), nullable=False, index=True
    )
    cantidad_consumida: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False)
    costo_unitario_snapshot: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    costo_total: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    consumido_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    es_desperdicio: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    item_orden_produccion: Mapped[ItemOrdenProduccion] = relationship(
        back_populates="consumos"
    )
    material: Mapped[Material] = relationship(back_populates="consumos")
