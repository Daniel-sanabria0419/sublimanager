"""Tabla `categorias_costo`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_TIPO_COSTO
from app.models.mixins import col_activo, col_id

if TYPE_CHECKING:
    from app.models.produccion.asientos_costo_produccion import AsientoCostoProduccion


class CategoriaCosto(Base):
    __tablename__ = "categorias_costo"
    __table_args__ = (
        CheckConstraint(
            f"tipo_costo IN ({IN_TIPO_COSTO})",
            name="ck_categorias_costo_tipo",
        ),
    )

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    tipo_costo: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    activo: Mapped[bool] = col_activo()

    asientos: Mapped[list[AsientoCostoProduccion]] = relationship(
        back_populates="categoria_costo"
    )
