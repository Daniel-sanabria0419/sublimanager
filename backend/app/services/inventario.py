"""Services de inventario (§5.1): materiales, existencias, movimientos."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoNegocioError, ValidacionError
from app.models.enums import EstadoMovimientoInventario, TipoMovimientoInventario
from app.models.inventario.bodegas import Bodega
from app.models.inventario.categorias_material import CategoriaMaterial
from app.models.inventario.existencias import Existencia
from app.models.inventario.items_movimiento_inventario import ItemMovimientoInventario
from app.models.inventario.materiales import Material
from app.models.inventario.movimientos_inventario import MovimientoInventario
from app.models.inventario.unidades_medida import UnidadMedida
from app.repositories.inventario import (
    BodegaRepo,
    CategoriaMaterialRepo,
    ExistenciaRepo,
    MaterialRepo,
    MovimientoInventarioRepo,
    UnidadMedidaRepo,
)
from app.utils.decimal_policy import line_subtotal, money_round, qty_round

# Dirección del stock según tipo (§5.1): cantidad de ítems siempre > 0.
TIPOS_ENTRADA: frozenset[str] = frozenset(
    {
        TipoMovimientoInventario.COMPRA,
        TipoMovimientoInventario.AJUSTE,
        TipoMovimientoInventario.DEVOLUCION,
        TipoMovimientoInventario.TRANSFERENCIA_ENTRADA,
    }
)
TIPOS_SALIDA: frozenset[str] = frozenset(
    {
        TipoMovimientoInventario.PRODUCCION,
        TipoMovimientoInventario.DESPERDICIO,
        TipoMovimientoInventario.TRANSFERENCIA_SALIDA,
        TipoMovimientoInventario.VENTA,
        TipoMovimientoInventario.REVERSO,
    }
)


@dataclass(frozen=True)
class ItemMovimientoDatos:
    cantidad: Decimal
    costo_unitario: Decimal
    material_id: int | None = None
    variante_producto_id: int | None = None


@dataclass(frozen=True)
class AlertaStockBajo:
    material_id: int
    nombre: str
    stock_minimo: Decimal
    stock_actual: Decimal
    faltante: Decimal


def _validar_xor_articulo(
    material_id: int | None, variante_producto_id: int | None
) -> None:
    tiene_mat = material_id is not None
    tiene_var = variante_producto_id is not None
    if tiene_mat == tiene_var:
        raise ValidacionError(
            "Debe indicar exactamente uno de material_id o variante_producto_id"
        )


def es_entrada(tipo_movimiento: str) -> bool:
    if tipo_movimiento in TIPOS_ENTRADA:
        return True
    if tipo_movimiento in TIPOS_SALIDA:
        return False
    raise ValidacionError(f"tipo_movimiento desconocido: {tipo_movimiento}")


class CatalogoInventarioService:
    """CRUD de catálogos: categorías, unidades, bodegas."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.categorias = CategoriaMaterialRepo(db)
        self.unidades = UnidadMedidaRepo(db)
        self.bodegas = BodegaRepo(db)

    # --- categorías ---
    def crear_categoria(
        self, *, nombre: str, descripcion: str | None = None, activo: bool = True
    ) -> CategoriaMaterial:
        cat = CategoriaMaterial(nombre=nombre, descripcion=descripcion, activo=activo)
        self.categorias.agregar(cat)
        self.db.commit()
        self.db.refresh(cat)
        return cat

    def listar_categorias(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[CategoriaMaterial]:
        return self.categorias.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener_categoria(self, id_: int) -> CategoriaMaterial:
        return self.categorias.obtener_o_404(id_, "categoria_material")

    def actualizar_categoria(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        descripcion: str | None = None,
        activo: bool | None = None,
    ) -> CategoriaMaterial:
        cat = self.obtener_categoria(id_)
        if nombre is not None:
            cat.nombre = nombre
        if descripcion is not None:
            cat.descripcion = descripcion
        if activo is not None:
            cat.activo = activo
        self.db.commit()
        self.db.refresh(cat)
        return cat

    def eliminar_categoria(self, id_: int) -> None:
        cat = self.obtener_categoria(id_)
        self.categorias.eliminar(cat)
        self.db.commit()

    # --- unidades ---
    def crear_unidad(
        self, *, nombre: str, abreviatura: str, activo: bool = True
    ) -> UnidadMedida:
        unidad = UnidadMedida(nombre=nombre, abreviatura=abreviatura, activo=activo)
        self.unidades.agregar(unidad)
        self.db.commit()
        self.db.refresh(unidad)
        return unidad

    def listar_unidades(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[UnidadMedida]:
        return self.unidades.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener_unidad(self, id_: int) -> UnidadMedida:
        return self.unidades.obtener_o_404(id_, "unidad_medida")

    def actualizar_unidad(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        abreviatura: str | None = None,
        activo: bool | None = None,
    ) -> UnidadMedida:
        unidad = self.obtener_unidad(id_)
        if nombre is not None:
            unidad.nombre = nombre
        if abreviatura is not None:
            unidad.abreviatura = abreviatura
        if activo is not None:
            unidad.activo = activo
        self.db.commit()
        self.db.refresh(unidad)
        return unidad

    def eliminar_unidad(self, id_: int) -> None:
        unidad = self.obtener_unidad(id_)
        self.unidades.eliminar(unidad)
        self.db.commit()

    # --- bodegas ---
    def crear_bodega(
        self, *, nombre: str, ubicacion: str | None = None, activo: bool = True
    ) -> Bodega:
        bodega = Bodega(nombre=nombre, ubicacion=ubicacion, activo=activo)
        self.bodegas.agregar(bodega)
        self.db.commit()
        self.db.refresh(bodega)
        return bodega

    def listar_bodegas(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[Bodega]:
        return self.bodegas.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener_bodega(self, id_: int) -> Bodega:
        return self.bodegas.obtener_o_404(id_, "bodega")

    def actualizar_bodega(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        ubicacion: str | None = None,
        activo: bool | None = None,
    ) -> Bodega:
        bodega = self.obtener_bodega(id_)
        if nombre is not None:
            bodega.nombre = nombre
        if ubicacion is not None:
            bodega.ubicacion = ubicacion
        if activo is not None:
            bodega.activo = activo
        self.db.commit()
        self.db.refresh(bodega)
        return bodega

    def eliminar_bodega(self, id_: int) -> None:
        bodega = self.obtener_bodega(id_)
        self.bodegas.eliminar(bodega)
        self.db.commit()


class MaterialService:
    """Alta/consulta de materiales; stock de apertura vía movimiento (§5.1)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.materiales = MaterialRepo(db)
        self.categorias = CategoriaMaterialRepo(db)
        self.unidades = UnidadMedidaRepo(db)
        self.bodegas = BodegaRepo(db)
        self.movimientos = MovimientoInventarioService(db)

    def crear(
        self,
        *,
        categoria_id: int,
        unidad_id: int,
        nombre: str,
        descripcion: str | None = None,
        stock_minimo: Decimal = Decimal("0"),
        activo: bool = True,
        stock_inicial: Decimal | None = None,
        bodega_id: int | None = None,
        costo_unitario_inicial: Decimal | None = None,
    ) -> Material:
        categoria = self.categorias.obtener_o_404(categoria_id, "categoria_material")
        if not categoria.activo:
            raise ValidacionError("La categoría de material no está activa")
        unidad = self.unidades.obtener_o_404(unidad_id, "unidad_medida")
        if not unidad.activo:
            raise ValidacionError("La unidad de medida no está activa")

        stock_min = qty_round(stock_minimo)
        if stock_min < 0:
            raise ValidacionError("stock_minimo debe ser >= 0")

        material = Material(
            categoria_id=categoria_id,
            unidad_id=unidad_id,
            nombre=nombre,
            descripcion=descripcion,
            stock_minimo=stock_min,
            costo_promedio=Decimal("0"),
            activo=activo,
        )
        self.materiales.agregar(material)

        if stock_inicial is not None and qty_round(stock_inicial) > 0:
            if bodega_id is None:
                raise ValidacionError(
                    "bodega_id es obligatorio cuando hay stock_inicial"
                )
            bodega = self.bodegas.obtener_o_404(bodega_id, "bodega")
            if not bodega.activo:
                raise ValidacionError("La bodega no está activa")
            costo = money_round(costo_unitario_inicial or Decimal("0"))
            if costo < 0:
                raise ValidacionError("costo_unitario_inicial no puede ser negativo")
            # Movimiento de apertura AJUSTE — nunca tocar existencias sin movimiento.
            self.movimientos.crear_y_confirmar(
                tipo_movimiento=TipoMovimientoInventario.AJUSTE,
                bodega_id=bodega_id,
                items=[
                    ItemMovimientoDatos(
                        material_id=material.id,
                        cantidad=qty_round(stock_inicial),
                        costo_unitario=costo,
                    )
                ],
                notas="Stock de apertura",
                tipo_referencia="apertura_material",
                referencia_id=material.id,
                actualizar_costo_promedio=True,
                commit=False,
            )

        self.db.commit()
        self.db.refresh(material)
        return material

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[Material]:
        return self.materiales.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> Material:
        return self.materiales.obtener_o_404(id_, "material")

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        descripcion: str | None = None,
        stock_minimo: Decimal | None = None,
        activo: bool | None = None,
        categoria_id: int | None = None,
        unidad_id: int | None = None,
    ) -> Material:
        material = self.obtener(id_)
        if nombre is not None:
            material.nombre = nombre
        if descripcion is not None:
            material.descripcion = descripcion
        if stock_minimo is not None:
            sm = qty_round(stock_minimo)
            if sm < 0:
                raise ValidacionError("stock_minimo debe ser >= 0")
            material.stock_minimo = sm
        if activo is not None:
            material.activo = activo
        if categoria_id is not None:
            cat = self.categorias.obtener_o_404(categoria_id, "categoria_material")
            if not cat.activo:
                raise ValidacionError("La categoría de material no está activa")
            material.categoria_id = categoria_id
        if unidad_id is not None:
            uni = self.unidades.obtener_o_404(unidad_id, "unidad_medida")
            if not uni.activo:
                raise ValidacionError("La unidad de medida no está activa")
            material.unidad_id = unidad_id
        # costo_promedio MUST NOT modificarse desde API genérica.
        self.db.commit()
        self.db.refresh(material)
        return material

    def alertas_stock_bajo(self) -> list[AlertaStockBajo]:
        existencias = ExistenciaRepo(self.db)
        alertas: list[AlertaStockBajo] = []
        for material in self.materiales.listar(limit=10_000, filtros={"activo": True}):
            stock = existencias.stock_total_material(material.id)
            if stock < material.stock_minimo:
                alertas.append(
                    AlertaStockBajo(
                        material_id=material.id,
                        nombre=material.nombre,
                        stock_minimo=material.stock_minimo,
                        stock_actual=qty_round(stock),
                        faltante=qty_round(material.stock_minimo - stock),
                    )
                )
        return alertas


class ExistenciaService:
    """Consultas de existencias (solo lectura vía API; escritura por movimientos)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ExistenciaRepo(db)

    def listar(
        self,
        *,
        bodega_id: int | None = None,
        material_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Existencia]:
        return self.repo.listar_con_filtros(
            bodega_id=bodega_id,
            material_id=material_id,
            offset=offset,
            limit=limit,
        )

    def obtener(self, id_: int) -> Existencia:
        return self.repo.obtener_o_404(id_, "existencia")

    def stock_material(self, material_id: int) -> Decimal:
        return qty_round(self.repo.stock_total_material(material_id))


class MovimientoInventarioService:
    """Única vía para alterar existencias (§5.1)."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MovimientoInventarioRepo(db)
        self.existencias = ExistenciaRepo(db)
        self.materiales = MaterialRepo(db)
        self.bodegas = BodegaRepo(db)

    def obtener(self, id_: int) -> MovimientoInventario:
        mov = self.repo.obtener_con_items(id_)
        if mov is None:
            from app.core.exceptions import RecursoNoEncontradoError

            raise RecursoNoEncontradoError(f"movimiento_inventario id={id_} no encontrado")
        return mov

    def listar(
        self,
        *,
        bodega_id: int | None = None,
        tipo_movimiento: str | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[MovimientoInventario]:
        return self.repo.listar(
            offset=offset,
            limit=limit,
            filtros={
                "bodega_id": bodega_id,
                "tipo_movimiento": tipo_movimiento,
                "estado": estado,
            },
        )

    def crear_y_confirmar(
        self,
        *,
        tipo_movimiento: str,
        bodega_id: int,
        items: list[ItemMovimientoDatos],
        notas: str | None = None,
        tipo_referencia: str | None = None,
        referencia_id: int | None = None,
        grupo_transferencia_id: UUID | None = None,
        fecha_movimiento: datetime | None = None,
        actualizar_costo_promedio: bool = False,
        commit: bool = True,
    ) -> MovimientoInventario:
        """Crea movimiento en CONFIRMADO y aplica stock en una sola transacción."""
        movimiento = self._crear_cabecera(
            tipo_movimiento=tipo_movimiento,
            bodega_id=bodega_id,
            estado=EstadoMovimientoInventario.CONFIRMADO,
            items=items,
            notas=notas,
            tipo_referencia=tipo_referencia,
            referencia_id=referencia_id,
            grupo_transferencia_id=grupo_transferencia_id,
            fecha_movimiento=fecha_movimiento,
        )
        self._aplicar_stock(
            movimiento, actualizar_costo_promedio=actualizar_costo_promedio
        )
        if commit:
            self.db.commit()
            self.db.refresh(movimiento)
        else:
            self.db.flush()
        return movimiento

    def crear_borrador(
        self,
        *,
        tipo_movimiento: str,
        bodega_id: int,
        items: list[ItemMovimientoDatos],
        notas: str | None = None,
        tipo_referencia: str | None = None,
        referencia_id: int | None = None,
        grupo_transferencia_id: UUID | None = None,
    ) -> MovimientoInventario:
        """Crea movimiento BORRADOR sin tocar existencias."""
        movimiento = self._crear_cabecera(
            tipo_movimiento=tipo_movimiento,
            bodega_id=bodega_id,
            estado=EstadoMovimientoInventario.BORRADOR,
            items=items,
            notas=notas,
            tipo_referencia=tipo_referencia,
            referencia_id=referencia_id,
            grupo_transferencia_id=grupo_transferencia_id,
        )
        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def confirmar(
        self, id_: int, *, actualizar_costo_promedio: bool = False
    ) -> MovimientoInventario:
        movimiento = self.obtener(id_)
        if movimiento.estado != EstadoMovimientoInventario.BORRADOR:
            raise ConflictoNegocioError(
                "Solo se pueden confirmar movimientos en estado BORRADOR"
            )
        movimiento.estado = EstadoMovimientoInventario.CONFIRMADO
        self._aplicar_stock(
            movimiento, actualizar_costo_promedio=actualizar_costo_promedio
        )
        self.db.commit()
        self.db.refresh(movimiento)
        return movimiento

    def transferir(
        self,
        *,
        bodega_origen_id: int,
        bodega_destino_id: int,
        items: list[ItemMovimientoDatos],
        notas: str | None = None,
    ) -> tuple[MovimientoInventario, MovimientoInventario]:
        """Par SALIDA/ENTRADA atómico con mismo grupo_transferencia_id."""
        if bodega_origen_id == bodega_destino_id:
            raise ValidacionError("bodega origen y destino deben ser distintas")
        grupo = uuid4()
        salida = self.crear_y_confirmar(
            tipo_movimiento=TipoMovimientoInventario.TRANSFERENCIA_SALIDA,
            bodega_id=bodega_origen_id,
            items=items,
            notas=notas,
            grupo_transferencia_id=grupo,
            commit=False,
        )
        entrada = self.crear_y_confirmar(
            tipo_movimiento=TipoMovimientoInventario.TRANSFERENCIA_ENTRADA,
            bodega_id=bodega_destino_id,
            items=items,
            notas=notas,
            grupo_transferencia_id=grupo,
            commit=False,
        )
        self.db.commit()
        self.db.refresh(salida)
        self.db.refresh(entrada)
        return salida, entrada

    def _crear_cabecera(
        self,
        *,
        tipo_movimiento: str,
        bodega_id: int,
        estado: str,
        items: list[ItemMovimientoDatos],
        notas: str | None,
        tipo_referencia: str | None,
        referencia_id: int | None,
        grupo_transferencia_id: UUID | None,
        fecha_movimiento: datetime | None = None,
    ) -> MovimientoInventario:
        if tipo_movimiento not in {*(TIPOS_ENTRADA | TIPOS_SALIDA)}:
            raise ValidacionError(f"tipo_movimiento inválido: {tipo_movimiento}")
        if not items:
            raise ValidacionError("El movimiento debe tener al menos un ítem")

        bodega = self.bodegas.obtener_o_404(bodega_id, "bodega")
        if not bodega.activo:
            raise ValidacionError("La bodega no está activa")

        movimiento = MovimientoInventario(
            tipo_movimiento=tipo_movimiento,
            estado=estado,
            grupo_transferencia_id=grupo_transferencia_id,
            tipo_referencia=tipo_referencia,
            referencia_id=referencia_id,
            bodega_id=bodega_id,
            fecha_movimiento=fecha_movimiento or datetime.now(timezone.utc),
            notas=notas,
        )
        self.repo.agregar(movimiento)

        for item in items:
            _validar_xor_articulo(item.material_id, item.variante_producto_id)
            cantidad = qty_round(item.cantidad)
            if cantidad <= 0:
                raise ValidacionError("cantidad del ítem debe ser > 0")
            costo_u = money_round(item.costo_unitario)
            if costo_u < 0:
                raise ValidacionError("costo_unitario no puede ser negativo")
            if item.material_id is not None:
                self.materiales.obtener_o_404(item.material_id, "material")
            linea = ItemMovimientoInventario(
                movimiento_id=movimiento.id,
                material_id=item.material_id,
                variante_producto_id=item.variante_producto_id,
                cantidad=cantidad,
                costo_unitario=costo_u,
                costo_total=line_subtotal(cantidad, costo_u),
            )
            self.db.add(linea)
        self.db.flush()
        self.db.refresh(movimiento)
        return movimiento

    def _aplicar_stock(
        self,
        movimiento: MovimientoInventario,
        *,
        actualizar_costo_promedio: bool = False,
    ) -> None:
        """Aplica delta de existencias; rechaza stock negativo."""
        entrada = es_entrada(movimiento.tipo_movimiento)
        # Recargar ítems
        mov = self.repo.obtener_con_items(movimiento.id)
        assert mov is not None
        for item in mov.items:
            delta = item.cantidad if entrada else -item.cantidad
            self._ajustar_existencia(
                bodega_id=mov.bodega_id,
                material_id=item.material_id,
                variante_producto_id=item.variante_producto_id,
                delta=delta,
            )
            if (
                actualizar_costo_promedio
                and entrada
                and item.material_id is not None
            ):
                self._actualizar_promedio_material(
                    material_id=item.material_id,
                    qty_recepcion=item.cantidad,
                    costo_recepcion=item.costo_unitario,
                    # Stock ya incluye la recepción: restar para fórmula.
                    qty_antes_de_esta_recepcion=self.existencias.stock_total_material(
                        item.material_id
                    )
                    - item.cantidad,
                )

    def _ajustar_existencia(
        self,
        *,
        bodega_id: int,
        material_id: int | None,
        variante_producto_id: int | None,
        delta: Decimal,
    ) -> Existencia:
        if material_id is not None:
            existencia = self.existencias.obtener_por_bodega_material(
                bodega_id, material_id, for_update=True
            )
        else:
            assert variante_producto_id is not None
            existencia = self.existencias.obtener_por_bodega_variante(
                bodega_id, variante_producto_id, for_update=True
            )

        if existencia is None:
            if delta < 0:
                raise ConflictoNegocioError(
                    "Stock insuficiente: no hay existencia previa para la salida"
                )
            existencia = Existencia(
                bodega_id=bodega_id,
                material_id=material_id,
                variante_producto_id=variante_producto_id,
                cantidad=Decimal("0"),
            )
            self.existencias.agregar(existencia)

        nueva = qty_round(existencia.cantidad + delta)
        if nueva < 0:
            raise ConflictoNegocioError(
                f"Stock insuficiente: la operación dejaría cantidad negativa "
                f"(actual={existencia.cantidad}, delta={delta})"
            )
        existencia.cantidad = nueva
        self.db.flush()
        return existencia

    def _actualizar_promedio_material(
        self,
        *,
        material_id: int,
        qty_recepcion: Decimal,
        costo_recepcion: Decimal,
        qty_antes_de_esta_recepcion: Decimal,
    ) -> None:
        from app.utils.decimal_policy import costo_promedio_ponderado

        material = self.materiales.obtener_bloqueado(material_id)
        if material is None:
            from app.core.exceptions import RecursoNoEncontradoError

            raise RecursoNoEncontradoError(f"material id={material_id} no encontrado")
        material.costo_promedio = costo_promedio_ponderado(
            qty_antes_de_esta_recepcion,
            material.costo_promedio,
            qty_recepcion,
            costo_recepcion,
        )
        self.db.flush()
