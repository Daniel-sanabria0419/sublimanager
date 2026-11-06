"""Tabla `bodegas`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_activo, col_id

if TYPE_CHECKING:
    from app.models.inventario.existencias import Existencia
    from app.models.inventario.movimientos_inventario import MovimientoInventario


class Bodega(Base):
    __tablename__ = "bodegas"

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    ubicacion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    activo: Mapped[bool] = col_activo()

    existencias: Mapped[list[Existencia]] = relationship(back_populates="bodega")
    movimientos: Mapped[list[MovimientoInventario]] = relationship(
        back_populates="bodega"
    )
