"""Tabla `recetas_producto`."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_activo, col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.productos.productos import Producto
    from app.models.productos.variantes_producto import VarianteProducto
    from app.models.recetas.items_receta_producto import ItemRecetaProducto


class RecetaProducto(Base):
    __tablename__ = "recetas_producto"
    __table_args__ = (
        # UNIQUE(producto_id, variante_id, version) con NULL variante → índices parciales
        Index(
            "uq_recetas_producto_con_variante",
            "producto_id",
            "variante_id",
            "version",
            unique=True,
            postgresql_where="variante_id IS NOT NULL",
        ),
        Index(
            "uq_recetas_producto_sin_variante",
            "producto_id",
            "version",
            unique=True,
            postgresql_where="variante_id IS NULL",
        ),
    )

    id: Mapped[int] = col_id()
    producto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("productos.id"), nullable=False, index=True
    )
    variante_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("variantes_producto.id"), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    activo: Mapped[bool] = col_activo()
    creado_en: Mapped[datetime] = col_creado_en()

    producto: Mapped[Producto] = relationship(back_populates="recetas")
    variante: Mapped[VarianteProducto | None] = relationship(back_populates="recetas")
    items: Mapped[list[ItemRecetaProducto]] = relationship(
        back_populates="receta",
        cascade="all, delete-orphan",
    )
