"""Tabla `clientes`."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_activo, col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.pedidos.pedidos import Pedido


class Cliente(Base):
    __tablename__ = "clientes"

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    identificacion: Mapped[str | None] = mapped_column(String(64), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(120), nullable=True)
    direccion: Mapped[str | None] = mapped_column(Text, nullable=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    activo: Mapped[bool] = col_activo()
    creado_en: Mapped[datetime] = col_creado_en()

    pedidos: Mapped[list[Pedido]] = relationship(back_populates="cliente")
