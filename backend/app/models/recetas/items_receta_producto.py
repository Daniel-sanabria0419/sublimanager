"""Tabla `items_receta_producto`."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CANTIDAD, PORCENTAJE, col_id

if TYPE_CHECKING:
    from app.models.inventario.materiales import Material
    from app.models.recetas.recetas_producto import RecetaProducto


class ItemRecetaProducto(Base):
    __tablename__ = "items_receta_producto"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_items_receta_cantidad_gt_0"),
        CheckConstraint(
            "porcentaje_desperdicio >= 0",
            name="ck_items_receta_desperdicio_ge_0",
        ),
    )

    id: Mapped[int] = col_id()
    receta_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("recetas_producto.id"), nullable=False, index=True
    )
    material_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("materiales.id"), nullable=False, index=True
    )
    cantidad: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False)
    porcentaje_desperdicio: Mapped[Decimal] = mapped_column(
        PORCENTAJE, nullable=False, default=Decimal("0")
    )
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)

    receta: Mapped[RecetaProducto] = relationship(back_populates="items")
    material: Mapped[Material] = relationship(back_populates="items_receta")
