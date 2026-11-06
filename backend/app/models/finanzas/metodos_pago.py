"""Tabla `metodos_pago`."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import col_activo, col_id

if TYPE_CHECKING:
    from app.models.finanzas.pagos import Pago
    from app.models.finanzas.pagos_gasto import PagoGasto
    from app.models.finanzas.pagos_proveedor import PagoProveedor


class MetodoPago(Base):
    __tablename__ = "metodos_pago"

    id: Mapped[int] = col_id()
    nombre: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    activo: Mapped[bool] = col_activo()

    pagos: Mapped[list[Pago]] = relationship(back_populates="metodo_pago")
    pagos_gasto: Mapped[list[PagoGasto]] = relationship(back_populates="metodo_pago")
    pagos_proveedor: Mapped[list[PagoProveedor]] = relationship(
        back_populates="metodo_pago"
    )
