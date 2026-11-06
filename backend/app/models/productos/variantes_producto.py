"""Tabla `variantes_producto`."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import DINERO, col_activo, col_id

if TYPE_CHECKING:
    from app.models.compras.items_compra import ItemCompra
    from app.models.inventario.existencias import Existencia
    from app.models.inventario.items_movimiento_inventario import ItemMovimientoInventario
    from app.models.pedidos.items_pedido import ItemPedido
    from app.models.productos.productos import Producto
    from app.models.recetas.perfiles_costo_producto import PerfilCostoProducto
    from app.models.recetas.recetas_producto import RecetaProducto


class VarianteProducto(Base):
    __tablename__ = "variantes_producto"
    __table_args__ = (
        CheckConstraint("precio_venta >= 0", name="ck_variantes_precio_venta_ge_0"),
    )

    id: Mapped[int] = col_id()
    producto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("productos.id"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    talla: Mapped[str | None] = mapped_column(String(64), nullable=True)
    color: Mapped[str | None] = mapped_column(String(64), nullable=True)
    precio_venta: Mapped[Decimal] = mapped_column(DINERO, nullable=False, default=Decimal("0"))
    control_stock: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    activo: Mapped[bool] = col_activo()

    producto: Mapped[Producto] = relationship(back_populates="variantes")
    existencias: Mapped[list[Existencia]] = relationship(back_populates="variante_producto")
    items_movimiento: Mapped[list[ItemMovimientoInventario]] = relationship(
        back_populates="variante_producto"
    )
    items_compra: Mapped[list[ItemCompra]] = relationship(back_populates="variante_producto")
    recetas: Mapped[list[RecetaProducto]] = relationship(back_populates="variante")
    perfiles_costo: Mapped[list[PerfilCostoProducto]] = relationship(
        back_populates="variante"
    )
    items_pedido: Mapped[list[ItemPedido]] = relationship(back_populates="variante")
