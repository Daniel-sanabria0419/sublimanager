"""API `/api/v1/pedidos` — alta, totales, estados, diseños, saldo."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ValidacionError
from app.schemas.pedidos import (
    DisenoPedidoCreate,
    DisenoPedidoOut,
    DisenoPedidoUpdate,
    HistorialEstadoPedidoOut,
    ItemPedidoOut,
    PedidoCreate,
    PedidoEstadoIn,
    PedidoOut,
    PedidoUpdate,
)
from app.services.pedidos import ItemPedidoDatos, PedidoService
from app.utils.decimal_policy import money_round

router = APIRouter(prefix="/pedidos", tags=["pedidos"])


def _pedido_out(svc: PedidoService, pedido) -> PedidoOut:  # noqa: ANN001
    pagado = svc.total_pagado(pedido.id)
    saldo = money_round(money_round(pedido.total) - pagado)
    return PedidoOut(
        id=pedido.id,
        numero_pedido=pedido.numero_pedido,
        cliente_id=pedido.cliente_id,
        fecha_pedido=pedido.fecha_pedido,
        fecha_entrega=pedido.fecha_entrega,
        subtotal=pedido.subtotal,
        descuento=pedido.descuento,
        total=pedido.total,
        estado=pedido.estado,
        notas=pedido.notas,
        creado_en=pedido.creado_en,
        actualizado_en=pedido.actualizado_en,
        items=[ItemPedidoOut.model_validate(i) for i in pedido.items],
        total_pagado=pagado,
        saldo_pendiente=saldo,
    )


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def crear(payload: PedidoCreate, db: Session = Depends(get_db)):
    items = [
        ItemPedidoDatos(
            producto_id=i.producto_id,
            variante_id=i.variante_id,
            descripcion=i.descripcion,
            cantidad=i.cantidad,
            precio_venta_unitario=i.precio_venta_unitario,
        )
        for i in payload.items
    ]
    svc = PedidoService(db)
    pedido = svc.crear(
        cliente_id=payload.cliente_id,
        items=items,
        numero_pedido=payload.numero_pedido,
        fecha_pedido=payload.fecha_pedido,
        fecha_entrega=payload.fecha_entrega,
        descuento=payload.descuento,
        notas=payload.notas,
    )
    return _pedido_out(svc, pedido)


@router.get("", response_model=list[PedidoOut])
def listar(
    cliente_id: int | None = None,
    estado: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    svc = PedidoService(db)
    pedidos = svc.listar(
        cliente_id=cliente_id, estado=estado, offset=offset, limit=limit
    )
    return [_pedido_out(svc, svc.obtener(p.id)) for p in pedidos]


@router.get("/{pedido_id}", response_model=PedidoOut)
def obtener(pedido_id: int, db: Session = Depends(get_db)):
    svc = PedidoService(db)
    return _pedido_out(svc, svc.obtener(pedido_id))


@router.patch("/{pedido_id}", response_model=PedidoOut)
def actualizar(
    pedido_id: int, payload: PedidoUpdate, db: Session = Depends(get_db)
):
    svc = PedidoService(db)
    pedido = svc.actualizar(
        pedido_id, **payload.model_dump(exclude_unset=True)
    )
    return _pedido_out(svc, pedido)


@router.post("/{pedido_id}/estado", response_model=PedidoOut)
def cambiar_estado(
    pedido_id: int, payload: PedidoEstadoIn, db: Session = Depends(get_db)
):
    svc = PedidoService(db)
    pedido = svc.cambiar_estado(
        pedido_id,
        estado_nuevo=payload.estado_nuevo.value,
        notas=payload.notas,
        bodega_id=payload.bodega_id,
    )
    return _pedido_out(svc, pedido)


@router.post("/{pedido_id}/cancelar", response_model=PedidoOut)
def cancelar(
    pedido_id: int,
    notas: str | None = None,
    db: Session = Depends(get_db),
):
    svc = PedidoService(db)
    return _pedido_out(svc, svc.cancelar(pedido_id, notas=notas))


@router.get(
    "/{pedido_id}/historial-estados",
    response_model=list[HistorialEstadoPedidoOut],
)
def historial(pedido_id: int, db: Session = Depends(get_db)):
    return PedidoService(db).listar_historial(pedido_id)


@router.get("/{pedido_id}/saldo")
def saldo(pedido_id: int, db: Session = Depends(get_db)):
    svc = PedidoService(db)
    pedido = svc.obtener(pedido_id)
    pagado = svc.total_pagado(pedido_id)
    return {
        "pedido_id": pedido_id,
        "total": str(money_round(pedido.total)),
        "total_pagado": str(pagado),
        "saldo_pendiente": str(
            money_round(money_round(pedido.total) - pagado)
        ),
    }


@router.post(
    "/{pedido_id}/disenos",
    response_model=DisenoPedidoOut,
    status_code=status.HTTP_201_CREATED,
)
def agregar_diseno(
    pedido_id: int, payload: DisenoPedidoCreate, db: Session = Depends(get_db)
):
    svc = PedidoService(db)
    pedido = svc.obtener(pedido_id)
    item_ids = {i.id for i in pedido.items}
    if payload.item_pedido_id not in item_ids:
        raise ValidacionError(
            "item_pedido_id no pertenece al pedido indicado"
        )
    return svc.agregar_diseno(
        item_pedido_id=payload.item_pedido_id,
        ruta_archivo=payload.ruta_archivo,
        estado_aprobacion=payload.estado_aprobacion.value,
        notas=payload.notas,
        version=payload.version,
    )


@router.get("/{pedido_id}/disenos", response_model=list[DisenoPedidoOut])
def listar_disenos(pedido_id: int, db: Session = Depends(get_db)):
    return PedidoService(db).listar_disenos(pedido_id=pedido_id)


@router.patch(
    "/disenos/{diseno_id}",
    response_model=DisenoPedidoOut,
)
def actualizar_diseno(
    diseno_id: int, payload: DisenoPedidoUpdate, db: Session = Depends(get_db)
):
    data = payload.model_dump(exclude_unset=True)
    if "estado_aprobacion" in data and data["estado_aprobacion"] is not None:
        data["estado_aprobacion"] = payload.estado_aprobacion.value  # type: ignore[union-attr]
    return PedidoService(db).actualizar_diseno(diseno_id, **data)
