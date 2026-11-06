"""Repositorios del módulo compras (F)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.compras.compras import Compra
from app.models.compras.items_compra import ItemCompra
from app.models.compras.proveedores import Proveedor
from app.repositories.base import RepositorioBase


class ProveedorRepo(RepositorioBase[Proveedor]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Proveedor)


class CompraRepo(RepositorioBase[Compra]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Compra)

    def obtener_con_items(self, id_: int, *, for_update: bool = False) -> Compra | None:
        # FOR UPDATE no puede ir junto a LEFT OUTER JOIN de items (PostgreSQL).
        if for_update:
            stmt = select(Compra).where(Compra.id == id_).with_for_update()
            compra = self.db.scalars(stmt).first()
            if compra is None:
                return None
            _ = compra.items  # carga lazy dentro de la transacción
            return compra
        stmt = (
            select(Compra)
            .where(Compra.id == id_)
            .options(joinedload(Compra.items))
        )
        return self.db.scalars(stmt).unique().first()

    def listar_con_items(
        self,
        *,
        proveedor_id: int | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Compra]:
        stmt = select(Compra).options(joinedload(Compra.items))
        if proveedor_id is not None:
            stmt = stmt.where(Compra.proveedor_id == proveedor_id)
        if estado is not None:
            stmt = stmt.where(Compra.estado == estado)
        stmt = stmt.offset(offset).limit(limit).order_by(Compra.id)
        return list(self.db.scalars(stmt).unique().all())


class ItemCompraRepo(RepositorioBase[ItemCompra]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ItemCompra)
