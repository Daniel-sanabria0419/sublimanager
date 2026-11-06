"""Repositorios del módulo pedidos (D)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.enums import EstadoPago
from app.models.finanzas.pagos import Pago
from app.models.pedidos.clientes import Cliente
from app.models.pedidos.disenos_pedido import DisenoPedido
from app.models.pedidos.historial_estado_pedido import HistorialEstadoPedido
from app.models.pedidos.items_pedido import ItemPedido
from app.models.pedidos.pedidos import Pedido
from app.repositories.base import RepositorioBase


class ClienteRepo(RepositorioBase[Cliente]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Cliente)


class PedidoRepo(RepositorioBase[Pedido]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Pedido)

    def obtener_con_detalle(self, id_: int) -> Pedido | None:
        stmt = (
            select(Pedido)
            .where(Pedido.id == id_)
            .options(
                selectinload(Pedido.items).selectinload(ItemPedido.disenos),
                selectinload(Pedido.historial_estados),
                selectinload(Pedido.pagos),
            )
        )
        return self.db.scalars(stmt).first()

    def obtener_por_numero(self, numero_pedido: str) -> Pedido | None:
        stmt = select(Pedido).where(Pedido.numero_pedido == numero_pedido)
        return self.db.scalars(stmt).first()

    def listar_filtrado(
        self,
        *,
        cliente_id: int | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Pedido]:
        stmt: Select[tuple[Pedido]] = select(Pedido)
        if cliente_id is not None:
            stmt = stmt.where(Pedido.cliente_id == cliente_id)
        if estado is not None:
            stmt = stmt.where(Pedido.estado == estado)
        stmt = stmt.offset(offset).limit(limit).order_by(Pedido.id)
        return list(self.db.scalars(stmt).all())

    def siguiente_secuencia(self) -> int:
        """Siguiente número secuencial para generar `numero_pedido`."""
        actual = self.db.scalar(select(func.coalesce(func.max(Pedido.id), 0)))
        return int(actual or 0) + 1

    def suma_pagos_confirmados(self, pedido_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(Pago.monto), 0)).where(
            Pago.pedido_id == pedido_id,
            Pago.estado == EstadoPago.CONFIRMADO,
        )
        valor = self.db.scalar(stmt)
        return Decimal(str(valor or 0))


class ItemPedidoRepo(RepositorioBase[ItemPedido]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ItemPedido)

    def listar_por_pedido(self, pedido_id: int) -> list[ItemPedido]:
        stmt = (
            select(ItemPedido)
            .where(ItemPedido.pedido_id == pedido_id)
            .order_by(ItemPedido.id)
        )
        return list(self.db.scalars(stmt).all())


class DisenoPedidoRepo(RepositorioBase[DisenoPedido]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, DisenoPedido)

    def listar_por_item(self, item_pedido_id: int) -> list[DisenoPedido]:
        stmt = (
            select(DisenoPedido)
            .where(DisenoPedido.item_pedido_id == item_pedido_id)
            .order_by(DisenoPedido.version, DisenoPedido.id)
        )
        return list(self.db.scalars(stmt).all())

    def siguiente_version(self, item_pedido_id: int) -> int:
        actual = self.db.scalar(
            select(func.coalesce(func.max(DisenoPedido.version), 0)).where(
                DisenoPedido.item_pedido_id == item_pedido_id
            )
        )
        return int(actual or 0) + 1


class HistorialEstadoPedidoRepo(RepositorioBase[HistorialEstadoPedido]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, HistorialEstadoPedido)

    def listar_por_pedido(self, pedido_id: int) -> list[HistorialEstadoPedido]:
        stmt = (
            select(HistorialEstadoPedido)
            .where(HistorialEstadoPedido.pedido_id == pedido_id)
            .order_by(HistorialEstadoPedido.id)
        )
        return list(self.db.scalars(stmt).all())
