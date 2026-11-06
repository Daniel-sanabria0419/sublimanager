"""Repositorios del módulo producción (E)."""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.produccion.asientos_costo_produccion import AsientoCostoProduccion
from app.models.produccion.consumos_produccion import ConsumoProduccion
from app.models.produccion.items_orden_produccion import ItemOrdenProduccion
from app.models.produccion.ordenes_produccion import OrdenProduccion
from app.repositories.base import RepositorioBase


class OrdenProduccionRepo(RepositorioBase[OrdenProduccion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, OrdenProduccion)

    def obtener_con_detalle(self, id_: int) -> OrdenProduccion | None:
        stmt = (
            select(OrdenProduccion)
            .where(OrdenProduccion.id == id_)
            .options(
                selectinload(OrdenProduccion.items).selectinload(
                    ItemOrdenProduccion.consumos
                ),
                selectinload(OrdenProduccion.items).selectinload(
                    ItemOrdenProduccion.asientos_costo
                ),
                selectinload(OrdenProduccion.items).selectinload(
                    ItemOrdenProduccion.item_pedido
                ),
            )
        )
        return self.db.scalars(stmt).first()

    def obtener_por_numero(self, numero_produccion: str) -> OrdenProduccion | None:
        stmt = select(OrdenProduccion).where(
            OrdenProduccion.numero_produccion == numero_produccion
        )
        return self.db.scalars(stmt).first()

    def listar_filtrado(
        self,
        *,
        pedido_id: int | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[OrdenProduccion]:
        stmt: Select[tuple[OrdenProduccion]] = select(OrdenProduccion)
        if pedido_id is not None:
            stmt = stmt.where(OrdenProduccion.pedido_id == pedido_id)
        if estado is not None:
            stmt = stmt.where(OrdenProduccion.estado == estado)
        stmt = stmt.offset(offset).limit(limit).order_by(OrdenProduccion.id)
        return list(self.db.scalars(stmt).all())

    def siguiente_secuencia(self) -> int:
        actual = self.db.scalar(select(func.coalesce(func.max(OrdenProduccion.id), 0)))
        return int(actual or 0) + 1


class ItemOrdenProduccionRepo(RepositorioBase[ItemOrdenProduccion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ItemOrdenProduccion)

    def obtener_con_detalle(self, id_: int) -> ItemOrdenProduccion | None:
        stmt = (
            select(ItemOrdenProduccion)
            .where(ItemOrdenProduccion.id == id_)
            .options(
                selectinload(ItemOrdenProduccion.consumos),
                selectinload(ItemOrdenProduccion.asientos_costo),
                selectinload(ItemOrdenProduccion.item_pedido),
                selectinload(ItemOrdenProduccion.orden_produccion),
            )
        )
        return self.db.scalars(stmt).first()

    def listar_por_orden(self, orden_produccion_id: int) -> list[ItemOrdenProduccion]:
        stmt = (
            select(ItemOrdenProduccion)
            .where(ItemOrdenProduccion.orden_produccion_id == orden_produccion_id)
            .order_by(ItemOrdenProduccion.id)
        )
        return list(self.db.scalars(stmt).all())


class ConsumoProduccionRepo(RepositorioBase[ConsumoProduccion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ConsumoProduccion)

    def listar_por_item(self, item_orden_produccion_id: int) -> list[ConsumoProduccion]:
        stmt = (
            select(ConsumoProduccion)
            .where(
                ConsumoProduccion.item_orden_produccion_id == item_orden_produccion_id
            )
            .order_by(ConsumoProduccion.id)
        )
        return list(self.db.scalars(stmt).all())


class AsientoCostoProduccionRepo(RepositorioBase[AsientoCostoProduccion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AsientoCostoProduccion)

    def listar_por_item(
        self,
        item_orden_produccion_id: int,
        *,
        etapa_costo: str | None = None,
    ) -> list[AsientoCostoProduccion]:
        stmt = select(AsientoCostoProduccion).where(
            AsientoCostoProduccion.item_orden_produccion_id == item_orden_produccion_id
        )
        if etapa_costo is not None:
            stmt = stmt.where(AsientoCostoProduccion.etapa_costo == etapa_costo)
        stmt = stmt.order_by(AsientoCostoProduccion.id)
        return list(self.db.scalars(stmt).all())
