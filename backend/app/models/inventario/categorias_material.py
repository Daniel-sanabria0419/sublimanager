"""Tabla `categorias_material`."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_activo, col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.inventario.materiales import Material


class CategoriaMaterial(Base):
    __tablename__ = "categorias_material"

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = col_activo()
    creado_en: Mapped[datetime] = col_creado_en()

    materiales: Mapped[list[Material]] = relationship(back_populates="categoria")
