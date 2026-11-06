"""Tabla `ordenes_produccion`.

V1: `pedido_id` es NOT NULL (OP interna sin pedido diferida a fase posterior).
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_ORDEN_PRODUCCION
from app.models.mixins import col_id

if TYPE_CHECKING:
    from app.models.pedidos.pedidos import Pedido
    from app.models.produccion.items_orden_produccion import ItemOrdenProduccion


class OrdenProduccion(Base):
    __tablename__ = "ordenes_produccion"
    __table_args__ = (
        CheckConstraint(
            f"estado IN ({IN_ESTADO_ORDEN_PRODUCCION})",
            name="ck_ordenes_produccion_estado",
        ),
    )

    id: Mapped[int] = col_id()
    # APROBADO V1: NOT NULL — toda OP exige pedido de cliente
    pedido_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pedidos.id"), nullable=False, index=True
    )
    numero_produccion: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    estado: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    fecha_inicio: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    fecha_fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    pedido: Mapped[Pedido] = relationship(back_populates="ordenes_produccion")
    items: Mapped[list[ItemOrdenProduccion]] = relationship(
        back_populates="orden_produccion",
        cascade="all, delete-orphan",
    )
