"""Tabla `historial_estado_pedido`."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_PEDIDO
from app.models.mixins import col_id

if TYPE_CHECKING:
    from app.models.pedidos.pedidos import Pedido


class HistorialEstadoPedido(Base):
    __tablename__ = "historial_estado_pedido"
    __table_args__ = (
        CheckConstraint(
            f"estado_nuevo IN ({IN_ESTADO_PEDIDO})",
            name="ck_historial_estado_nuevo",
        ),
        CheckConstraint(
            f"estado_anterior IS NULL OR estado_anterior IN ({IN_ESTADO_PEDIDO})",
            name="ck_historial_estado_anterior",
        ),
    )

    id: Mapped[int] = col_id()
    pedido_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pedidos.id"), nullable=False, index=True
    )
    estado_anterior: Mapped[str | None] = mapped_column(String(32), nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(String(32), nullable=False)
    cambiado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    pedido: Mapped[Pedido] = relationship(back_populates="historial_estados")
