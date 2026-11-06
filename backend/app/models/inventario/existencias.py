"""Tabla `existencias` (stock por bodega + material XOR variante)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import XOR_MATERIAL_VARIANTE
from app.models.mixins import CANTIDAD, col_id

if TYPE_CHECKING:
    from app.models.inventario.bodegas import Bodega
    from app.models.inventario.materiales import Material
    from app.models.productos.variantes_producto import VarianteProducto


class Existencia(Base):
    __tablename__ = "existencias"
    __table_args__ = (
        CheckConstraint(XOR_MATERIAL_VARIANTE, name="ck_existencias_xor_articulo"),
        CheckConstraint("cantidad >= 0", name="ck_existencias_cantidad_ge_0"),
        Index(
            "uq_existencias_bodega_material",
            "bodega_id",
            "material_id",
            unique=True,
            postgresql_where="material_id IS NOT NULL",
        ),
        Index(
            "uq_existencias_bodega_variante",
            "bodega_id",
            "variante_producto_id",
            unique=True,
            postgresql_where="variante_producto_id IS NOT NULL",
        ),
    )

    id: Mapped[int] = col_id()
    bodega_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("bodegas.id"), nullable=False, index=True
    )
    material_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("materiales.id"), nullable=True, index=True
    )
    variante_producto_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("variantes_producto.id"), nullable=True, index=True
    )
    cantidad: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False, default=Decimal("0"))
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    bodega: Mapped[Bodega] = relationship(back_populates="existencias")
    material: Mapped[Material | None] = relationship(back_populates="existencias")
    variante_producto: Mapped[VarianteProducto | None] = relationship(
        back_populates="existencias"
    )
