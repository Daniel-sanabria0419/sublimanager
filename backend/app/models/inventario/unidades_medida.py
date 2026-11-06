"""Tabla `unidades_medida`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_activo, col_id

if TYPE_CHECKING:
    from app.models.inventario.materiales import Material


class UnidadMedida(Base):
    __tablename__ = "unidades_medida"

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    abreviatura: Mapped[str] = mapped_column(String(16), nullable=False)
    activo: Mapped[bool] = col_activo()

    materiales: Mapped[list[Material]] = relationship(back_populates="unidad")
