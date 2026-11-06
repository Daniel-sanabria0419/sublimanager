"""ProductoCostoService — costo estimado unitario (§5.4)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ValidacionError
from app.models.enums import TipoProducto
from app.repositories.inventario import MaterialRepo
from app.repositories.productos import ProductoRepo, VarianteProductoRepo
from app.repositories.recetas import (
    PerfilCostoProductoRepo,
    RecetaProductoRepo,
    costo_adquisicion_variante,
)
from app.utils.decimal_policy import (
    a_decimal,
    money_round,
    percent_round,
    qty_round,
)


@dataclass(frozen=True)
class CostoEstimadoResultado:
    producto_id: int
    variante_id: int | None
    tipo_producto: str
    costo_materiales: Decimal
    costo_mano_obra: Decimal
    costo_electricidad: Decimal
    costo_depreciacion: Decimal
    costo_otros: Decimal
    costo_estimado: Decimal
    precio_venta: Decimal | None
    utilidad: Decimal | None
    margen_porcentaje: Decimal | None
    receta_id: int | None
    receta_version: int | None
    perfil_costo_id: int | None


class ProductoCostoService:
    """Calcula costo estimado según tipo de producto (Decimal ROUND_HALF_UP)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.productos = ProductoRepo(db)
        self.variantes = VarianteProductoRepo(db)
        self.recetas = RecetaProductoRepo(db)
        self.perfiles = PerfilCostoProductoRepo(db)
        self.materiales = MaterialRepo(db)

    def estimar(
        self,
        *,
        producto_id: int,
        variante_id: int | None = None,
        costo_adquisicion: Decimal | None = None,
    ) -> CostoEstimadoResultado:
        producto = self.productos.obtener_o_404(producto_id, "producto")
        precio_venta: Decimal | None = None
        if variante_id is not None:
            variante = self.variantes.obtener_o_404(variante_id, "variante_producto")
            if variante.producto_id != producto.id:
                raise ValidacionError(
                    "La variante no pertenece al producto indicado"
                )
            precio_venta = money_round(variante.precio_venta)

        tipo = producto.tipo_producto
        cero = Decimal("0")

        if tipo == TipoProducto.FABRICADO:
            return self._estimar_fabricado(
                producto_id=producto_id,
                variante_id=variante_id,
                precio_venta=precio_venta,
            )
        if tipo == TipoProducto.REVENTA:
            return self._estimar_reventa(
                producto_id=producto_id,
                variante_id=variante_id,
                precio_venta=precio_venta,
                costo_adquisicion=costo_adquisicion,
            )
        if tipo == TipoProducto.SERVICIO:
            return self._estimar_servicio(
                producto_id=producto_id,
                variante_id=variante_id,
                precio_venta=precio_venta,
            )
        raise ValidacionError(f"tipo_producto no soportado: {tipo}")

    def _perfil_componentes(
        self, producto_id: int, variante_id: int | None
    ) -> tuple[Decimal, Decimal, Decimal, Decimal, int | None]:
        perfil = self.perfiles.obtener_activo(producto_id, variante_id)
        if perfil is None:
            cero = Decimal("0.00")
            return cero, cero, cero, cero, None
        return (
            money_round(perfil.costo_mano_obra_por_unidad),
            money_round(perfil.costo_electricidad_por_unidad),
            money_round(perfil.costo_depreciacion_por_unidad),
            money_round(perfil.costo_otros_por_unidad),
            perfil.id,
        )

    def _costo_materiales_receta(
        self, producto_id: int, variante_id: int | None
    ) -> tuple[Decimal, int | None, int | None]:
        receta = self.recetas.obtener_activa(producto_id, variante_id)
        if receta is None:
            raise ValidacionError(
                "No hay receta activa para calcular el costo FABRICADO"
            )
        total = Decimal("0")
        for item in receta.items:
            material = self.materiales.obtener_o_404(item.material_id, "material")
            qty = qty_round(item.cantidad)
            desperdicio = percent_round(item.porcentaje_desperdicio)
            factor = Decimal("1") + (desperdicio / Decimal("100"))
            # Intermedios sin cortar; redondeo dinero al final de cada línea
            linea = money_round(
                qty * money_round(material.costo_promedio) * factor
            )
            total += linea
        return money_round(total), receta.id, receta.version

    def _con_margen(
        self,
        *,
        producto_id: int,
        variante_id: int | None,
        tipo_producto: str,
        costo_materiales: Decimal,
        costo_mano_obra: Decimal,
        costo_electricidad: Decimal,
        costo_depreciacion: Decimal,
        costo_otros: Decimal,
        costo_estimado: Decimal,
        precio_venta: Decimal | None,
        receta_id: int | None,
        receta_version: int | None,
        perfil_costo_id: int | None,
    ) -> CostoEstimadoResultado:
        utilidad: Decimal | None = None
        margen: Decimal | None = None
        if precio_venta is not None:
            utilidad = money_round(precio_venta - costo_estimado)
            if precio_venta != 0:
                margen = percent_round(
                    (utilidad / precio_venta) * Decimal("100")
                )
            else:
                margen = Decimal("0.00")
        return CostoEstimadoResultado(
            producto_id=producto_id,
            variante_id=variante_id,
            tipo_producto=tipo_producto,
            costo_materiales=costo_materiales,
            costo_mano_obra=costo_mano_obra,
            costo_electricidad=costo_electricidad,
            costo_depreciacion=costo_depreciacion,
            costo_otros=costo_otros,
            costo_estimado=costo_estimado,
            precio_venta=precio_venta,
            utilidad=utilidad,
            margen_porcentaje=margen,
            receta_id=receta_id,
            receta_version=receta_version,
            perfil_costo_id=perfil_costo_id,
        )

    def _estimar_fabricado(
        self,
        *,
        producto_id: int,
        variante_id: int | None,
        precio_venta: Decimal | None,
    ) -> CostoEstimadoResultado:
        mat, receta_id, version = self._costo_materiales_receta(
            producto_id, variante_id
        )
        mano, elec, deprec, otros, perfil_id = self._perfil_componentes(
            producto_id, variante_id
        )
        estimado = money_round(mat + mano + elec + deprec + otros)
        return self._con_margen(
            producto_id=producto_id,
            variante_id=variante_id,
            tipo_producto=TipoProducto.FABRICADO,
            costo_materiales=mat,
            costo_mano_obra=mano,
            costo_electricidad=elec,
            costo_depreciacion=deprec,
            costo_otros=otros,
            costo_estimado=estimado,
            precio_venta=precio_venta,
            receta_id=receta_id,
            receta_version=version,
            perfil_costo_id=perfil_id,
        )

    def _estimar_reventa(
        self,
        *,
        producto_id: int,
        variante_id: int | None,
        precio_venta: Decimal | None,
        costo_adquisicion: Decimal | None,
    ) -> CostoEstimadoResultado:
        if costo_adquisicion is not None:
            adquisicion = money_round(a_decimal(costo_adquisicion))
        elif variante_id is not None:
            adquisicion = money_round(
                costo_adquisicion_variante(self.db, variante_id)
            )
        else:
            raise ValidacionError(
                "REVENTA requiere variante_id o costo_adquisicion para el costo estimado"
            )
        if adquisicion < 0:
            raise ValidacionError("costo_adquisicion debe ser >= 0")
        cero = Decimal("0.00")
        return self._con_margen(
            producto_id=producto_id,
            variante_id=variante_id,
            tipo_producto=TipoProducto.REVENTA,
            costo_materiales=cero,
            costo_mano_obra=cero,
            costo_electricidad=cero,
            costo_depreciacion=cero,
            costo_otros=cero,
            costo_estimado=adquisicion,
            precio_venta=precio_venta,
            receta_id=None,
            receta_version=None,
            perfil_costo_id=None,
        )

    def _estimar_servicio(
        self,
        *,
        producto_id: int,
        variante_id: int | None,
        precio_venta: Decimal | None,
    ) -> CostoEstimadoResultado:
        mano, _elec, _deprec, otros, perfil_id = self._perfil_componentes(
            producto_id, variante_id
        )
        cero = Decimal("0.00")
        estimado = money_round(mano + otros)
        return self._con_margen(
            producto_id=producto_id,
            variante_id=variante_id,
            tipo_producto=TipoProducto.SERVICIO,
            costo_materiales=cero,
            costo_mano_obra=mano,
            costo_electricidad=cero,
            costo_depreciacion=cero,
            costo_otros=otros,
            costo_estimado=estimado,
            precio_venta=precio_venta,
            receta_id=None,
            receta_version=None,
            perfil_costo_id=perfil_id,
        )
