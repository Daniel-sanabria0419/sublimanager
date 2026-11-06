"""Tabla `pedidos`."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import IN_ESTADO_PEDIDO
from app.models.mixins import DINERO, col_actualizado_en, col_creado_en, col_id

if TYPE_CHECKING:
    from app.models.finanzas.pagos import Pago
    from app.models.pedidos.clientes import Cliente
    from app.models.pedidos.historial_estado_pedido import HistorialEstadoPedido
    from app.models.pedidos.items_pedido import ItemPedido
    from app.models.produccion.ordenes_produccion import OrdenProduccion


class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        CheckConstraint(
            f"estado IN ({IN_ESTADO_PEDIDO})",
            name="ck_pedidos_estado",
        ),
        CheckConstraint("subtotal >= 0", name="ck_pedidos_subtotal_ge_0"),
        CheckConstraint("descuento >= 0", name="ck_pedidos_descuento_ge_0"),
        CheckConstraint("total >= 0", name="ck_pedidos_total_ge_0"),
    )

    id: Mapped[int] = col_id()
    numero_pedido: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    cliente_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("clientes.id"), nullable=False, index=True
    )
    fecha_pedido: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    fecha_entrega: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    subtotal: Mapped[Decimal] = mapped_column(DINERO, nullable=False, default=Decimal("0"))
    # APROBADO: descuento = monto monetario (no porcentaje)
    descuento: Mapped[Decimal] = mapped_column(DINERO, nullable=False, default=Decimal("0"))
    total: Mapped[Decimal] = mapped_column(DINERO, nullable=False, default=Decimal("0"))
    estado: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    notas: Mapped[str | None] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = col_creado_en()
    actualizado_en: Mapped[datetime] = col_actualizado_en()

    cliente: Mapped[Cliente] = relationship(back_populates="pedidos")
    items: Mapped[list[ItemPedido]] = relationship(
        back_populates="pedido",
        cascade="all, delete-orphan",
    )
    historial_estados: Mapped[list[HistorialEstadoPedido]] = relationship(
        back_populates="pedido",
        cascade="all, delete-orphan",
    )
    ordenes_produccion: Mapped[list[OrdenProduccion]] = relationship(
        back_populates="pedido"
    )
    pagos: Mapped[list[Pago]] = relationship(back_populates="pedido")
