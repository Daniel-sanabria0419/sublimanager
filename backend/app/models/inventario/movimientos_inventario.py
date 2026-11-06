"""Tabla `movimientos_inventario`."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_MOVIMIENTO_INVENTARIO, IN_TIPO_MOVIMIENTO_INVENTARIO
from app.models.mixins import col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.inventario.bodegas import Bodega
    from app.models.inventario.items_movimiento_inventario import ItemMovimientoInventario


class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint(
            f"tipo_movimiento IN ({IN_TIPO_MOVIMIENTO_INVENTARIO})",
            name="ck_movimientos_inventario_tipo",
        ),
        CheckConstraint(
            f"estado IN ({IN_ESTADO_MOVIMIENTO_INVENTARIO})",
            name="ck_movimientos_inventario_estado",
        ),
    )

    id: Mapped[int] = col_id()
    tipo_movimiento: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    grupo_transferencia_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )
    tipo_referencia: Mapped[str | None] = mapped_column(String(64), nullable=True)
    referencia_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    bodega_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bodegas.id"), nullable=False, index=True
    )
    fecha_movimiento: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = col_creado_en()

    bodega: Mapped[Bodega] = relationship(back_populates="movimientos")
    items: Mapped[list[ItemMovimientoInventario]] = relationship(
        back_populates="movimiento",
        cascade="all, delete-orphan",
    )
