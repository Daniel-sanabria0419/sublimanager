"""PedidoService — clientes/pedidos (§5.3): snapshots, estados, diseños.

Crear/editar pedido MUST NOT descontar materiales ni productos terminados.
REVENTA con control_stock descuenta inventario solo al pasar a ENTREGADO.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoNegocioError, ValidacionError
from app.models.enums import (
    EstadoAprobacionDiseno,
    EstadoPedido,
    TipoMovimientoInventario,
    TipoProducto,
)
from app.models.inventario.existencias import Existencia
from app.models.inventario.movimientos_inventario import MovimientoInventario
from app.models.pedidos.disenos_pedido import DisenoPedido
from app.models.pedidos.historial_estado_pedido import HistorialEstadoPedido
from app.models.pedidos.items_pedido import ItemPedido
from app.models.pedidos.pedidos import Pedido
from app.repositories.pedidos import (
    ClienteRepo,
    DisenoPedidoRepo,
    HistorialEstadoPedidoRepo,
    ItemPedidoRepo,
    PedidoRepo,
)
from app.repositories.productos import ProductoRepo, VarianteProductoRepo
from app.services.costos import ProductoCostoService
from app.services.inventario import ItemMovimientoDatos, MovimientoInventarioService
from app.utils.decimal_policy import a_decimal, line_subtotal, money_round, qty_round

# Transiciones válidas de estado de pedido (§5.3).
TRANSICIONES_PEDIDO: dict[str, frozenset[str]] = {
    EstadoPedido.PENDIENTE: frozenset(
        {
            EstadoPedido.CONFIRMADO,
            EstadoPedido.DISENO,
            EstadoPedido.CANCELADO,
        }
    ),
    EstadoPedido.CONFIRMADO: frozenset(
        {
            EstadoPedido.DISENO,
            EstadoPedido.ESPERANDO_APROBACION,
            EstadoPedido.EN_PRODUCCION,
            EstadoPedido.LISTO,
            EstadoPedido.CANCELADO,
        }
    ),
    EstadoPedido.DISENO: frozenset(
        {
            EstadoPedido.ESPERANDO_APROBACION,
            EstadoPedido.EN_PRODUCCION,
            EstadoPedido.CONFIRMADO,
            EstadoPedido.CANCELADO,
        }
    ),
    EstadoPedido.ESPERANDO_APROBACION: frozenset(
        {
            EstadoPedido.DISENO,
            EstadoPedido.EN_PRODUCCION,
            EstadoPedido.CONFIRMADO,
            EstadoPedido.CANCELADO,
        }
    ),
    EstadoPedido.EN_PRODUCCION: frozenset(
        {
            EstadoPedido.LISTO,
            EstadoPedido.CANCELADO,
        }
    ),
    EstadoPedido.LISTO: frozenset(
        {
            EstadoPedido.ENTREGADO,
            EstadoPedido.CANCELADO,
        }
    ),
    EstadoPedido.ENTREGADO: frozenset(),
    EstadoPedido.CANCELADO: frozenset(),
}

TRANSICIONES_APROBACION_DISENO: dict[str, frozenset[str]] = {
    EstadoAprobacionDiseno.BORRADOR: frozenset(
        {
            EstadoAprobacionDiseno.PENDIENTE_APROBACION,
            EstadoAprobacionDiseno.APROBADO,
            EstadoAprobacionDiseno.RECHAZADO,
        }
    ),
    EstadoAprobacionDiseno.PENDIENTE_APROBACION: frozenset(
        {
            EstadoAprobacionDiseno.APROBADO,
            EstadoAprobacionDiseno.RECHAZADO,
            EstadoAprobacionDiseno.BORRADOR,
        }
    ),
    EstadoAprobacionDiseno.APROBADO: frozenset(),
    EstadoAprobacionDiseno.RECHAZADO: frozenset(
        {
            EstadoAprobacionDiseno.BORRADOR,
            EstadoAprobacionDiseno.PENDIENTE_APROBACION,
        }
    ),
}


@dataclass(frozen=True)
class ItemPedidoDatos:
    producto_id: int
    cantidad: Decimal
    variante_id: int | None = None
    descripcion: str | None = None
    precio_venta_unitario: Decimal | None = None


class PedidoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.pedidos = PedidoRepo(db)
        self.items = ItemPedidoRepo(db)
        self.historial = HistorialEstadoPedidoRepo(db)
        self.disenos = DisenoPedidoRepo(db)
        self.clientes = ClienteRepo(db)
        self.productos = ProductoRepo(db)
        self.variantes = VarianteProductoRepo(db)
        self.costos = ProductoCostoService(db)
        self.movimientos = MovimientoInventarioService(db)

    # ------------------------------------------------------------------
    # Lectura / saldo
    # ------------------------------------------------------------------

    def obtener(self, id_: int) -> Pedido:
        pedido = self.pedidos.obtener_con_detalle(id_)
        if pedido is None:
            from app.core.exceptions import RecursoNoEncontradoError

            raise RecursoNoEncontradoError(f"pedido id={id_} no encontrado")
        return pedido

    def listar(
        self,
        *,
        cliente_id: int | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Pedido]:
        return self.pedidos.listar_filtrado(
            cliente_id=cliente_id,
            estado=estado,
            offset=offset,
            limit=limit,
        )

    def total_pagado(self, pedido_id: int) -> Decimal:
        return money_round(self.pedidos.suma_pagos_confirmados(pedido_id))

    def saldo_pendiente(self, pedido: Pedido) -> Decimal:
        pagado = self.total_pagado(pedido.id)
        return money_round(money_round(pedido.total) - pagado)

    # ------------------------------------------------------------------
    # Crear / actualizar
    # ------------------------------------------------------------------

    def crear(
        self,
        *,
        cliente_id: int,
        items: list[ItemPedidoDatos],
        numero_pedido: str | None = None,
        fecha_pedido: datetime | None = None,
        fecha_entrega: datetime | None = None,
        descuento: Decimal | int | str = Decimal("0"),
        notas: str | None = None,
    ) -> Pedido:
        if not items:
            raise ValidacionError("El pedido debe tener al menos un ítem")

        cliente = self.clientes.obtener_o_404(cliente_id, "cliente")
        if not cliente.activo:
            raise ValidacionError("El cliente no está activo")

        descuento_m = money_round(a_decimal(descuento))
        if descuento_m < 0:
            raise ValidacionError("descuento debe ser >= 0 (monto)")

        numero = (numero_pedido or "").strip() or self._generar_numero()
        if self.pedidos.obtener_por_numero(numero) is not None:
            raise ConflictoNegocioError(
                f"Ya existe un pedido con numero_pedido '{numero}'"
            )

        # Snapshot de existencias de materiales antes de crear (invariante §5.3).
        stock_antes = self._snapshot_stock_materiales()

        lineas: list[ItemPedido] = []
        subtotal = Decimal("0.00")
        for datos in items:
            item = self._construir_item(datos)
            lineas.append(item)
            subtotal = money_round(subtotal + item.subtotal)

        if descuento_m > subtotal:
            raise ValidacionError(
                "descuento no puede superar el subtotal del pedido"
            )
        total = money_round(subtotal - descuento_m)

        pedido = Pedido(
            numero_pedido=numero,
            cliente_id=cliente_id,
            fecha_pedido=fecha_pedido or datetime.now(timezone.utc),
            fecha_entrega=fecha_entrega,
            subtotal=subtotal,
            descuento=descuento_m,
            total=total,
            estado=EstadoPedido.PENDIENTE,
            notas=notas,
        )
        for item in lineas:
            pedido.items.append(item)

        try:
            self.pedidos.agregar(pedido)
            self._registrar_historial(
                pedido_id=pedido.id,
                estado_anterior=None,
                estado_nuevo=EstadoPedido.PENDIENTE,
                notas="Alta de pedido",
            )
            self.db.flush()
            stock_despues = self._snapshot_stock_materiales()
            if stock_antes != stock_despues:
                raise ConflictoNegocioError(
                    "Invariante violado: crear pedido no debe alterar inventario"
                )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictoNegocioError(
                f"No se pudo crear el pedido '{numero}'"
            ) from exc

        return self.obtener(pedido.id)

    def actualizar(
        self,
        id_: int,
        *,
        fecha_entrega: datetime | None = None,
        descuento: Decimal | int | str | None = None,
        notas: str | None = None,
    ) -> Pedido:
        pedido = self.obtener(id_)
        if pedido.estado in {EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO}:
            raise ConflictoNegocioError(
                f"No se puede editar un pedido en estado {pedido.estado}"
            )
        if fecha_entrega is not None:
            pedido.fecha_entrega = fecha_entrega
        if notas is not None:
            pedido.notas = notas
        if descuento is not None:
            descuento_m = money_round(a_decimal(descuento))
            if descuento_m < 0:
                raise ValidacionError("descuento debe ser >= 0 (monto)")
            if descuento_m > money_round(pedido.subtotal):
                raise ValidacionError(
                    "descuento no puede superar el subtotal del pedido"
                )
            pedido.descuento = descuento_m
            pedido.total = money_round(pedido.subtotal - descuento_m)
        self.db.commit()
        return self.obtener(id_)

    # ------------------------------------------------------------------
    # Estados
    # ------------------------------------------------------------------

    def cambiar_estado(
        self,
        id_: int,
        *,
        estado_nuevo: str,
        notas: str | None = None,
        bodega_id: int | None = None,
    ) -> Pedido:
        try:
            destino = EstadoPedido(estado_nuevo).value
        except ValueError as exc:
            raise ValidacionError(
                f"estado_nuevo inválido: {estado_nuevo}"
            ) from exc

        pedido = self.obtener(id_)
        origen = pedido.estado
        if destino == origen:
            raise ConflictoNegocioError(
                f"El pedido ya está en estado {destino}"
            )
        permitidos = TRANSICIONES_PEDIDO.get(origen, frozenset())
        if destino not in permitidos:
            raise ConflictoNegocioError(
                f"Transición no permitida: {origen} → {destino}"
            )

        if destino == EstadoPedido.ENTREGADO:
            self._entregar_reventa_si_aplica(pedido, bodega_id=bodega_id)

        self._registrar_historial(
            pedido_id=pedido.id,
            estado_anterior=origen,
            estado_nuevo=destino,
            notas=notas,
        )
        pedido.estado = destino
        self.db.commit()
        return self.obtener(id_)

    def cancelar(self, id_: int, *, notas: str | None = None) -> Pedido:
        return self.cambiar_estado(
            id_,
            estado_nuevo=EstadoPedido.CANCELADO,
            notas=notas or "Cancelación de pedido",
        )

    def listar_historial(self, pedido_id: int) -> list[HistorialEstadoPedido]:
        self.obtener(pedido_id)
        return self.historial.listar_por_pedido(pedido_id)

    # ------------------------------------------------------------------
    # Diseños (solo rutas; sin binarios)
    # ------------------------------------------------------------------

    def agregar_diseno(
        self,
        *,
        item_pedido_id: int,
        ruta_archivo: str,
        estado_aprobacion: str = EstadoAprobacionDiseno.BORRADOR,
        notas: str | None = None,
        version: int | None = None,
    ) -> DisenoPedido:
        item = self.items.obtener_o_404(item_pedido_id, "item_pedido")
        pedido = self.obtener(item.pedido_id)
        if pedido.estado == EstadoPedido.CANCELADO:
            raise ConflictoNegocioError(
                "No se pueden agregar diseños a un pedido CANCELADO"
            )
        ruta = ruta_archivo.strip()
        if not ruta:
            raise ValidacionError("ruta_archivo es obligatoria (sin binarios en BD)")
        if len(ruta) > 1024:
            raise ValidacionError("ruta_archivo supera 1024 caracteres")

        try:
            estado = EstadoAprobacionDiseno(estado_aprobacion).value
        except ValueError as exc:
            raise ValidacionError(
                f"estado_aprobacion inválido: {estado_aprobacion}"
            ) from exc

        ver = version if version is not None else self.disenos.siguiente_version(
            item_pedido_id
        )
        if ver < 1:
            raise ValidacionError("version debe ser > 0")

        diseno = DisenoPedido(
            item_pedido_id=item_pedido_id,
            ruta_archivo=ruta,
            version=ver,
            estado_aprobacion=estado,
            notas=notas,
        )
        self.disenos.agregar(diseno)
        self.db.commit()
        self.db.refresh(diseno)
        return diseno

    def actualizar_diseno(
        self,
        diseno_id: int,
        *,
        ruta_archivo: str | None = None,
        estado_aprobacion: str | None = None,
        notas: str | None = None,
    ) -> DisenoPedido:
        diseno = self.disenos.obtener_o_404(diseno_id, "diseno_pedido")
        if ruta_archivo is not None:
            ruta = ruta_archivo.strip()
            if not ruta:
                raise ValidacionError("ruta_archivo no puede estar vacía")
            diseno.ruta_archivo = ruta
        if notas is not None:
            diseno.notas = notas
        if estado_aprobacion is not None:
            try:
                destino = EstadoAprobacionDiseno(estado_aprobacion).value
            except ValueError as exc:
                raise ValidacionError(
                    f"estado_aprobacion inválido: {estado_aprobacion}"
                ) from exc
            origen = diseno.estado_aprobacion
            if destino != origen:
                permitidos = TRANSICIONES_APROBACION_DISENO.get(
                    origen, frozenset()
                )
                if destino not in permitidos:
                    raise ConflictoNegocioError(
                        f"Transición de diseño no permitida: {origen} → {destino}"
                    )
                diseno.estado_aprobacion = destino
        self.db.commit()
        self.db.refresh(diseno)
        return diseno

    def listar_disenos(
        self, *, item_pedido_id: int | None = None, pedido_id: int | None = None
    ) -> list[DisenoPedido]:
        if item_pedido_id is not None:
            self.items.obtener_o_404(item_pedido_id, "item_pedido")
            return self.disenos.listar_por_item(item_pedido_id)
        if pedido_id is not None:
            pedido = self.obtener(pedido_id)
            resultado: list[DisenoPedido] = []
            for item in pedido.items:
                resultado.extend(self.disenos.listar_por_item(item.id))
            return resultado
        raise ValidacionError("Indique item_pedido_id o pedido_id")

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _generar_numero(self) -> str:
        seq = self.pedidos.siguiente_secuencia()
        fecha = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"PED-{fecha}-{seq:05d}"

    def _construir_item(self, datos: ItemPedidoDatos) -> ItemPedido:
        cantidad = qty_round(a_decimal(datos.cantidad))
        if cantidad <= 0:
            raise ValidacionError("cantidad de ítem debe ser > 0")

        producto = self.productos.obtener_o_404(datos.producto_id, "producto")
        if not producto.activo:
            raise ValidacionError(
                f"El producto id={producto.id} no está activo"
            )

        variante = None
        precio: Decimal | None = (
            money_round(a_decimal(datos.precio_venta_unitario))
            if datos.precio_venta_unitario is not None
            else None
        )
        if datos.variante_id is not None:
            variante = self.variantes.obtener_o_404(
                datos.variante_id, "variante_producto"
            )
            if variante.producto_id != producto.id:
                raise ValidacionError(
                    "La variante no pertenece al producto indicado"
                )
            if not variante.activo:
                raise ValidacionError(
                    f"La variante id={variante.id} no está activa"
                )
            if precio is None:
                precio = money_round(variante.precio_venta)

        if precio is None:
            raise ValidacionError(
                "precio_venta_unitario es obligatorio si no hay variante"
            )
        if precio < 0:
            raise ValidacionError("precio_venta_unitario debe ser >= 0")

        # Snapshot de costo estimado (§5.3 / §5.4) vía servicio Stage 4.
        estimado = self.costos.estimar(
            producto_id=producto.id,
            variante_id=datos.variante_id,
        )
        costo_unitario = money_round(estimado.costo_estimado)
        subtotal = line_subtotal(cantidad, precio)

        return ItemPedido(
            producto_id=producto.id,
            variante_id=datos.variante_id,
            descripcion=datos.descripcion,
            cantidad=cantidad,
            precio_venta_unitario=precio,
            costo_unitario_estimado=costo_unitario,
            subtotal=subtotal,
        )

    def _registrar_historial(
        self,
        *,
        pedido_id: int,
        estado_anterior: str | None,
        estado_nuevo: str,
        notas: str | None,
    ) -> HistorialEstadoPedido:
        fila = HistorialEstadoPedido(
            pedido_id=pedido_id,
            estado_anterior=estado_anterior,
            estado_nuevo=estado_nuevo,
            notas=notas,
        )
        return self.historial.agregar(fila)

    def _snapshot_stock_materiales(self) -> dict[tuple[int, int], Decimal]:
        """Mapa (bodega_id, material_id) → cantidad (solo materiales)."""
        stmt = select(
            Existencia.bodega_id,
            Existencia.material_id,
            Existencia.cantidad,
        ).where(Existencia.material_id.is_not(None))
        return {
            (int(b), int(m)): qty_round(c)
            for b, m, c in self.db.execute(stmt).all()
        }

    def _entregar_reventa_si_aplica(
        self, pedido: Pedido, *, bodega_id: int | None
    ) -> None:
        """Al ENTREGADO: salida VENTA de variantes REVENTA con control_stock.

        FABRICADO / SERVICIO no descuentan materiales aquí (§5.3).
        """
        items_venta: list[ItemMovimientoDatos] = []
        for item in pedido.items:
            producto = self.productos.obtener_o_404(item.producto_id, "producto")
            if producto.tipo_producto != TipoProducto.REVENTA:
                continue
            if item.variante_id is None:
                raise ValidacionError(
                    "Ítem REVENTA requiere variante_id para entrega con stock"
                )
            variante = self.variantes.obtener_o_404(
                item.variante_id, "variante_producto"
            )
            if not variante.control_stock:
                continue
            items_venta.append(
                ItemMovimientoDatos(
                    cantidad=qty_round(item.cantidad),
                    costo_unitario=money_round(item.costo_unitario_estimado),
                    variante_producto_id=variante.id,
                )
            )

        if not items_venta:
            return
        if bodega_id is None:
            raise ValidacionError(
                "bodega_id es obligatorio al entregar ítems REVENTA con control_stock"
            )
        self.movimientos.crear_y_confirmar(
            tipo_movimiento=TipoMovimientoInventario.VENTA,
            bodega_id=bodega_id,
            items=items_venta,
            notas=f"Entrega pedido {pedido.numero_pedido}",
            tipo_referencia="pedido",
            referencia_id=pedido.id,
            commit=False,
        )

    def contar_movimientos_por_pedido(self, pedido_id: int) -> int:
        """Utilidad de prueba: movimientos de inventario referenciando el pedido."""
        stmt = select(func.count()).select_from(MovimientoInventario).where(
            MovimientoInventario.tipo_referencia == "pedido",
            MovimientoInventario.referencia_id == pedido_id,
        )
        return int(self.db.scalar(stmt) or 0)
