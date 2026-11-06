"""Tabla `items_movimiento_inventario`."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import XOR_MATERIAL_VARIANTE
from app.models.mixins import CANTIDAD, DINERO, col_id

if TYPE_CHECKING:
    from app.models.inventario.materiales import Material
    from app.models.inventario.movimientos_inventario import MovimientoInventario
    from app.models.productos.variantes_producto import VarianteProducto


class ItemMovimientoInventario(Base):
    __tablename__ = "items_movimiento_inventario"
    __table_args__ = (
        CheckConstraint(
            XOR_MATERIAL_VARIANTE, name="ck_items_movimiento_xor_articulo"
        ),
        CheckConstraint("cantidad > 0", name="ck_items_movimiento_cantidad_gt_0"),
        CheckConstraint("costo_total >= 0", name="ck_items_movimiento_costo_total_ge_0"),
        CheckConstraint("costo_unitario >= 0", name="ck_items_movimiento_costo_unitario_ge_0"),
    )

    id: Mapped[int] = col_id()
    movimiento_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("movimientos_inventario.id"),
        nullable=False,
        index=True,
    )
    material_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("materiales.id"), nullable=True, index=True
    )
    variante_producto_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("variantes_producto.id"), nullable=True, index=True
    )
    cantidad: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False)
    costo_unitario: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    costo_total: Mapped[Decimal] = mapped_column(DINERO, nullable=False)

    movimiento: Mapped[MovimientoInventario] = relationship(back_populates="items")
    material: Mapped[Material | None] = relationship(back_populates="items_movimiento")
    variante_producto: Mapped[VarianteProducto | None] = relationship(
        back_populates="items_movimiento"
    )
