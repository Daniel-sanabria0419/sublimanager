"""Repositorios del módulo inventario (A)."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.inventario.bodegas import Bodega
from app.models.inventario.categorias_material import CategoriaMaterial
from app.models.inventario.existencias import Existencia
from app.models.inventario.items_movimiento_inventario import ItemMovimientoInventario
from app.models.inventario.materiales import Material
from app.models.inventario.movimientos_inventario import MovimientoInventario
from app.models.inventario.unidades_medida import UnidadMedida
from app.repositories.base import RepositorioBase


class CategoriaMaterialRepo(RepositorioBase[CategoriaMaterial]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CategoriaMaterial)


class UnidadMedidaRepo(RepositorioBase[UnidadMedida]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, UnidadMedida)


class BodegaRepo(RepositorioBase[Bodega]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Bodega)


class MaterialRepo(RepositorioBase[Material]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Material)

    def obtener_bloqueado(self, id_: int) -> Material | None:
        """SELECT … FOR UPDATE sobre el material (promedio / stock)."""
        stmt = select(Material).where(Material.id == id_).with_for_update()
        return self.db.scalars(stmt).first()


class ExistenciaRepo(RepositorioBase[Existencia]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Existencia)

    def obtener_por_bodega_material(
        self, bodega_id: int, material_id: int, *, for_update: bool = False
    ) -> Existencia | None:
        stmt: Select[tuple[Existencia]] = select(Existencia).where(
            Existencia.bodega_id == bodega_id,
            Existencia.material_id == material_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        return self.db.scalars(stmt).first()

    def obtener_por_bodega_variante(
        self, bodega_id: int, variante_producto_id: int, *, for_update: bool = False
    ) -> Existencia | None:
        stmt: Select[tuple[Existencia]] = select(Existencia).where(
            Existencia.bodega_id == bodega_id,
            Existencia.variante_producto_id == variante_producto_id,
        )
        if for_update:
            stmt = stmt.with_for_update()
        return self.db.scalars(stmt).first()

    def stock_total_material(self, material_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(Existencia.cantidad), 0)).where(
            Existencia.material_id == material_id
        )
        valor = self.db.scalar(stmt)
        return Decimal(valor or 0)

    def listar_con_filtros(
        self,
        *,
        bodega_id: int | None = None,
        material_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Existencia]:
        stmt = select(Existencia)
        if bodega_id is not None:
            stmt = stmt.where(Existencia.bodega_id == bodega_id)
        if material_id is not None:
            stmt = stmt.where(Existencia.material_id == material_id)
        stmt = stmt.offset(offset).limit(limit).order_by(Existencia.id)
        return list(self.db.scalars(stmt).all())


class MovimientoInventarioRepo(RepositorioBase[MovimientoInventario]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, MovimientoInventario)

    def obtener_con_items(self, id_: int) -> MovimientoInventario | None:
        stmt = (
            select(MovimientoInventario)
            .where(MovimientoInventario.id == id_)
            .options(joinedload(MovimientoInventario.items))
        )
        return self.db.scalars(stmt).unique().first()

    def listar_por_referencia(
        self, tipo_referencia: str, referencia_id: int
    ) -> list[MovimientoInventario]:
        stmt = (
            select(MovimientoInventario)
            .where(
                MovimientoInventario.tipo_referencia == tipo_referencia,
                MovimientoInventario.referencia_id == referencia_id,
            )
            .options(joinedload(MovimientoInventario.items))
            .order_by(MovimientoInventario.id)
        )
        return list(self.db.scalars(stmt).unique().all())


class ItemMovimientoRepo(RepositorioBase[ItemMovimientoInventario]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ItemMovimientoInventario)
