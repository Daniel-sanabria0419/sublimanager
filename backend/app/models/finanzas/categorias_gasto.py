"""Tabla `categorias_gasto`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_activo, col_id

if TYPE_CHECKING:
    from app.models.finanzas.gastos import Gasto


class CategoriaGasto(Base):
    __tablename__ = "categorias_gasto"

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = col_activo()

    gastos: Mapped[list[Gasto]] = relationship(back_populates="categoria")
