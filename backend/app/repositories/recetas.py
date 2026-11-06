"""Repositorios del módulo recetas y costos (C)."""

from __future__ import annotations

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models.enums import EstadoMovimientoInventario, TipoMovimientoInventario
from app.models.inventario.items_movimiento_inventario import ItemMovimientoInventario
from app.models.inventario.movimientos_inventario import MovimientoInventario
from app.models.recetas.categorias_costo import CategoriaCosto
from app.models.recetas.items_receta_producto import ItemRecetaProducto
from app.models.recetas.perfiles_costo_producto import PerfilCostoProducto
from app.models.recetas.recetas_producto import RecetaProducto
from app.repositories.base import RepositorioBase


class CategoriaCostoRepo(RepositorioBase[CategoriaCosto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CategoriaCosto)


class RecetaProductoRepo(RepositorioBase[RecetaProducto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RecetaProducto)

    def obtener_con_items(self, id_: int) -> RecetaProducto | None:
        stmt = (
            select(RecetaProducto)
            .where(RecetaProducto.id == id_)
            .options(joinedload(RecetaProducto.items))
        )
        return self.db.scalars(stmt).unique().first()

    def siguiente_version(
        self, producto_id: int, variante_id: int | None
    ) -> int:
        stmt = select(func.coalesce(func.max(RecetaProducto.version), 0)).where(
            RecetaProducto.producto_id == producto_id
        )
        if variante_id is None:
            stmt = stmt.where(RecetaProducto.variante_id.is_(None))
        else:
            stmt = stmt.where(RecetaProducto.variante_id == variante_id)
        actual = self.db.scalar(stmt) or 0
        return int(actual) + 1

    def listar_por_alcance(
        self,
        producto_id: int,
        *,
        variante_id: int | None = None,
        solo_variante_exacta: bool = False,
        activo: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RecetaProducto]:
        stmt: Select[tuple[RecetaProducto]] = select(RecetaProducto).where(
            RecetaProducto.producto_id == producto_id
        )
        if solo_variante_exacta or variante_id is not None:
            if variante_id is None:
                stmt = stmt.where(RecetaProducto.variante_id.is_(None))
            else:
                stmt = stmt.where(RecetaProducto.variante_id == variante_id)
        if activo is not None:
            stmt = stmt.where(RecetaProducto.activo == activo)
        stmt = (
            stmt.options(joinedload(RecetaProducto.items))
            .offset(offset)
            .limit(limit)
            .order_by(RecetaProducto.version.desc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def desactivar_otras_del_alcance(
        self,
        producto_id: int,
        variante_id: int | None,
        *,
        excepto_id: int | None = None,
    ) -> None:
        stmt = select(RecetaProducto).where(
            RecetaProducto.producto_id == producto_id,
            RecetaProducto.activo.is_(True),
        )
        if variante_id is None:
            stmt = stmt.where(RecetaProducto.variante_id.is_(None))
        else:
            stmt = stmt.where(RecetaProducto.variante_id == variante_id)
        for receta in self.db.scalars(stmt).all():
            if excepto_id is not None and receta.id == excepto_id:
                continue
            receta.activo = False

    def obtener_activa(
        self, producto_id: int, variante_id: int | None = None
    ) -> RecetaProducto | None:
        """Activa del alcance exacto; si hay variante, fallback a receta de producto."""
        if variante_id is not None:
            stmt = (
                select(RecetaProducto)
                .where(
                    RecetaProducto.producto_id == producto_id,
                    RecetaProducto.variante_id == variante_id,
                    RecetaProducto.activo.is_(True),
                )
                .options(joinedload(RecetaProducto.items))
                .order_by(RecetaProducto.version.desc())
            )
            encontrada = self.db.scalars(stmt).unique().first()
            if encontrada is not None:
                return encontrada
        stmt = (
            select(RecetaProducto)
            .where(
                RecetaProducto.producto_id == producto_id,
                RecetaProducto.variante_id.is_(None),
                RecetaProducto.activo.is_(True),
            )
            .options(joinedload(RecetaProducto.items))
            .order_by(RecetaProducto.version.desc())
        )
        return self.db.scalars(stmt).unique().first()


class ItemRecetaRepo(RepositorioBase[ItemRecetaProducto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ItemRecetaProducto)


class PerfilCostoProductoRepo(RepositorioBase[PerfilCostoProducto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, PerfilCostoProducto)

    def listar_por_alcance(
        self,
        producto_id: int,
        *,
        variante_id: int | None = None,
        solo_variante_exacta: bool = False,
        activo: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PerfilCostoProducto]:
        stmt = select(PerfilCostoProducto).where(
            PerfilCostoProducto.producto_id == producto_id
        )
        if solo_variante_exacta or variante_id is not None:
            if variante_id is None:
                stmt = stmt.where(PerfilCostoProducto.variante_id.is_(None))
            else:
                stmt = stmt.where(PerfilCostoProducto.variante_id == variante_id)
        if activo is not None:
            stmt = stmt.where(PerfilCostoProducto.activo == activo)
        stmt = (
            stmt.offset(offset)
            .limit(limit)
            .order_by(PerfilCostoProducto.vigente_desde.desc(), PerfilCostoProducto.id.desc())
        )
        return list(self.db.scalars(stmt).all())

    def desactivar_otros_del_alcance(
        self,
        producto_id: int,
        variante_id: int | None,
        *,
        excepto_id: int | None = None,
    ) -> None:
        stmt = select(PerfilCostoProducto).where(
            PerfilCostoProducto.producto_id == producto_id,
            PerfilCostoProducto.activo.is_(True),
        )
        if variante_id is None:
            stmt = stmt.where(PerfilCostoProducto.variante_id.is_(None))
        else:
            stmt = stmt.where(PerfilCostoProducto.variante_id == variante_id)
        for perfil in self.db.scalars(stmt).all():
            if excepto_id is not None and perfil.id == excepto_id:
                continue
            perfil.activo = False

    def obtener_activo(
        self, producto_id: int, variante_id: int | None = None
    ) -> PerfilCostoProducto | None:
        if variante_id is not None:
            stmt = (
                select(PerfilCostoProducto)
                .where(
                    PerfilCostoProducto.producto_id == producto_id,
                    PerfilCostoProducto.variante_id == variante_id,
                    PerfilCostoProducto.activo.is_(True),
                )
                .order_by(
                    PerfilCostoProducto.vigente_desde.desc(),
                    PerfilCostoProducto.id.desc(),
                )
            )
            encontrada = self.db.scalars(stmt).first()
            if encontrada is not None:
                return encontrada
        stmt = (
            select(PerfilCostoProducto)
            .where(
                PerfilCostoProducto.producto_id == producto_id,
                PerfilCostoProducto.variante_id.is_(None),
                PerfilCostoProducto.activo.is_(True),
            )
            .order_by(
                PerfilCostoProducto.vigente_desde.desc(),
                PerfilCostoProducto.id.desc(),
            )
        )
        return self.db.scalars(stmt).first()


def costo_adquisicion_variante(db: Session, variante_id: int):
    """Último costo unitario de compra/ajuste confirmado para la variante (§5.4 REVENTA)."""
    from decimal import Decimal

    stmt = (
        select(ItemMovimientoInventario.costo_unitario)
        .join(
            MovimientoInventario,
            MovimientoInventario.id == ItemMovimientoInventario.movimiento_id,
        )
        .where(
            ItemMovimientoInventario.variante_producto_id == variante_id,
            MovimientoInventario.estado == EstadoMovimientoInventario.CONFIRMADO,
            MovimientoInventario.tipo_movimiento.in_(
                (
                    TipoMovimientoInventario.COMPRA,
                    TipoMovimientoInventario.AJUSTE,
                )
            ),
        )
        .order_by(
            MovimientoInventario.fecha_movimiento.desc(),
            ItemMovimientoInventario.id.desc(),
        )
        .limit(1)
    )
    valor = db.scalar(stmt)
    if valor is None:
        return Decimal("0")
    return Decimal(valor)
