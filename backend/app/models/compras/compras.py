"""Tabla `compras`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_COMPRA
from app.models.mixins import DINERO, col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.compras.items_compra import ItemCompra
    from app.models.compras.proveedores import Proveedor
    from app.models.finanzas.pagos_proveedor import PagoProveedor


class Compra(Base):
    __tablename__ = "compras"
    __table_args__ = (
        CheckConstraint(
            f"estado IN ({IN_ESTADO_COMPRA})",
            name="ck_compras_estado",
        ),
        CheckConstraint("subtotal >= 0", name="ck_compras_subtotal_ge_0"),
        CheckConstraint("total >= 0", name="ck_compras_total_ge_0"),
    )

    id: Mapped[int] = col_id()
    proveedor_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("proveedores.id"), nullable=False, index=True
    )
    fecha_compra: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    numero_factura: Mapped[str | None] = mapped_column(String(80), nullable=True)
    subtotal: Mapped[Decimal] = mapped_column(DINERO, nullable=False, default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(DINERO, nullable=False, default=Decimal("0"))
    estado: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    creado_en: Mapped[datetime] = col_creado_en()

    proveedor: Mapped[Proveedor] = relationship(back_populates="compras")
    items: Mapped[list[ItemCompra]] = relationship(
        back_populates="compra",
        cascade="all, delete-orphan",
    )
    pagos_proveedor: Mapped[list[PagoProveedor]] = relationship(back_populates="compra")
