"""Tabla `perfiles_costo_producto`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import DINERO, col_activo, col_id

if TYPE_CHECKING:
    from app.models.productos.productos import Producto
    from app.models.productos.variantes_producto import VarianteProducto


class PerfilCostoProducto(Base):
    __tablename__ = "perfiles_costo_producto"
    __table_args__ = (
        CheckConstraint(
            "costo_mano_obra_por_unidad >= 0",
            name="ck_perfiles_costo_mano_obra_ge_0",
        ),
        CheckConstraint(
            "costo_electricidad_por_unidad >= 0",
            name="ck_perfiles_costo_electricidad_ge_0",
        ),
        CheckConstraint(
            "costo_depreciacion_por_unidad >= 0",
            name="ck_perfiles_costo_depreciacion_ge_0",
        ),
        CheckConstraint(
            "costo_otros_por_unidad >= 0",
            name="ck_perfiles_costo_otros_ge_0",
        ),
    )

    id: Mapped[int] = col_id()
    producto_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("productos.id"), nullable=False, index=True
    )
    variante_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("variantes_producto.id"), nullable=True, index=True
    )
    costo_mano_obra_por_unidad: Mapped[Decimal] = mapped_column(
        DINERO, nullable=False, default=Decimal("0")
    )
    costo_electricidad_por_unidad: Mapped[Decimal] = mapped_column(
        DINERO, nullable=False, default=Decimal("0")
    )
    costo_depreciacion_por_unidad: Mapped[Decimal] = mapped_column(
        DINERO, nullable=False, default=Decimal("0")
    )
    costo_otros_por_unidad: Mapped[Decimal] = mapped_column(
        DINERO, nullable=False, default=Decimal("0")
    )
    vigente_desde: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    activo: Mapped[bool] = col_activo()

    producto: Mapped[Producto] = relationship(back_populates="perfiles_costo")
    variante: Mapped[VarianteProducto | None] = relationship(
        back_populates="perfiles_costo"
    )
