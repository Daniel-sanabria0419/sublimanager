"""API `/api/v1/ordenes-produccion` — OP desde pedido, consumos, costos, cierre."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.produccion import (
    AsientoCostoCreate,
    AsientoCostoProduccionOut,
    CantidadesProduccionIn,
    ComparacionCostoItemOut,
    ComparacionCostoOrdenOut,
    CompletarOrdenIn,
    ConsumoProduccionCreate,
    ConsumoProduccionOut,
    ItemOrdenProduccionOut,
    MaterialesRequeridosOut,
    MaterialRequeridoOut,
    OrdenProduccionCreate,
    OrdenProduccionOut,
)
from app.services.produccion import (
    AsientoCostoDatos,
    ConsumoDatos,
    ItemOpDatos,
    OrdenProduccionService,
)

router = APIRouter(prefix="/ordenes-produccion", tags=["ordenes-produccion"])


def _item_out(item) -> ItemOrdenProduccionOut:  # noqa: ANN001
    return ItemOrdenProduccionOut(
        id=item.id,
        orden_produccion_id=item.orden_produccion_id,
        item_pedido_id=item.item_pedido_id,
        cantidad_planificada=item.cantidad_planificada,
        cantidad_producida=item.cantidad_producida,
        cantidad_rechazada=item.cantidad_rechazada,
        consumos=[ConsumoProduccionOut.model_validate(c) for c in item.consumos],
        asientos_costo=[
            AsientoCostoProduccionOut.model_validate(a) for a in item.asientos_costo
        ],
    )


def _op_out(op) -> OrdenProduccionOut:  # noqa: ANN001
    return OrdenProduccionOut(
        id=op.id,
        pedido_id=op.pedido_id,
        numero_produccion=op.numero_produccion,
        estado=op.estado,
        fecha_inicio=op.fecha_inicio,
        fecha_fin=op.fecha_fin,
        notas=op.notas,
        items=[_item_out(i) for i in op.items],
    )


@router.post("", response_model=OrdenProduccionOut, status_code=status.HTTP_201_CREATED)
def crear(payload: OrdenProduccionCreate, db: Session = Depends(get_db)):
    items = [
        ItemOpDatos(
            item_pedido_id=i.item_pedido_id,
            cantidad_planificada=i.cantidad_planificada,
        )
        for i in payload.items
    ]
    op = OrdenProduccionService(db).crear(
        pedido_id=payload.pedido_id,
        items=items,
        numero_produccion=payload.numero_produccion,
        notas=payload.notas,
        bodega_id=payload.bodega_id,
    )
    return _op_out(op)


@router.get("", response_model=list[OrdenProduccionOut])
def listar(
    pedido_id: int | None = None,
    estado: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    svc = OrdenProduccionService(db)
    ordenes = svc.listar(
        pedido_id=pedido_id, estado=estado, offset=offset, limit=limit
    )
    return [_op_out(svc.obtener(o.id)) for o in ordenes]


@router.get("/{orden_id}", response_model=OrdenProduccionOut)
def obtener(orden_id: int, db: Session = Depends(get_db)):
    return _op_out(OrdenProduccionService(db).obtener(orden_id))


@router.get("/{orden_id}/materiales-requeridos", response_model=MaterialesRequeridosOut)
def materiales_requeridos(
    orden_id: int,
    bodega_id: int = Query(...),
    db: Session = Depends(get_db),
):
    filas, todos = OrdenProduccionService(db).materiales_requeridos(
        orden_id, bodega_id=bodega_id
    )
    return MaterialesRequeridosOut(
        orden_produccion_id=orden_id,
        bodega_id=bodega_id,
        materiales=[MaterialRequeridoOut(**f.__dict__) for f in filas],
        todos_suficientes=todos,
    )


@router.post("/{orden_id}/iniciar", response_model=OrdenProduccionOut)
def iniciar(orden_id: int, db: Session = Depends(get_db)):
    return _op_out(OrdenProduccionService(db).iniciar(orden_id))


@router.post("/{orden_id}/cancelar", response_model=OrdenProduccionOut)
def cancelar(orden_id: int, db: Session = Depends(get_db)):
    return _op_out(OrdenProduccionService(db).cancelar(orden_id))


@router.post("/{orden_id}/completar", response_model=OrdenProduccionOut)
def completar(
    orden_id: int,
    payload: CompletarOrdenIn | None = None,
    db: Session = Depends(get_db),
):
    bodega = payload.bodega_producto_id if payload is not None else None
    return _op_out(
        OrdenProduccionService(db).completar(
            orden_id, bodega_producto_id=bodega
        )
    )


@router.post(
    "/{orden_id}/items/{item_id}/consumos",
    response_model=ConsumoProduccionOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_consumo(
    orden_id: int,
    item_id: int,
    payload: ConsumoProduccionCreate,
    bodega_id: int = Query(...),
    db: Session = Depends(get_db),
):
    consumo = OrdenProduccionService(db).registrar_consumo(
        orden_id,
        item_id,
        bodega_id=bodega_id,
        datos=ConsumoDatos(
            material_id=payload.material_id,
            cantidad_consumida=payload.cantidad_consumida,
            es_desperdicio=payload.es_desperdicio,
            notas=payload.notas,
            costo_unitario_snapshot=payload.costo_unitario_snapshot,
        ),
    )
    return ConsumoProduccionOut.model_validate(consumo)


@router.post(
    "/{orden_id}/items/{item_id}/asientos-costo",
    response_model=AsientoCostoProduccionOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar_asiento(
    orden_id: int,
    item_id: int,
    payload: AsientoCostoCreate,
    db: Session = Depends(get_db),
):
    asiento = OrdenProduccionService(db).registrar_asiento_costo(
        orden_id,
        item_id,
        datos=AsientoCostoDatos(
            categoria_costo_id=payload.categoria_costo_id,
            costo_unitario=payload.costo_unitario,
            cantidad=payload.cantidad,
            descripcion=payload.descripcion,
            gasto_id=payload.gasto_id,
            etapa_costo=payload.etapa_costo.value,
        ),
    )
    return AsientoCostoProduccionOut.model_validate(asiento)


@router.post(
    "/{orden_id}/items/{item_id}/cantidades",
    response_model=ItemOrdenProduccionOut,
)
def registrar_cantidades(
    orden_id: int,
    item_id: int,
    payload: CantidadesProduccionIn,
    db: Session = Depends(get_db),
):
    item = OrdenProduccionService(db).registrar_cantidades(
        orden_id,
        item_id,
        cantidad_producida=payload.cantidad_producida,
        cantidad_rechazada=payload.cantidad_rechazada,
        bodega_producto_id=payload.bodega_producto_id,
    )
    return _item_out(item)


@router.get("/{orden_id}/comparacion-costos", response_model=ComparacionCostoOrdenOut)
def comparacion_costos(orden_id: int, db: Session = Depends(get_db)):
    cmp_ = OrdenProduccionService(db).comparar_costos(orden_id)
    return ComparacionCostoOrdenOut(
        orden_produccion_id=cmp_.orden_produccion_id,
        items=[
            ComparacionCostoItemOut(
                item_orden_produccion_id=i.item_orden_produccion_id,
                item_pedido_id=i.item_pedido_id,
                costo_estimado_total=i.costo_estimado_total,
                costo_real_total=i.costo_real_total,
                diferencia=i.diferencia,
                estimado_por_tipo=i.estimado_por_tipo,
                real_por_tipo=i.real_por_tipo,
                costo_materiales_consumos=i.costo_materiales_consumos,
            )
            for i in cmp_.items
        ],
        costo_estimado_total=cmp_.costo_estimado_total,
        costo_real_total=cmp_.costo_real_total,
        diferencia=cmp_.diferencia,
    )
