"""Services de recetas y perfiles de costo (módulo C, históricos)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoNegocioError, ValidacionError
from app.models.enums import TipoCosto
from app.models.recetas.categorias_costo import CategoriaCosto
from app.models.recetas.items_receta_producto import ItemRecetaProducto
from app.models.recetas.perfiles_costo_producto import PerfilCostoProducto
from app.models.recetas.recetas_producto import RecetaProducto
from app.repositories.inventario import MaterialRepo
from app.repositories.productos import ProductoRepo, VarianteProductoRepo
from app.repositories.recetas import (
    CategoriaCostoRepo,
    PerfilCostoProductoRepo,
    RecetaProductoRepo,
)
from app.utils.decimal_policy import money_round, percent_round, qty_round


@dataclass(frozen=True)
class ItemRecetaDatos:
    material_id: int
    cantidad: Decimal
    porcentaje_desperdicio: Decimal = Decimal("0")
    notas: str | None = None


class CategoriaCostoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = CategoriaCostoRepo(db)

    def _validar_tipo(self, tipo_costo: str) -> str:
        try:
            return TipoCosto(tipo_costo).value
        except ValueError as exc:
            raise ValidacionError(f"tipo_costo inválido: {tipo_costo}") from exc

    def crear(
        self, *, nombre: str, tipo_costo: str, activo: bool = True
    ) -> CategoriaCosto:
        cat = CategoriaCosto(
            nombre=nombre,
            tipo_costo=self._validar_tipo(tipo_costo),
            activo=activo,
        )
        try:
            self.repo.agregar(cat)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                f"Ya existe la categoría de costo '{nombre}'"
            ) from exc
        self.db.refresh(cat)
        return cat

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[CategoriaCosto]:
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> CategoriaCosto:
        return self.repo.obtener_o_404(id_, "categoria_costo")

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        tipo_costo: str | None = None,
        activo: bool | None = None,
    ) -> CategoriaCosto:
        cat = self.obtener(id_)
        if nombre is not None:
            cat.nombre = nombre
        if tipo_costo is not None:
            cat.tipo_costo = self._validar_tipo(tipo_costo)
        if activo is not None:
            cat.activo = activo
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                "Nombre de categoría de costo duplicado"
            ) from exc
        self.db.refresh(cat)
        return cat

    def eliminar(self, id_: int) -> None:
        cat = self.obtener(id_)
        self.repo.eliminar(cat)
        self.db.commit()


class RecetaProductoService:
    """Versiones históricas: nunca sobrescribe; al activar desactiva la anterior."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = RecetaProductoRepo(db)
        self.productos = ProductoRepo(db)
        self.variantes = VarianteProductoRepo(db)
        self.materiales = MaterialRepo(db)

    def crear(
        self,
        *,
        producto_id: int,
        nombre: str,
        variante_id: int | None = None,
        activo: bool = True,
        items: list[ItemRecetaDatos] | None = None,
    ) -> RecetaProducto:
        producto = self.productos.obtener_o_404(producto_id, "producto")
        if variante_id is not None:
            variante = self.variantes.obtener_o_404(variante_id, "variante_producto")
            if variante.producto_id != producto.id:
                raise ValidacionError(
                    "La variante no pertenece al producto indicado"
                )

        items = items or []
        for item in items:
            if item.cantidad <= 0:
                raise ValidacionError("cantidad de ítem de receta debe ser > 0")
            if item.porcentaje_desperdicio < 0:
                raise ValidacionError("porcentaje_desperdicio debe ser >= 0")
            self.materiales.obtener_o_404(item.material_id, "material")

        version = self.repo.siguiente_version(producto_id, variante_id)
        receta = RecetaProducto(
            producto_id=producto_id,
            variante_id=variante_id,
            version=version,
            nombre=nombre,
            activo=False,
        )
        self.repo.agregar(receta)

        for item in items:
            linea = ItemRecetaProducto(
                receta_id=receta.id,
                material_id=item.material_id,
                cantidad=qty_round(item.cantidad),
                porcentaje_desperdicio=percent_round(item.porcentaje_desperdicio),
                notas=item.notas,
            )
            self.db.add(linea)
        self.db.flush()

        if activo:
            self.repo.desactivar_otras_del_alcance(
                producto_id, variante_id, excepto_id=receta.id
            )
            receta.activo = True

        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                "Conflicto de versión de receta (producto/variante/versión)"
            ) from exc

        cargada = self.repo.obtener_con_items(receta.id)
        assert cargada is not None
        return cargada

    def listar(
        self,
        *,
        producto_id: int,
        variante_id: int | None = None,
        solo_variante_exacta: bool = False,
        activo: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RecetaProducto]:
        self.productos.obtener_o_404(producto_id, "producto")
        return self.repo.listar_por_alcance(
            producto_id,
            variante_id=variante_id,
            solo_variante_exacta=solo_variante_exacta,
            activo=activo,
            offset=offset,
            limit=limit,
        )

    def obtener(self, id_: int) -> RecetaProducto:
        receta = self.repo.obtener_con_items(id_)
        if receta is None:
            from app.core.exceptions import RecursoNoEncontradoError

            raise RecursoNoEncontradoError(f"receta_producto id={id_} no encontrado")
        return receta

    def activar(self, id_: int) -> RecetaProducto:
        """Activa esta versión y desactiva las demás del mismo alcance (histórico intacto)."""
        receta = self.obtener(id_)
        self.repo.desactivar_otras_del_alcance(
            receta.producto_id, receta.variante_id, excepto_id=receta.id
        )
        receta.activo = True
        self.db.commit()
        return self.obtener(id_)


