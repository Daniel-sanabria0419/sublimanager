"""Tabla `proveedores`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_activo, col_id

if TYPE_CHECKING:
    from app.models.compras.compras import Compra


class Proveedor(Base):
    __tablename__ = "proveedores"

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    identificacion: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = col_activo()

    compras: Mapped[list[Compra]] = relationship(back_populates="proveedor")
