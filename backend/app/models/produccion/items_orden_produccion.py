"""Tabla `items_orden_produccion`."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import CANTIDAD, col_id

if TYPE_CHECKING:
    from app.models.pedidos.items_pedido import ItemPedido
    from app.models.produccion.asientos_costo_produccion import AsientoCostoProduccion
    from app.models.produccion.consumos_produccion import ConsumoProduccion
    from app.models.produccion.ordenes_produccion import OrdenProduccion


class ItemOrdenProduccion(Base):
    __tablename__ = "items_orden_produccion"
    __table_args__ = (
        CheckConstraint(
            "cantidad_planificada > 0",
            name="ck_items_op_planificada_gt_0",
        ),
        CheckConstraint(
            "cantidad_producida >= 0",
            name="ck_items_op_producida_ge_0",
        ),
        CheckConstraint(
            "cantidad_rechazada >= 0",
            name="ck_items_op_rechazada_ge_0",
        ),
        CheckConstraint(
            "cantidad_producida + cantidad_rechazada <= cantidad_planificada",
            name="ck_items_op_cantidades_coherentes",
        ),
    )

    id: Mapped[int] = col_id()
    orden_produccion_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("ordenes_produccion.id"), nullable=False, index=True
    )
    # V1: ligado a pedido — NOT NULL
    item_pedido_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("items_pedido.id"), nullable=False, index=True
    )
    cantidad_planificada: Mapped[Decimal] = mapped_column(CANTIDAD, nullable=False)
    cantidad_producida: Mapped[Decimal] = mapped_column(
        CANTIDAD, nullable=False, default=Decimal("0")
    )
    cantidad_rechazada: Mapped[Decimal] = mapped_column(
        CANTIDAD, nullable=False, default=Decimal("0")
    )

    orden_produccion: Mapped[OrdenProduccion] = relationship(back_populates="items")
    item_pedido: Mapped[ItemPedido] = relationship(back_populates="items_orden_produccion")
    consumos: Mapped[list[ConsumoProduccion]] = relationship(
        back_populates="item_orden_produccion",
        cascade="all, delete-orphan",
    )
    asientos_costo: Mapped[list[AsientoCostoProduccion]] = relationship(
        back_populates="item_orden_produccion",
        cascade="all, delete-orphan",
    )
