"""Tabla `items_pedido`."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CANTIDAD, DINERO, col_id

if TYPE_CHECKING:
    from app.models.pedidos.disenos_pedido import DisenoPedido
    from app.models.pedidos.pedidos import Pedido
    from app.models.productos.productos import Producto
    from app.models.productos.variantes_producto import VarianteProducto
    from app.models.produccion.items_orden_produccion import ItemOrdenProduccion


class ItemPedido(Base):
    __tablename__ = "items_pedido"
    __table_args__ = (
        CheckConstraint("cantidad > 0", name="ck_items_pedido_cantidad_gt_0"),
        CheckConstraint(
            "precio_venta_unitario >= 0",
            name="ck_items_pedido_precio_ge_0",
        ),
        CheckConstraint(
            "costo_unitario_estimado >= 0",
            name="ck_items_pedido_costo_est_ge_0",
        ),
        CheckConstraint("subtotal >= 0", name="ck_items_pedido_subtotal_ge_0"),
    )

    id: Mapped[int] = col_id()
    pedido_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("pedidos.id"), nullable=False, index=True
    )
    producto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("productos.id"), nullable=False, index=True
    )
    variante_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("variantes_producto.id"), nullable=True, index=True
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    cantidad: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False)
    precio_venta_unitario: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    costo_unitario_estimado: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(DINERO, nullable=False)

    pedido: Mapped[Pedido] = relationship(back_populates="items")
    producto: Mapped[Producto] = relationship(back_populates="items_pedido")
    variante: Mapped[VarianteProducto | None] = relationship(back_populates="items_pedido")
    disenos: Mapped[list[DisenoPedido]] = relationship(
        back_populates="item_pedido",
        cascade="all, delete-orphan",
    )
    items_orden_produccion: Mapped[list[ItemOrdenProduccion]] = relationship(
        back_populates="item_pedido"
    )
