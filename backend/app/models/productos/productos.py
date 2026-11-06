"""Tabla `productos`."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_TIPO_PRODUCTO
from app.models.mixins import col_activo, col_actualizado_en, col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.pedidos.items_pedido import ItemPedido
    from app.models.productos.categorias_producto import CategoriaProducto
    from app.models.productos.tecnicas_producto import TecnicaProducto
    from app.models.productos.variantes_producto import VarianteProducto
    from app.models.recetas.perfiles_costo_producto import PerfilCostoProducto
    from app.models.recetas.recetas_producto import RecetaProducto


class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = (
        CheckConstraint(
            f"tipo_producto IN ({IN_TIPO_PRODUCTO})",
            name="ck_productos_tipo_producto",
        ),
    )

    id: Mapped[int] = col_id()
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categorias_producto.id"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    tipo_producto: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    activo: Mapped[bool] = col_activo()
    creado_en: Mapped[datetime] = col_creado_en()
    actualizado_en: Mapped[datetime] = col_actualizado_en()

    categoria: Mapped[CategoriaProducto] = relationship(back_populates="productos")
    variantes: Mapped[list[VarianteProducto]] = relationship(back_populates="producto")
    tecnicas: Mapped[list[TecnicaProducto]] = relationship(back_populates="producto")
    recetas: Mapped[list[RecetaProducto]] = relationship(back_populates="producto")
    perfiles_costo: Mapped[list[PerfilCostoProducto]] = relationship(
        back_populates="producto"
    )
    items_pedido: Mapped[list[ItemPedido]] = relationship(back_populates="producto")
