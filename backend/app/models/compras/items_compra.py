"""Tabla `items_compra`."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import XOR_MATERIAL_VARIANTE
from app.models.mixins import CANTIDAD, DINERO, col_id

if TYPE_CHECKING:
    from app.models.compras.compras import Compra
    from app.models.inventario.materiales import Material
    from app.models.productos.variantes_producto import VarianteProducto


class ItemCompra(Base):
    __tablename__ = "items_compra"
    __table_args__ = (
        CheckConstraint(XOR_MATERIAL_VARIANTE, name="ck_items_compra_xor_articulo"),
        CheckConstraint("cantidad > 0", name="ck_items_compra_cantidad_gt_0"),
        CheckConstraint("costo_unitario >= 0", name="ck_items_compra_costo_ge_0"),
        CheckConstraint("subtotal >= 0", name="ck_items_compra_subtotal_ge_0"),
    )

    id: Mapped[int] = col_id()
    compra_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("compras.id"), nullable=False, index=True
    )
    material_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("materiales.id"), nullable=True, index=True
    )
    variante_producto_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("variantes_producto.id"), nullable=True, index=True
    )
    cantidad: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False)
    costo_unitario: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(DINERO, nullable=False)

    compra: Mapped[Compra] = relationship(back_populates="items")
    material: Mapped[Material | None] = relationship(back_populates="items_compra")
    variante_producto: Mapped[VarianteProducto | None] = relationship(
        back_populates="items_compra"
    )
