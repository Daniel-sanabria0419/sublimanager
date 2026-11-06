"""Services de productos (§ Stage 4 módulo B): catálogo, variantes, técnicas."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoNegocioError, ValidacionError
from app.models.enums import TipoProducto
from app.models.productos.categorias_producto import CategoriaProducto
from app.models.productos.productos import Producto
from app.models.productos.tecnicas_produccion import TecnicaProduccion
from app.models.productos.tecnicas_producto import TecnicaProducto
from app.models.productos.variantes_producto import VarianteProducto
from app.repositories.productos import (
    CategoriaProductoRepo,
    ProductoRepo,
    TecnicaProduccionRepo,
    TecnicaProductoRepo,
    VarianteProductoRepo,
)
from app.utils.decimal_policy import money_round


class CategoriaProductoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoriaProductoRepo(db)

    def crear(
        self, *, nombre: str, descripcion: str | None = None, activo: bool = True
    ) -> CategoriaProducto:
        cat = CategoriaProducto(nombre=nombre, descripcion=descripcion, activo=activo)
        try:
            self.repo.agregar(cat)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                f"Ya existe una categoría de producto con nombre '{nombre}'"
            ) from exc
        self.db.refresh(cat)
        return cat

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[CategoriaProducto]:
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> CategoriaProducto:
        return self.repo.obtener_o_404(id_, "categoria_producto")

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        descripcion: str | None = None,
        activo: bool | None = None,
    ) -> CategoriaProducto:
        cat = self.obtener(id_)
        if nombre is not None:
            cat.nombre = nombre
        if descripcion is not None:
            cat.descripcion = descripcion
        if activo is not None:
            cat.activo = activo
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                "Nombre de categoría de producto duplicado"
            ) from exc
        self.db.refresh(cat)
        return cat

    def eliminar(self, id_: int) -> None:
        cat = self.obtener(id_)
        self.repo.eliminar(cat)
        self.db.commit()


class ProductoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProductoRepo(db)
        self.categorias = CategoriaProductoRepo(db)

    def _validar_tipo(self, tipo_producto: str) -> str:
        try:
            return TipoProducto(tipo_producto).value
        except ValueError as exc:
            raise ValidacionError(
                f"tipo_producto inválido: {tipo_producto}. "
                "Use FABRICADO | REVENTA | SERVICIO"
            ) from exc

    def crear(
        self,
        *,
        categoria_id: int,
        nombre: str,
        tipo_producto: str,
        descripcion: str | None = None,
        activo: bool = True,
    ) -> Producto:
        cat = self.categorias.obtener_o_404(categoria_id, "categoria_producto")
        if not cat.activo:
            raise ValidacionError("La categoría de producto no está activa")
        tipo = self._validar_tipo(tipo_producto)
        producto = Producto(
            categoria_id=categoria_id,
            nombre=nombre,
            descripcion=descripcion,
            tipo_producto=tipo,
            activo=activo,
        )
        self.repo.agregar(producto)
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def listar(
        self,
        *,
        activo: bool | None = None,
        tipo_producto: str | None = None,
        categoria_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Producto]:
        if tipo_producto is not None:
            tipo_producto = self._validar_tipo(tipo_producto)
        return self.repo.listar_filtrado(
            activo=activo,
            tipo_producto=tipo_producto,
            categoria_id=categoria_id,
            offset=offset,
            limit=limit,
        )

    def obtener(self, id_: int) -> Producto:
        return self.repo.obtener_o_404(id_, "producto")

    def actualizar(
        self,
        id_: int,
        *,
        categoria_id: int | None = None,
        nombre: str | None = None,
        descripcion: str | None = None,
        tipo_producto: str | None = None,
        activo: bool | None = None,
    ) -> Producto:
        producto = self.obtener(id_)
        if categoria_id is not None:
            cat = self.categorias.obtener_o_404(categoria_id, "categoria_producto")
            if not cat.activo:
                raise ValidacionError("La categoría de producto no está activa")
            producto.categoria_id = categoria_id
        if nombre is not None:
            producto.nombre = nombre
        if descripcion is not None:
            producto.descripcion = descripcion
        if tipo_producto is not None:
            producto.tipo_producto = self._validar_tipo(tipo_producto)
        if activo is not None:
            producto.activo = activo
        self.db.commit()
        self.db.refresh(producto)
        return producto


class VarianteProductoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = VarianteProductoRepo(db)
        self.productos = ProductoRepo(db)

    def crear(
        self,
        *,
        producto_id: int,
        sku: str,
        talla: str | None = None,
        color: str | None = None,
        precio_venta: Decimal = Decimal("0"),
        control_stock: bool = True,
        activo: bool = True,
    ) -> VarianteProducto:
        self.productos.obtener_o_404(producto_id, "producto")
        precio = money_round(precio_venta)
        if precio < 0:
            raise ValidacionError("precio_venta debe ser >= 0")
        existente = self.repo.obtener_por_sku(sku)
        if existente is not None:
            raise ConflictoNegocioError(f"SKU '{sku}' ya está en uso")
        variante = VarianteProducto(
            producto_id=producto_id,
            sku=sku,
            talla=talla,
            color=color,
            precio_venta=precio,
            control_stock=control_stock,
            activo=activo,
        )
        try:
            self.repo.agregar(variante)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(f"SKU '{sku}' ya está en uso") from exc
        self.db.refresh(variante)
        return variante

    def listar(
        self,
        *,
        producto_id: int | None = None,
        activo: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[VarianteProducto]:
        if producto_id is not None:
            return self.repo.listar_por_producto(
                producto_id, activo=activo, offset=offset, limit=limit
            )
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> VarianteProducto:
        return self.repo.obtener_o_404(id_, "variante_producto")

    def actualizar(
        self,
        id_: int,
        *,
        sku: str | None = None,
        talla: str | None = None,
        color: str | None = None,
        precio_venta: Decimal | None = None,
        control_stock: bool | None = None,
        activo: bool | None = None,
    ) -> VarianteProducto:
        variante = self.obtener(id_)
        if sku is not None and sku != variante.sku:
            otra = self.repo.obtener_por_sku(sku)
            if otra is not None and otra.id != variante.id:
                raise ConflictoNegocioError(f"SKU '{sku}' ya está en uso")
            variante.sku = sku
        if talla is not None:
            variante.talla = talla
        if color is not None:
            variante.color = color
        if precio_venta is not None:
            precio = money_round(precio_venta)
            if precio < 0:
                raise ValidacionError("precio_venta debe ser >= 0")
            variante.precio_venta = precio
        if control_stock is not None:
            variante.control_stock = control_stock
        if activo is not None:
            variante.activo = activo
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError("SKU duplicado") from exc
        self.db.refresh(variante)
        return variante


class TecnicaProduccionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TecnicaProduccionRepo(db)

    def crear(
        self, *, nombre: str, descripcion: str | None = None, activo: bool = True
    ) -> TecnicaProduccion:
        tecnica = TecnicaProduccion(
            nombre=nombre, descripcion=descripcion, activo=activo
        )
        try:
            self.repo.agregar(tecnica)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                f"Ya existe la técnica '{nombre}'"
            ) from exc
        self.db.refresh(tecnica)
        return tecnica

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[TecnicaProduccion]:
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> TecnicaProduccion:
        return self.repo.obtener_o_404(id_, "tecnica_produccion")

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        descripcion: str | None = None,
        activo: bool | None = None,
    ) -> TecnicaProduccion:
        tecnica = self.obtener(id_)
        if nombre is not None:
            tecnica.nombre = nombre
        if descripcion is not None:
            tecnica.descripcion = descripcion
        if activo is not None:
            tecnica.activo = activo
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError("Nombre de técnica duplicado") from exc
        self.db.refresh(tecnica)
        return tecnica

    def eliminar(self, id_: int) -> None:
        tecnica = self.obtener(id_)
        self.repo.eliminar(tecnica)
        self.db.commit()


class TecnicaProductoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TecnicaProductoRepo(db)
        self.productos = ProductoRepo(db)
        self.tecnicas = TecnicaProduccionRepo(db)

    def vincular(self, *, producto_id: int, tecnica_id: int) -> TecnicaProducto:
        self.productos.obtener_o_404(producto_id, "producto")
        self.tecnicas.obtener_o_404(tecnica_id, "tecnica_produccion")
        existente = self.repo.obtener_par(producto_id, tecnica_id)
        if existente is not None:
            raise ConflictoNegocioError(
                "La técnica ya está vinculada a este producto"
            )
        vinculo = TecnicaProducto(producto_id=producto_id, tecnica_id=tecnica_id)
        try:
            self.repo.agregar(vinculo)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                "La técnica ya está vinculada a este producto"
            ) from exc
        self.db.refresh(vinculo)
        return vinculo

    def listar_por_producto(self, producto_id: int) -> list[TecnicaProducto]:
        self.productos.obtener_o_404(producto_id, "producto")
        return self.repo.listar_por_producto(producto_id)

    def desvincular(self, id_: int) -> None:
        vinculo = self.repo.obtener_o_404(id_, "tecnica_producto")
        self.repo.eliminar(vinculo)
        self.db.commit()
