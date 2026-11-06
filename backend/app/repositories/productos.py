"""Repositorios del módulo productos (B)."""

from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.productos.categorias_producto import CategoriaProducto
from app.models.productos.productos import Producto
from app.models.productos.tecnicas_produccion import TecnicaProduccion
from app.models.productos.tecnicas_producto import TecnicaProducto
from app.models.productos.variantes_producto import VarianteProducto
from app.repositories.base import RepositorioBase


class CategoriaProductoRepo(RepositorioBase[CategoriaProducto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CategoriaProducto)


class ProductoRepo(RepositorioBase[Producto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Producto)

    def listar_filtrado(
        self,
        *,
        activo: bool | None = None,
        tipo_producto: str | None = None,
        categoria_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Producto]:
        stmt: Select[tuple[Producto]] = select(Producto)
        if activo is not None:
            stmt = stmt.where(Producto.activo == activo)
        if tipo_producto is not None:
            stmt = stmt.where(Producto.tipo_producto == tipo_producto)
        if categoria_id is not None:
            stmt = stmt.where(Producto.categoria_id == categoria_id)
        stmt = stmt.offset(offset).limit(limit).order_by(Producto.id)
        return list(self.db.scalars(stmt).all())


class VarianteProductoRepo(RepositorioBase[VarianteProducto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, VarianteProducto)

    def obtener_por_sku(self, sku: str) -> VarianteProducto | None:
        stmt = select(VarianteProducto).where(VarianteProducto.sku == sku)
        return self.db.scalars(stmt).first()

    def listar_por_producto(
        self,
        producto_id: int,
        *,
        activo: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[VarianteProducto]:
        stmt = select(VarianteProducto).where(
            VarianteProducto.producto_id == producto_id
        )
        if activo is not None:
            stmt = stmt.where(VarianteProducto.activo == activo)
        stmt = stmt.offset(offset).limit(limit).order_by(VarianteProducto.id)
        return list(self.db.scalars(stmt).all())


class TecnicaProduccionRepo(RepositorioBase[TecnicaProduccion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TecnicaProduccion)


class TecnicaProductoRepo(RepositorioBase[TecnicaProducto]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TecnicaProducto)

    def obtener_par(
        self, producto_id: int, tecnica_id: int
    ) -> TecnicaProducto | None:
        stmt = select(TecnicaProducto).where(
            TecnicaProducto.producto_id == producto_id,
            TecnicaProducto.tecnica_id == tecnica_id,
        )
        return self.db.scalars(stmt).first()

    def listar_por_producto(self, producto_id: int) -> list[TecnicaProducto]:
        stmt = (
            select(TecnicaProducto)
            .where(TecnicaProducto.producto_id == producto_id)
            .order_by(TecnicaProducto.id)
        )
        return list(self.db.scalars(stmt).all())
