"""Tabla `tecnicas_producto` (N:N producto × técnica)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_id

if TYPE_CHECKING:
    from app.models.productos.productos import Producto
    from app.models.productos.tecnicas_produccion import TecnicaProduccion


class TecnicaProducto(Base):
    __tablename__ = "tecnicas_producto"
    __table_args__ = (
        UniqueConstraint("producto_id", "tecnica_id", name="uq_tecnicas_producto_par"),
    )

    id: Mapped[int] = col_id()
    producto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("productos.id"), nullable=False, index=True
    )
    tecnica_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("tecnicas_produccion.id"), nullable=False, index=True
    )

    producto: Mapped[Producto] = relationship(back_populates="tecnicas")
    tecnica: Mapped[TecnicaProduccion] = relationship(back_populates="productos")
