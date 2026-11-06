"""Tabla `disenos_pedido`."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_APROBACION_DISENO
from app.models.mixins import col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.pedidos.items_pedido import ItemPedido


class DisenoPedido(Base):
    __tablename__ = "disenos_pedido"
    __table_args__ = (
        CheckConstraint(
            f"estado_aprobacion IN ({IN_ESTADO_APROBACION_DISENO})",
            name="ck_disenos_pedido_estado_aprobacion",
        ),
        CheckConstraint("version > 0", name="ck_disenos_pedido_version_gt_0"),
    )

    id: Mapped[int] = col_id()
    item_pedido_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items_pedido.id"), nullable=False, index=True
    )
    ruta_archivo: Mapped[str] = mapped_column(String(1024), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    estado_aprobacion: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = col_creado_en()

    item_pedido: Mapped[ItemPedido] = relationship(back_populates="disenos")
