"""Tabla `asientos_costo_produccion`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ETAPA_COSTO
from app.models.mixins import CANTIDAD, DINERO, col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.finanzas.gastos import Gasto
    from app.models.produccion.items_orden_produccion import ItemOrdenProduccion
    from app.models.recetas.categorias_costo import CategoriaCosto


class AsientoCostoProduccion(Base):
    __tablename__ = "asientos_costo_produccion"
    __table_args__ = (
        CheckConstraint(
            f"etapa_costo IN ({IN_ETAPA_COSTO})",
            name="ck_asientos_costo_etapa",
        ),
        CheckConstraint("cantidad >= 0", name="ck_asientos_costo_cantidad_ge_0"),
        CheckConstraint(
            "costo_unitario >= 0",
            name="ck_asientos_costo_unitario_ge_0",
        ),
        CheckConstraint("costo_total >= 0", name="ck_asientos_costo_total_ge_0"),
    )

    id: Mapped[int] = col_id()
    item_orden_produccion_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("items_orden_produccion.id"),
        nullable=False,
        index=True,
    )
    categoria_costo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categorias_costo.id"), nullable=False, index=True
    )
    gasto_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("gastos.id"), nullable=True, index=True
    )
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    etapa_costo: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    cantidad: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False)
    costo_unitario: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    costo_total: Mapped[Decimal] = mapped_column(DINERO, nullable=False)
    creado_en: Mapped[datetime] = col_creado_en()

    item_orden_produccion: Mapped[ItemOrdenProduccion] = relationship(
        back_populates="asientos_costo"
    )
    categoria_costo: Mapped[CategoriaCosto] = relationship(back_populates="asientos")
    gasto: Mapped[Gasto | None] = relationship(back_populates="asientos_costo")
