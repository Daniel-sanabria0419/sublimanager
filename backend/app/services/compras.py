"""Services de compras y recepción (§5.2)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictoNegocioError, RecursoNoEncontradoError, ValidacionError
from app.models.compras.compras import Compra
from app.models.compras.items_compra import ItemCompra
from app.models.compras.proveedores import Proveedor
from app.models.enums import EstadoCompra, EstadoMovimientoInventario, TipoMovimientoInventario
from app.repositories.compras import CompraRepo, ProveedorRepo
from app.repositories.inventario import BodegaRepo, MaterialRepo, MovimientoInventarioRepo
from app.services.inventario import ItemMovimientoDatos, MovimientoInventarioService
from app.utils.decimal_policy import line_subtotal, money_round, qty_round

TIPO_REF_COMPRA = "compra"


@dataclass(frozen=True)
class ItemCompraDatos:
    cantidad: Decimal
    costo_unitario: Decimal
    material_id: int | None = None
    variante_producto_id: int | None = None


@dataclass(frozen=True)
class RecepcionItemDatos:
    item_compra_id: int
    cantidad: Decimal


def _validar_xor(
    material_id: int | None, variante_producto_id: int | None
) -> None:
    if (material_id is None) == (variante_producto_id is None):
        raise ValidacionError(
            "Cada ítem debe tener exactamente uno de material_id o variante_producto_id"
        )


class ProveedorService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProveedorRepo(db)

    def crear(
        self,
        *,
        nombre: str,
        identificacion: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        activo: bool = True,
    ) -> Proveedor:
        proveedor = Proveedor(
            nombre=nombre,
            identificacion=identificacion,
            telefono=telefono,
            email=email,
            direccion=direccion,
            activo=activo,
        )
        self.repo.agregar(proveedor)
        self.db.commit()
        self.db.refresh(proveedor)
        return proveedor

    def listar(
        self, *, activo: bool | None = None, offset: int = 0, limit: int = 100
    ) -> list[Proveedor]:
        return self.repo.listar(
            offset=offset, limit=limit, filtros={"activo": activo}
        )

    def obtener(self, id_: int) -> Proveedor:
        return self.repo.obtener_o_404(id_, "proveedor")

    def actualizar(
        self,
        id_: int,
        *,
        nombre: str | None = None,
        identificacion: str | None = None,
        telefono: str | None = None,
        email: str | None = None,
        direccion: str | None = None,
        activo: bool | None = None,
    ) -> Proveedor:
        proveedor = self.obtener(id_)
        if nombre is not None:
            proveedor.nombre = nombre
        if identificacion is not None:
            proveedor.identificacion = identificacion
        if telefono is not None:
            proveedor.telefono = telefono
        if email is not None:
            proveedor.email = email
        if direccion is not None:
            proveedor.direccion = direccion
        if activo is not None:
            proveedor.activo = activo
        self.db.commit()
        self.db.refresh(proveedor)
        return proveedor

    def eliminar(self, id_: int) -> None:
        proveedor = self.obtener(id_)
        self.repo.eliminar(proveedor)
        self.db.commit()


class CompraService:
    """Compras: BORRADOR no toca inventario; recepción atómica §5.2."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.compras = CompraRepo(db)
        self.proveedores = ProveedorRepo(db)
        self.materiales = MaterialRepo(db)
        self.bodegas = BodegaRepo(db)
        self.movimientos_repo = MovimientoInventarioRepo(db)
        self.movimientos = MovimientoInventarioService(db)

    def crear(
        self,
        *,
        proveedor_id: int,
        items: list[ItemCompraDatos],
        numero_factura: str | None = None,
        fecha_compra: datetime | None = None,
        notas_estado: str | None = None,  # reserved
    ) -> Compra:
        """Crea compra siempre en BORRADOR (no toca inventario)."""
        del notas_estado  # API futura
        proveedor = self.proveedores.obtener_o_404(proveedor_id, "proveedor")
        if not proveedor.activo:
            raise ValidacionError("El proveedor no está activo")
        if not items:
            raise ValidacionError("La compra debe tener al menos un ítem")

        lineas: list[ItemCompra] = []
        subtotal = Decimal("0")
        for item in items:
            _validar_xor(item.material_id, item.variante_producto_id)
            cantidad = qty_round(item.cantidad)
            if cantidad <= 0:
                raise ValidacionError("cantidad del ítem debe ser > 0")
            costo = money_round(item.costo_unitario)
            if costo < 0:
                raise ValidacionError("costo_unitario no puede ser negativo")
            if item.material_id is not None:
                mat = self.materiales.obtener_o_404(item.material_id, "material")
                if not mat.activo:
                    raise ValidacionError(
                        f"El material id={item.material_id} no está activo"
                    )
            sub = line_subtotal(cantidad, costo)
            subtotal += sub
            lineas.append(
                ItemCompra(
                    material_id=item.material_id,
                    variante_producto_id=item.variante_producto_id,
                    cantidad=cantidad,
                    costo_unitario=costo,
                    subtotal=sub,
                )
            )

        compra = Compra(
            proveedor_id=proveedor_id,
            fecha_compra=fecha_compra or datetime.now(timezone.utc),
            numero_factura=numero_factura,
            subtotal=money_round(subtotal),
            total=money_round(subtotal),
            estado=EstadoCompra.BORRADOR,
            items=lineas,
        )
        self.compras.agregar(compra)
        self.db.commit()
        return self.obtener(compra.id)

    def obtener(self, id_: int) -> Compra:
        compra = self.compras.obtener_con_items(id_)
        if compra is None:
            raise RecursoNoEncontradoError(f"compra id={id_} no encontrada")
        return compra

    def listar(
        self,
        *,
        proveedor_id: int | None = None,
        estado: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Compra]:
        return self.compras.listar_con_items(
            proveedor_id=proveedor_id,
            estado=estado,
            offset=offset,
            limit=limit,
        )

    def cancelar(self, id_: int) -> Compra:
        """Cancela solo BORRADOR. Tras recepción exige política REVERSO."""
        compra = self.compras.obtener_con_items(id_, for_update=True)
        if compra is None:
            raise RecursoNoEncontradoError(f"compra id={id_} no encontrada")

        if compra.estado == EstadoCompra.CANCELADA:
            raise ConflictoNegocioError("La compra ya está CANCELADA")

        if compra.estado in (
            EstadoCompra.RECIBIDA,
            EstadoCompra.PARCIALMENTE_RECIBIDA,
        ):
            raise ConflictoNegocioError(
                "No se puede cancelar una compra ya recibida; "
                "use un movimiento REVERSO según la política de reversión"
            )

        if compra.estado != EstadoCompra.BORRADOR:
            raise ConflictoNegocioError(
                f"No se puede cancelar compra en estado {compra.estado}"
            )

        # CANCELADA MUST NOT generar movimientos.
        compra.estado = EstadoCompra.CANCELADA
        self.db.commit()
        self.db.refresh(compra)
        return compra

    def cantidades_recibidas(self, compra_id: int) -> dict[int, Decimal]:
        """Suma cantidades CONFIRMADAS tipo COMPRA por item_compra_id lógico.

        Clave: item_compra.id (emparejado por material_id / variante).
        """
        compra = self.obtener(compra_id)
        movimientos = self.movimientos_repo.listar_por_referencia(
            TIPO_REF_COMPRA, compra_id
        )
        # Acumular por (material_id, variante_producto_id)
        recibidos_articulo: dict[tuple[int | None, int | None], Decimal] = {}
        for mov in movimientos:
            if mov.estado != EstadoMovimientoInventario.CONFIRMADO:
                continue
            if mov.tipo_movimiento != TipoMovimientoInventario.COMPRA:
                continue
            for item in mov.items:
                clave = (item.material_id, item.variante_producto_id)
                recibidos_articulo[clave] = qty_round(
                    recibidos_articulo.get(clave, Decimal("0")) + item.cantidad
                )

        por_item: dict[int, Decimal] = {}
        for linea in compra.items:
            clave = (linea.material_id, linea.variante_producto_id)
            por_item[linea.id] = recibidos_articulo.get(clave, Decimal("0"))
        return por_item

    def recibir(
        self,
        id_: int,
        *,
        bodega_id: int,
        items: list[RecepcionItemDatos] | None = None,
        notas: str | None = None,
    ) -> Compra:
        """Recepción atómica: estado + movimiento COMPRA + existencias + promedio."""
        compra = self.compras.obtener_con_items(id_, for_update=True)
        if compra is None:
            raise RecursoNoEncontradoError(f"compra id={id_} no encontrada")

        if compra.estado == EstadoCompra.CANCELADA:
            raise ConflictoNegocioError(
                "Una compra CANCELADA no puede generar movimientos de inventario"
            )
        if compra.estado == EstadoCompra.RECIBIDA:
            raise ConflictoNegocioError("La compra ya está totalmente RECIBIDA")

        bodega = self.bodegas.obtener_o_404(bodega_id, "bodega")
        if not bodega.activo:
            raise ValidacionError("La bodega no está activa")

        ya_recibido = self.cantidades_recibidas(compra.id)
        items_por_id = {linea.id: linea for linea in compra.items}

        if items is None:
            # Recibir todo lo pendiente.
            recepciones = []
            for linea in compra.items:
                pendiente = qty_round(linea.cantidad - ya_recibido.get(linea.id, Decimal("0")))
                if pendiente > 0:
                    recepciones.append(
                        RecepcionItemDatos(item_compra_id=linea.id, cantidad=pendiente)
                    )
        else:
            recepciones = items

        if not recepciones:
            raise ValidacionError("No hay cantidades pendientes por recibir")

        mov_items: list[ItemMovimientoDatos] = []
        for rec in recepciones:
            linea = items_por_id.get(rec.item_compra_id)
            if linea is None or linea.compra_id != compra.id:
                raise ValidacionError(
                    f"item_compra_id={rec.item_compra_id} no pertenece a la compra"
                )
            cantidad = qty_round(rec.cantidad)
            if cantidad <= 0:
                raise ValidacionError("cantidad a recibir debe ser > 0")
            pendiente = qty_round(
                linea.cantidad - ya_recibido.get(linea.id, Decimal("0"))
            )
            if cantidad > pendiente:
                raise ValidacionError(
                    f"Cantidad a recibir ({cantidad}) supera el pendiente "
                    f"({pendiente}) del ítem {linea.id}"
                )
            mov_items.append(
                ItemMovimientoDatos(
                    material_id=linea.material_id,
                    variante_producto_id=linea.variante_producto_id,
                    cantidad=cantidad,
                    costo_unitario=linea.costo_unitario,
                )
            )
            ya_recibido[linea.id] = qty_round(
                ya_recibido.get(linea.id, Decimal("0")) + cantidad
            )

        # Movimiento COMPRA confirmado + stock + promedio (atómico).
        self.movimientos.crear_y_confirmar(
            tipo_movimiento=TipoMovimientoInventario.COMPRA,
            bodega_id=bodega_id,
            items=mov_items,
            notas=notas or f"Recepción compra #{compra.id}",
            tipo_referencia=TIPO_REF_COMPRA,
            referencia_id=compra.id,
            actualizar_costo_promedio=True,
            commit=False,
        )

        # Determinar estado final.
        total_completo = True
        alguno = False
        for linea in compra.items:
            recibido = ya_recibido.get(linea.id, Decimal("0"))
            if recibido > 0:
                alguno = True
            if recibido < linea.cantidad:
                total_completo = False

        if total_completo and alguno:
            compra.estado = EstadoCompra.RECIBIDA
        elif alguno:
            compra.estado = EstadoCompra.PARCIALMENTE_RECIBIDA
        else:
            raise ConflictoNegocioError("Recepción sin efecto en cantidades")

        self.db.commit()
        return self.obtener(compra.id)
