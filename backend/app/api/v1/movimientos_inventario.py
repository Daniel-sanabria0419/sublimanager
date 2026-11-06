"""API `/api/v1/movimientos-inventario`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.inventario import (
    MovimientoInventarioCreate,
    MovimientoInventarioOut,
    TransferenciaCreate,
    TransferenciaOut,
)
from app.services.inventario import ItemMovimientoDatos, MovimientoInventarioService

router = APIRouter(prefix="/movimientos-inventario", tags=["movimientos-inventario"])


def _items(payload_items) -> list[ItemMovimientoDatos]:
    return [
        ItemMovimientoDatos(
            material_id=i.material_id,
            variante_producto_id=i.variante_producto_id,
            cantidad=i.cantidad,
            costo_unitario=i.costo_unitario,
        )
        for i in payload_items
    ]


@router.post(
    "", response_model=MovimientoInventarioOut, status_code=status.HTTP_201_CREATED
)
def crear(payload: MovimientoInventarioCreate, db: Session = Depends(get_db)):
    svc = MovimientoInventarioService(db)
    items = _items(payload.items)
    if payload.confirmar:
        return svc.crear_y_confirmar(
            tipo_movimiento=payload.tipo_movimiento,
            bodega_id=payload.bodega_id,
            items=items,
            notas=payload.notas,
            tipo_referencia=payload.tipo_referencia,
            referencia_id=payload.referencia_id,
        )
    return svc.crear_borrador(
        tipo_movimiento=payload.tipo_movimiento,
        bodega_id=payload.bodega_id,
        items=items,
        notas=payload.notas,
        tipo_referencia=payload.tipo_referencia,
        referencia_id=payload.referencia_id,
    )


@router.post(
    "/transferencias",
    response_model=TransferenciaOut,
    status_code=status.HTTP_201_CREATED,
)
def transferir(payload: TransferenciaCreate, db: Session = Depends(get_db)):
    salida, entrada = MovimientoInventarioService(db).transferir(
        bodega_origen_id=payload.bodega_origen_id,
        bodega_destino_id=payload.bodega_destino_id,
        items=_items(payload.items),
        notas=payload.notas,
    )
    assert salida.grupo_transferencia_id is not None
    return TransferenciaOut(
        grupo_transferencia_id=salida.grupo_transferencia_id,
        salida=MovimientoInventarioOut.model_validate(salida),
        entrada=MovimientoInventarioOut.model_validate(entrada),
    )


@router.get("", response_model=list[MovimientoInventarioOut])
def listar(
    bodega_id: int | None = None,
    tipo_movimiento: str | None = None,
    estado: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return MovimientoInventarioService(db).listar(
        bodega_id=bodega_id,
        tipo_movimiento=tipo_movimiento,
        estado=estado,
        offset=offset,
        limit=limit,
    )


@router.get("/{movimiento_id}", response_model=MovimientoInventarioOut)
def obtener(movimiento_id: int, db: Session = Depends(get_db)):
    return MovimientoInventarioService(db).obtener(movimiento_id)


@router.post("/{movimiento_id}/confirmar", response_model=MovimientoInventarioOut)
def confirmar(movimiento_id: int, db: Session = Depends(get_db)):
    return MovimientoInventarioService(db).confirmar(movimiento_id)
