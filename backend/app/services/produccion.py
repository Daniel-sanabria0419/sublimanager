"""OrdenProduccionService — producción desde pedido (§5.5–5.7).

V1: `pedido_id` NOT NULL. Inventario solo vía movimientos CONFIRMADOS
enlazados a cada `consumos_produccion` (sin doble descuento).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.constants import PEDIDO_ID_REQUERIDO_EN_OP
from app.core.exceptions import ConflictoNegocioError, ValidacionError
from app.models.enums import (
    EstadoMovimientoInventario,
    EstadoOrdenProduccion,
    EstadoPedido,
    EtapaCosto,
    TipoCosto,
    TipoMovimientoInventario,
    TipoProducto,
)
from app.models.produccion.asientos_costo_produccion import AsientoCostoProduccion
from app.models.produccion.consumos_produccion import ConsumoProduccion
from app.models.produccion.items_orden_produccion import ItemOrdenProduccion
from app.models.produccion.ordenes_produccion import OrdenProduccion
from app.models.recetas.categorias_costo import CategoriaCosto
from app.repositories.inventario import (
    BodegaRepo,
    ExistenciaRepo,
    MaterialRepo,
    MovimientoInventarioRepo,
)
from app.repositories.pedidos import ItemPedidoRepo, PedidoRepo
from app.repositories.produccion import (
    AsientoCostoProduccionRepo,
    ConsumoProduccionRepo,
    ItemOrdenProduccionRepo,
    OrdenProduccionRepo,
)
from app.repositories.productos import ProductoRepo, VarianteProductoRepo
from app.repositories.recetas import (
    CategoriaCostoRepo,
    PerfilCostoProductoRepo,
    RecetaProductoRepo,
)
from app.services.costos import ProductoCostoService
from app.services.inventario import ItemMovimientoDatos, MovimientoInventarioService
from app.utils.decimal_policy import (
    line_subtotal,
    money_round,
    percent_round,
    qty_round,
)

TIPO_REF_CONSUMO = "consumo_produccion"
TIPO_REF_ITEM_OP_PT = "item_orden_produccion_pt"
TIPO_REF_ORDEN = "orden_produccion"

# Pedidos desde los cuales se puede abrir OP (V1).
ESTADOS_PEDIDO_PARA_OP: frozenset[str] = frozenset(
    {
        EstadoPedido.CONFIRMADO,
        EstadoPedido.DISENO,
        EstadoPedido.ESPERANDO_APROBACION,
        EstadoPedido.EN_PRODUCCION,
        EstadoPedido.LISTO,
    }
)

TRANSICIONES_OP: dict[str, frozenset[str]] = {
    EstadoOrdenProduccion.PLANIFICADA: frozenset(
        {
            EstadoOrdenProduccion.EN_PROCESO,
            EstadoOrdenProduccion.CANCELADA,
        }
    ),
    EstadoOrdenProduccion.EN_PROCESO: frozenset(
        {
            EstadoOrdenProduccion.COMPLETADA,
            EstadoOrdenProduccion.CANCELADA,
        }
    ),
    EstadoOrdenProduccion.COMPLETADA: frozenset(),
    EstadoOrdenProduccion.CANCELADA: frozenset(),
}


@dataclass(frozen=True)
class ItemOpDatos:
    item_pedido_id: int
    cantidad_planificada: Decimal | None = None


@dataclass(frozen=True)
class ConsumoDatos:
    material_id: int
    cantidad_consumida: Decimal
    es_desperdicio: bool = False
    notas: str | None = None
    costo_unitario_snapshot: Decimal | None = None


@dataclass(frozen=True)
class AsientoCostoDatos:
    categoria_costo_id: int
    costo_unitario: Decimal
    cantidad: Decimal = Decimal("1")
    descripcion: str | None = None
    gasto_id: int | None = None
    etapa_costo: str = EtapaCosto.REAL


@dataclass(frozen=True)
class MaterialRequerido:
    material_id: int
    nombre_material: str
    cantidad_requerida: Decimal
    cantidad_disponible: Decimal
    costo_promedio: Decimal
    costo_estimado: Decimal
    suficiente: bool
    receta_id: int
    item_orden_produccion_id: int
    item_pedido_id: int


@dataclass(frozen=True)
class ComparacionCostoItem:
    item_orden_produccion_id: int
    item_pedido_id: int
    costo_estimado_total: Decimal
    costo_real_total: Decimal
    diferencia: Decimal
    estimado_por_tipo: dict[str, Decimal]
    real_por_tipo: dict[str, Decimal]
    costo_materiales_consumos: Decimal


@dataclass(frozen=True)
class ComparacionCostoOrden:
    orden_produccion_id: int
    items: list[ComparacionCostoItem]
    costo_estimado_total: Decimal
    costo_real_total: Decimal
    diferencia: Decimal


class OrdenProduccionService:
    """Orquesta OP, consumos únicos, PT y costos ESTIMADO/REAL."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.ordenes = OrdenProduccionRepo(db)
        self.items_op = ItemOrdenProduccionRepo(db)
        self.consumos = ConsumoProduccionRepo(db)
        self.asientos = AsientoCostoProduccionRepo(db)
        self.pedidos = PedidoRepo(db)
        self.items_pedido = ItemPedidoRepo(db)
        self.productos = ProductoRepo(db)
        self.variantes = VarianteProductoRepo(db)
        self.recetas = RecetaProductoRepo(db)
        self.perfiles = PerfilCostoProductoRepo(db)
        self.materiales = MaterialRepo(db)
        self.bodegas = BodegaRepo(db)
        self.existencias = ExistenciaRepo(db)
        self.movimientos_repo = MovimientoInventarioRepo(db)
        self.categorias_costo = CategoriaCostoRepo(db)
        self.movimientos = MovimientoInventarioService(db)
        self.costos = ProductoCostoService(db)

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    def obtener(self, id_: int) -> OrdenProduccion:
        op = self.ordenes.obtener_con_detalle(id_)
        if op is None:
            from app.core.exceptions import RecursoNoEncontradoError

            raise RecursoNoEncontradoError(f"orden_produccion id={id_} no encontrado")
        return op

    def listar(
        self,
        *,
        pedido_id: int | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[OrdenProduccion]:
        return self.ordenes.listar_filtrado(
            pedido_id=pedido_id, estado=estado, offset=offset, limit=limit
        )

    # ------------------------------------------------------------------
    # Alta desde pedido
    # ------------------------------------------------------------------

    def crear(
        self,
        *,
        pedido_id: int,
        items: list[ItemOpDatos],
        numero_produccion: str | None = None,
        notas: str | None = None,
        bodega_id: int | None = None,
    ) -> OrdenProduccion:
        if not PEDIDO_ID_REQUERIDO_EN_OP:
            raise ValidacionError("Configuración inconsistente: pedido_id requerido")
        if not items:
            raise ValidacionError("La orden de producción requiere al menos un ítem")

        pedido = self.pedidos.obtener_o_404(pedido_id, "pedido")
        if pedido.estado not in ESTADOS_PEDIDO_PARA_OP:
            raise ConflictoNegocioError(
                f"No se puede crear OP desde pedido en estado {pedido.estado}"
            )

        numero = (numero_produccion or "").strip() or self._generar_numero()
        if self.ordenes.obtener_por_numero(numero) is not None:
            raise ConflictoNegocioError(f"numero_produccion '{numero}' ya existe")

        op = OrdenProduccion(
            pedido_id=pedido.id,
            numero_produccion=numero,
            estado=EstadoOrdenProduccion.PLANIFICADA,
            notas=notas,
        )
        self.ordenes.agregar(op)

        vistos: set[int] = set()
        for dato in items:
            if dato.item_pedido_id in vistos:
                raise ValidacionError(
                    f"item_pedido_id={dato.item_pedido_id} duplicado en la OP"
                )
            vistos.add(dato.item_pedido_id)
            item_pedido = self.items_pedido.obtener_o_404(
                dato.item_pedido_id, "item_pedido"
            )
            if item_pedido.pedido_id != pedido.id:
                raise ValidacionError(
                    f"item_pedido {item_pedido.id} no pertenece al pedido {pedido.id}"
                )
            producto = self.productos.obtener_o_404(item_pedido.producto_id, "producto")
            if producto.tipo_producto != TipoProducto.FABRICADO:
                raise ValidacionError(
                    "Solo productos FABRICADO pueden incluirse en una OP "
                    f"(item_pedido={item_pedido.id}, tipo={producto.tipo_producto})"
                )

            planificada = (
                qty_round(dato.cantidad_planificada)
                if dato.cantidad_planificada is not None
                else qty_round(item_pedido.cantidad)
            )
            if planificada <= 0:
                raise ValidacionError("cantidad_planificada debe ser > 0")
            if planificada > qty_round(item_pedido.cantidad):
                raise ValidacionError(
                    "cantidad_planificada no puede exceder la cantidad del ítem "
                    f"de pedido ({item_pedido.cantidad})"
                )

            # Receta activa obligatoria al planificar.
            receta = self.recetas.obtener_activa(
                producto.id, item_pedido.variante_id
            )
            if receta is None:
                raise ValidacionError(
                    f"No hay receta activa para producto_id={producto.id}"
                )

            item_op = ItemOrdenProduccion(
                orden_produccion_id=op.id,
                item_pedido_id=item_pedido.id,
                cantidad_planificada=planificada,
                cantidad_producida=Decimal("0"),
                cantidad_rechazada=Decimal("0"),
            )
            self.items_op.agregar(item_op)
            self._crear_asientos_estimados(item_op, producto.id, item_pedido.variante_id)

        self.db.commit()
        return self.obtener(op.id)

    # ------------------------------------------------------------------
    # Materiales requeridos / disponibilidad
    # ------------------------------------------------------------------

    def materiales_requeridos(
        self, orden_id: int, *, bodega_id: int
    ) -> tuple[list[MaterialRequerido], bool]:
        op = self.obtener(orden_id)
        self.bodegas.obtener_o_404(bodega_id, "bodega")

        # Agregar por material para mostrar disponibilidad neta.
        agregados: dict[int, MaterialRequerido] = {}
        filas: list[MaterialRequerido] = []

        for item_op in op.items:
            item_pedido = item_op.item_pedido
            producto = self.productos.obtener_o_404(item_pedido.producto_id, "producto")
            receta = self.recetas.obtener_activa(producto.id, item_pedido.variante_id)
            if receta is None:
                raise ValidacionError(
                    f"No hay receta activa para producto_id={producto.id}"
                )
            for linea in receta.items:
                material = self.materiales.obtener_o_404(linea.material_id, "material")
                qty_base = qty_round(linea.cantidad)
                desperdicio = percent_round(linea.porcentaje_desperdicio)
                factor = Decimal("1") + (desperdicio / Decimal("100"))
                requerida = qty_round(
                    qty_base * factor * qty_round(item_op.cantidad_planificada)
                )
                existencia = self.existencias.obtener_por_bodega_material(
                    bodega_id, material.id
                )
                disponible = qty_round(
                    existencia.cantidad if existencia is not None else Decimal("0")
                )
                costo = money_round(material.costo_promedio)
                costo_est = line_subtotal(requerida, costo)
                fila = MaterialRequerido(
                    material_id=material.id,
                    nombre_material=material.nombre,
                    cantidad_requerida=requerida,
                    cantidad_disponible=disponible,
                    costo_promedio=costo,
                    costo_estimado=costo_est,
                    suficiente=disponible >= requerida,
                    receta_id=receta.id,
                    item_orden_produccion_id=item_op.id,
                    item_pedido_id=item_pedido.id,
                )
                filas.append(fila)
                prev = agregados.get(material.id)
                if prev is None:
                    agregados[material.id] = fila
                else:
                    nueva_req = qty_round(
                        prev.cantidad_requerida + fila.cantidad_requerida
                    )
                    agregados[material.id] = MaterialRequerido(
                        material_id=prev.material_id,
                        nombre_material=prev.nombre_material,
                        cantidad_requerida=nueva_req,
                        cantidad_disponible=prev.cantidad_disponible,
                        costo_promedio=prev.costo_promedio,
                        costo_estimado=line_subtotal(nueva_req, prev.costo_promedio),
                        suficiente=prev.cantidad_disponible >= nueva_req,
                        receta_id=prev.receta_id,
                        item_orden_produccion_id=prev.item_orden_produccion_id,
                        item_pedido_id=prev.item_pedido_id,
                    )

        todos = all(m.suficiente for m in agregados.values()) if agregados else True
        return filas, todos

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def iniciar(self, orden_id: int) -> OrdenProduccion:
        op = self.obtener(orden_id)
        self._transicionar(op, EstadoOrdenProduccion.EN_PROCESO)
        op.fecha_inicio = datetime.now(timezone.utc)
        self.db.commit()
        return self.obtener(orden_id)

    def cancelar(self, orden_id: int) -> OrdenProduccion:
        op = self.obtener(orden_id)
        if op.estado not in TRANSICIONES_OP or (
            EstadoOrdenProduccion.CANCELADA not in TRANSICIONES_OP[op.estado]
        ):
            raise ConflictoNegocioError(
                f"No se puede cancelar OP en estado {op.estado}"
            )
        # Reversos de consumos diferidos: bloquear si ya hubo consumos.
        for item in op.items:
            if item.consumos:
                raise ConflictoNegocioError(
                    "No se puede cancelar una OP con consumos registrados "
                    "(reversos diferidos a fase posterior)"
                )
        op.estado = EstadoOrdenProduccion.CANCELADA
        op.fecha_fin = datetime.now(timezone.utc)
        self.db.commit()
        return self.obtener(orden_id)

    def completar(
        self, orden_id: int, *, bodega_producto_id: int | None = None
    ) -> OrdenProduccion:
        op = self.obtener(orden_id)
        self._transicionar(op, EstadoOrdenProduccion.COMPLETADA)

        for item_op in op.items:
            self._consolidar_asientos_materiales_reales(item_op)
            if bodega_producto_id is not None:
                self._asegurar_entrada_producto_terminado(
                    item_op, bodega_id=bodega_producto_id
                )

        op.fecha_fin = datetime.now(timezone.utc)
        self.db.commit()
        return self.obtener(orden_id)

    # ------------------------------------------------------------------
    # Consumos (descuento único)
    # ------------------------------------------------------------------

    def registrar_consumo(
        self,
        orden_id: int,
        item_op_id: int,
        *,
        bodega_id: int,
        datos: ConsumoDatos,
    ) -> ConsumoProduccion:
        op = self.obtener(orden_id)
        if op.estado != EstadoOrdenProduccion.EN_PROCESO:
            raise ConflictoNegocioError(
                "Solo se registran consumos en OP EN_PROCESO"
            )
        item_op = self._item_de_orden(op, item_op_id)
        self.bodegas.obtener_o_404(bodega_id, "bodega")

        cantidad = qty_round(datos.cantidad_consumida)
        if cantidad <= 0:
            raise ValidacionError("cantidad_consumida debe ser > 0")

        material = self.materiales.obtener_o_404(datos.material_id, "material")
        costo_u = (
            money_round(datos.costo_unitario_snapshot)
            if datos.costo_unitario_snapshot is not None
            else money_round(material.costo_promedio)
        )
        if costo_u < 0:
            raise ValidacionError("costo_unitario_snapshot no puede ser negativo")

        # Validar disponibilidad antes de crear el consumo.
        existencia = self.existencias.obtener_por_bodega_material(
            bodega_id, material.id
        )
        disponible = qty_round(
            existencia.cantidad if existencia is not None else Decimal("0")
        )
        if disponible < cantidad:
            raise ConflictoNegocioError(
                f"Stock insuficiente de material_id={material.id} en bodega "
                f"{bodega_id}: disponible={disponible}, requerido={cantidad}"
            )

        consumo = ConsumoProduccion(
            item_orden_produccion_id=item_op.id,
            material_id=material.id,
            cantidad_consumida=cantidad,
            costo_unitario_snapshot=costo_u,
            costo_total=line_subtotal(cantidad, costo_u),
            consumido_en=datetime.now(timezone.utc),
            es_desperdicio=bool(datos.es_desperdicio),
            notas=datos.notas,
        )
        self.consumos.agregar(consumo)

        # Descuento único e idempotente: un movimiento CONFIRMADO por consumo.
        self._aplicar_descuento_inventario(consumo, bodega_id=bodega_id)

        self.db.commit()
        self.db.refresh(consumo)
        return consumo

    def _aplicar_descuento_inventario(
        self, consumo: ConsumoProduccion, *, bodega_id: int
    ) -> None:
        existentes = self.movimientos_repo.listar_por_referencia(
            TIPO_REF_CONSUMO, consumo.id
        )
        confirmados = [
            m
            for m in existentes
            if m.estado == EstadoMovimientoInventario.CONFIRMADO
        ]
        if confirmados:
            # Idempotencia: ya descontado.
            return

        tipo = (
            TipoMovimientoInventario.DESPERDICIO
            if consumo.es_desperdicio
            else TipoMovimientoInventario.PRODUCCION
        )
        self.movimientos.crear_y_confirmar(
            tipo_movimiento=tipo,
            bodega_id=bodega_id,
            items=[
                ItemMovimientoDatos(
                    material_id=consumo.material_id,
                    cantidad=consumo.cantidad_consumida,
                    costo_unitario=consumo.costo_unitario_snapshot,
                )
            ],
            notas=(
                f"Consumo OP item={consumo.item_orden_produccion_id} "
                f"consumo={consumo.id}"
            ),
            tipo_referencia=TIPO_REF_CONSUMO,
            referencia_id=consumo.id,
            commit=False,
        )

    # ------------------------------------------------------------------
    # Asientos de costo no material (REAL)
    # ------------------------------------------------------------------

    def registrar_asiento_costo(
        self,
        orden_id: int,
        item_op_id: int,
        *,
        datos: AsientoCostoDatos,
    ) -> AsientoCostoProduccion:
        op = self.obtener(orden_id)
        if op.estado not in {
            EstadoOrdenProduccion.EN_PROCESO,
            EstadoOrdenProduccion.COMPLETADA,
        }:
            raise ConflictoNegocioError(
                "Asientos REAL solo en OP EN_PROCESO o COMPLETADA"
            )
        item_op = self._item_de_orden(op, item_op_id)
        categoria = self.categorias_costo.obtener_o_404(
            datos.categoria_costo_id, "categoria_costo"
        )
        if categoria.tipo_costo == TipoCosto.MATERIAL:
            raise ValidacionError(
                "Los costos MATERIAL se consolidan desde consumos al cerrar; "
                "no registre asientos MATERIAL manuales"
            )
        etapa = datos.etapa_costo
        if etapa not in {EtapaCosto.ESTIMADO, EtapaCosto.REAL}:
            raise ValidacionError(f"etapa_costo inválida: {etapa}")
        if etapa == EtapaCosto.ESTIMADO:
            raise ValidacionError(
                "Los asientos ESTIMADO se generan al crear la OP; use etapa REAL"
            )

        cantidad = qty_round(datos.cantidad)
        if cantidad < 0:
            raise ValidacionError("cantidad no puede ser negativa")
        costo_u = money_round(datos.costo_unitario)
        if costo_u < 0:
            raise ValidacionError("costo_unitario no puede ser negativo")

        asiento = AsientoCostoProduccion(
            item_orden_produccion_id=item_op.id,
            categoria_costo_id=categoria.id,
            gasto_id=datos.gasto_id,
            descripcion=datos.descripcion,
            etapa_costo=EtapaCosto.REAL,
            cantidad=cantidad,
            costo_unitario=costo_u,
            costo_total=line_subtotal(cantidad, costo_u),
        )
        self.asientos.agregar(asiento)
        self.db.commit()
        self.db.refresh(asiento)
        return asiento

    # ------------------------------------------------------------------
    # Cantidades producidas / rechazadas (+ PT)
    # ------------------------------------------------------------------

    def registrar_cantidades(
        self,
        orden_id: int,
        item_op_id: int,
        *,
        cantidad_producida: Decimal,
        cantidad_rechazada: Decimal = Decimal("0"),
        bodega_producto_id: int | None = None,
    ) -> ItemOrdenProduccion:
        op = self.obtener(orden_id)
        if op.estado != EstadoOrdenProduccion.EN_PROCESO:
            raise ConflictoNegocioError(
                "Solo se registran cantidades en OP EN_PROCESO"
            )
        item_op = self._item_de_orden(op, item_op_id)

        producida = qty_round(cantidad_producida)
        rechazada = qty_round(cantidad_rechazada)
        if producida < 0 or rechazada < 0:
            raise ValidacionError("cantidades no pueden ser negativas")
        if producida + rechazada > qty_round(item_op.cantidad_planificada):
            raise ValidacionError(
                "cantidad_producida + cantidad_rechazada no puede exceder "
                f"cantidad_planificada ({item_op.cantidad_planificada})"
            )

        anterior = qty_round(item_op.cantidad_producida)
        delta = qty_round(producida - anterior)
        if delta < 0:
            ya_pt = self.movimientos_repo.listar_por_referencia(
                TIPO_REF_ITEM_OP_PT, item_op.id
            )
            if any(
                m.estado == EstadoMovimientoInventario.CONFIRMADO for m in ya_pt
            ):
                raise ConflictoNegocioError(
                    "No se permite reducir cantidad_producida tras haber entrado PT "
                    "(reversos diferidos)"
                )

        item_op.cantidad_producida = producida
        item_op.cantidad_rechazada = rechazada

        if delta > 0 and bodega_producto_id is not None:
            self._entrar_producto_terminado_delta(
                item_op, bodega_id=bodega_producto_id, cantidad=delta
            )

        self.db.commit()
        refreshed = self.items_op.obtener_con_detalle(item_op.id)
        assert refreshed is not None
        return refreshed

    # ------------------------------------------------------------------
    # Comparación ESTIMADO vs REAL
    # ------------------------------------------------------------------

    def comparar_costos(self, orden_id: int) -> ComparacionCostoOrden:
        op = self.obtener(orden_id)
        items_cmp: list[ComparacionCostoItem] = []
        total_est = Decimal("0.00")
        total_real = Decimal("0.00")

        for item_op in op.items:
            est_por_tipo = self._sumar_asientos_por_tipo(
                item_op, EtapaCosto.ESTIMADO
            )
            real_por_tipo = self._sumar_asientos_por_tipo(item_op, EtapaCosto.REAL)

            # Materiales reales: preferir asientos MATERIAL REAL; si aún no
            # consolidados (OP abierta), sumar consumos (incluye desperdicio).
            mat_consumos = money_round(
                sum((c.costo_total for c in item_op.consumos), Decimal("0"))
            )
            if TipoCosto.MATERIAL not in real_por_tipo and mat_consumos > 0:
                real_por_tipo[TipoCosto.MATERIAL] = mat_consumos

            est_total = money_round(
                sum(est_por_tipo.values(), Decimal("0"))
            )
            real_total = money_round(
                sum(real_por_tipo.values(), Decimal("0"))
            )
            items_cmp.append(
                ComparacionCostoItem(
                    item_orden_produccion_id=item_op.id,
                    item_pedido_id=item_op.item_pedido_id,
                    costo_estimado_total=est_total,
                    costo_real_total=real_total,
                    diferencia=money_round(real_total - est_total),
                    estimado_por_tipo=est_por_tipo,
                    real_por_tipo=real_por_tipo,
                    costo_materiales_consumos=mat_consumos,
                )
            )
            total_est = money_round(total_est + est_total)
            total_real = money_round(total_real + real_total)

        return ComparacionCostoOrden(
            orden_produccion_id=op.id,
            items=items_cmp,
            costo_estimado_total=total_est,
            costo_real_total=total_real,
            diferencia=money_round(total_real - total_est),
        )

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _generar_numero(self) -> str:
        seq = self.ordenes.siguiente_secuencia()
        return f"OP-{seq:06d}"

    def _transicionar(self, op: OrdenProduccion, nuevo: str) -> None:
        permitidos = TRANSICIONES_OP.get(op.estado, frozenset())
        if nuevo not in permitidos:
            raise ConflictoNegocioError(
                f"Transición OP inválida: {op.estado} → {nuevo}"
            )
        op.estado = nuevo

    def _item_de_orden(
        self, op: OrdenProduccion, item_op_id: int
    ) -> ItemOrdenProduccion:
        for item in op.items:
            if item.id == item_op_id:
                return item
        from app.core.exceptions import RecursoNoEncontradoError

        raise RecursoNoEncontradoError(
            f"item_orden_produccion id={item_op_id} no pertenece a OP {op.id}"
        )

    def _categoria_por_tipo(self, tipo_costo: str) -> CategoriaCosto:
        existentes = self.categorias_costo.listar(
            limit=500, filtros={"tipo_costo": tipo_costo, "activo": True}
        )
        if existentes:
            return existentes[0]
        nombres = {
            TipoCosto.MATERIAL: "Materiales producción",
            TipoCosto.MANO_OBRA: "Mano de obra",
            TipoCosto.ELECTRICIDAD: "Electricidad",
            TipoCosto.DEPRECIACION: "Depreciación",
            TipoCosto.OTRO: "Otros costos",
        }
        cat = CategoriaCosto(
            nombre=nombres.get(tipo_costo, f"Costo {tipo_costo}"),
            tipo_costo=tipo_costo,
            activo=True,
        )
        self.categorias_costo.agregar(cat)
        return cat

    def _crear_asientos_estimados(
        self,
        item_op: ItemOrdenProduccion,
        producto_id: int,
        variante_id: int | None,
    ) -> None:
        estimado = self.costos.estimar(
            producto_id=producto_id, variante_id=variante_id
        )
        qty = qty_round(item_op.cantidad_planificada)
        componentes = (
            (TipoCosto.MATERIAL, estimado.costo_materiales),
            (TipoCosto.MANO_OBRA, estimado.costo_mano_obra),
            (TipoCosto.ELECTRICIDAD, estimado.costo_electricidad),
            (TipoCosto.DEPRECIACION, estimado.costo_depreciacion),
            (TipoCosto.OTRO, estimado.costo_otros),
        )
        for tipo, unitario in componentes:
            unitario = money_round(unitario)
            if unitario == 0 and tipo != TipoCosto.MATERIAL:
                continue
            cat = self._categoria_por_tipo(tipo)
            asiento = AsientoCostoProduccion(
                item_orden_produccion_id=item_op.id,
                categoria_costo_id=cat.id,
                gasto_id=None,
                descripcion=f"Estimado {tipo} × {qty}",
                etapa_costo=EtapaCosto.ESTIMADO,
                cantidad=qty,
                costo_unitario=unitario,
                costo_total=line_subtotal(qty, unitario),
            )
            self.asientos.agregar(asiento)

    def _consolidar_asientos_materiales_reales(
        self, item_op: ItemOrdenProduccion
    ) -> None:
        """Un asiento MATERIAL REAL por ítem a partir de consumos (sin duplicar)."""
        cat_material = self._categoria_por_tipo(TipoCosto.MATERIAL)
        ya = [
            a
            for a in item_op.asientos_costo
            if a.etapa_costo == EtapaCosto.REAL
            and a.categoria_costo_id == cat_material.id
        ]
        if ya:
            return

        if not item_op.consumos:
            return

        total = money_round(
            sum((c.costo_total for c in item_op.consumos), Decimal("0"))
        )
        qty = qty_round(
            sum((c.cantidad_consumida for c in item_op.consumos), Decimal("0"))
        )
        if qty <= 0:
            return
        unitario = money_round(total / qty) if qty else Decimal("0.00")
        asiento = AsientoCostoProduccion(
            item_orden_produccion_id=item_op.id,
            categoria_costo_id=cat_material.id,
            gasto_id=None,
            descripcion="Consolidado desde consumos (incluye desperdicio)",
            etapa_costo=EtapaCosto.REAL,
            cantidad=qty,
            costo_unitario=unitario,
            costo_total=total,
        )
        self.asientos.agregar(asiento)

    def _entrar_producto_terminado_delta(
        self,
        item_op: ItemOrdenProduccion,
        *,
        bodega_id: int,
        cantidad: Decimal,
    ) -> None:
        item_pedido = item_op.item_pedido
        if item_pedido.variante_id is None:
            return
        variante = self.variantes.obtener_o_404(
            item_pedido.variante_id, "variante_producto"
        )
        if not variante.control_stock:
            return
        self.bodegas.obtener_o_404(bodega_id, "bodega")

        # Costo unitario PT ≈ costo unitario estimado del ítem de pedido.
        costo_u = money_round(item_pedido.costo_unitario_estimado)
        self.movimientos.crear_y_confirmar(
            tipo_movimiento=TipoMovimientoInventario.AJUSTE,
            bodega_id=bodega_id,
            items=[
                ItemMovimientoDatos(
                    variante_producto_id=variante.id,
                    cantidad=cantidad,
                    costo_unitario=costo_u,
                )
            ],
            notas=(
                f"Entrada PT OP item={item_op.id} "
                f"producida={item_op.cantidad_producida}"
            ),
            tipo_referencia=TIPO_REF_ITEM_OP_PT,
            referencia_id=item_op.id,
            commit=False,
        )

    def _asegurar_entrada_producto_terminado(
        self, item_op: ItemOrdenProduccion, *, bodega_id: int
    ) -> None:
        """Al completar: entra el remanente de PT no registrado aún."""
        producida = qty_round(item_op.cantidad_producida)
        if producida <= 0:
            return
        item_pedido = item_op.item_pedido
        if item_pedido.variante_id is None:
            return
        variante = self.variantes.obtener_o_404(
            item_pedido.variante_id, "variante_producto"
        )
        if not variante.control_stock:
            return

        ya = self.movimientos_repo.listar_por_referencia(
            TIPO_REF_ITEM_OP_PT, item_op.id
        )
        entrado = Decimal("0")
        for mov in ya:
            if mov.estado != EstadoMovimientoInventario.CONFIRMADO:
                continue
            for linea in mov.items:
                if linea.variante_producto_id == variante.id:
                    entrado = qty_round(entrado + linea.cantidad)

        faltante = qty_round(producida - entrado)
        if faltante > 0:
            self._entrar_producto_terminado_delta(
                item_op, bodega_id=bodega_id, cantidad=faltante
            )

    def _sumar_asientos_por_tipo(
        self, item_op: ItemOrdenProduccion, etapa: str
    ) -> dict[str, Decimal]:
        resultado: dict[str, Decimal] = {}
        for asiento in item_op.asientos_costo:
            if asiento.etapa_costo != etapa:
                continue
            cat = self.categorias_costo.obtener(asiento.categoria_costo_id)
            if cat is None:
                continue
            tipo = cat.tipo_costo
            resultado[tipo] = money_round(
                resultado.get(tipo, Decimal("0")) + money_round(asiento.costo_total)
            )
        return resultado