class PerfilCostoProductoService:
    """Perfiles históricos: cada cambio crea fila nueva; no sobrescribe vigentes previas."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PerfilCostoProductoRepo(db)
        self.productos = ProductoRepo(db)
        self.variantes = VarianteProductoRepo(db)

    def crear(
        self,
        *,
        producto_id: int,
        variante_id: int | None = None,
        costo_mano_obra_por_unidad: Decimal = Decimal("0"),
        costo_electricidad_por_unidad: Decimal = Decimal("0"),
        costo_depreciacion_por_unidad: Decimal = Decimal("0"),
        costo_otros_por_unidad: Decimal = Decimal("0"),
        vigente_desde: datetime | None = None,
        activo: bool = True,
    ) -> PerfilCostoProducto:
        producto = self.productos.obtener_o_404(producto_id, "producto")
        if variante_id is not None:
            variante = self.variantes.obtener_o_404(variante_id, "variante_producto")
            if variante.producto_id != producto.id:
                raise ValidacionError(
                    "La variante no pertenece al producto indicado"
                )

        costos = {
            "mano_obra": money_round(costo_mano_obra_por_unidad),
            "electricidad": money_round(costo_electricidad_por_unidad),
            "depreciacion": money_round(costo_depreciacion_por_unidad),
            "otros": money_round(costo_otros_por_unidad),
        }
        for nombre, valor in costos.items():
            if valor < 0:
                raise ValidacionError(f"costo_{nombre}_por_unidad debe ser >= 0")

        vigente = vigente_desde or datetime.now(timezone.utc)
        perfil = PerfilCostoProducto(
            producto_id=producto_id,
            variante_id=variante_id,
            costo_mano_obra_por_unidad=costos["mano_obra"],
            costo_electricidad_por_unidad=costos["electricidad"],
            costo_depreciacion_por_unidad=costos["depreciacion"],
            costo_otros_por_unidad=costos["otros"],
            vigente_desde=vigente,
            activo=False,
        )
        self.repo.agregar(perfil)

        if activo:
            self.repo.desactivar_otros_del_alcance(
                producto_id, variante_id, excepto_id=perfil.id
            )
            perfil.activo = True

        self.db.commit()
        self.db.refresh(perfil)
        return perfil

    def listar(
        self,
        *,
        producto_id: int,
        variante_id: int | None = None,
        solo_variante_exacta: bool = False,
        activo: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[PerfilCostoProducto]:
        self.productos.obtener_o_404(producto_id, "producto")
        return self.repo.listar_por_alcance(
            producto_id,
            variante_id=variante_id,
            solo_variante_exacta=solo_variante_exacta,
            activo=activo,
            offset=offset,
            limit=limit,
        )

    def obtener(self, id_: int) -> PerfilCostoProducto:
        return self.repo.obtener_o_404(id_, "perfil_costo_producto")

    def activar(self, id_: int) -> PerfilCostoProducto:
        perfil = self.obtener(id_)
        self.repo.desactivar_otros_del_alcance(
            perfil.producto_id, perfil.variante_id, excepto_id=perfil.id
        )
        perfil.activo = True
        self.db.commit()
        self.db.refresh(perfil)
        return perfil
