"""Tabla `materiales`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CANTIDAD, DINERO, col_activo, col_actualizado_en, col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.inventario.categorias_material import CategoriaMaterial
    from app.models.inventario.existencias import Existencia
    from app.models.inventario.items_movimiento_inventario import ItemMovimientoInventario
    from app.models.inventario.unidades_medida import UnidadMedida
    from app.models.compras.items_compra import ItemCompra
    from app.models.produccion.consumos_produccion import ConsumoProduccion
    from app.models.recetas.items_receta_producto import ItemRecetaProducto


class Material(Base):
    __tablename__ = "materiales"
    __table_args__ = (
        CheckConstraint("stock_minimo >= 0", name="ck_materiales_stock_minimo_ge_0"),
        CheckConstraint("costo_promedio >= 0", name="ck_materiales_costo_promedio_ge_0"),
    )

    id: Mapped[int] = col_id()
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categorias_material.id"), nullable=False, index=True
    )
    unidad_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("unidades_medida.id"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock_minimo: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False, default=Decimal("0"))
    costo_promedio: Mapped[Decimal] = mapped_column(DINERO, nullable=False, default=Decimal("0"))
    activo: Mapped[bool] = col_activo()
    creado_en: Mapped[datetime] = col_creado_en()
    actualizado_en: Mapped[datetime] = col_actualizado_en()

    categoria: Mapped[CategoriaMaterial] = relationship(back_populates="materiales")
    unidad: Mapped[UnidadMedida] = relationship(back_populates="materiales")
    existencias: Mapped[list[Existencia]] = relationship(back_populates="material")
    items_movimiento: Mapped[list[ItemMovimientoInventario]] = relationship(
        back_populates="material"
    )
    items_compra: Mapped[list[ItemCompra]] = relationship(back_populates="material")
    items_receta: Mapped[list[ItemRecetaProducto]] = relationship(back_populates="material")
    consumos: Mapped[list[ConsumoProduccion]] = relationship(back_populates="material")
