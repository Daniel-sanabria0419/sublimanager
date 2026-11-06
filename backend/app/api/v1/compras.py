"""API `/api/v1/compras` — borrador, recepción, cancelación."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.compras import (
    CompraCreate,
    CompraOut,
    CompraRecepcionIn,
)
from app.services.compras import CompraService, ItemCompraDatos, RecepcionItemDatos

router = APIRouter(prefix="/compras", tags=["compras"])


@router.post("", response_model=CompraOut, status_code=status.HTTP_201_CREATED)
def crear(payload: CompraCreate, db: Session = Depends(get_db)):
    items = [
        ItemCompraDatos(
            material_id=i.material_id,
            variante_producto_id=i.variante_producto_id,
            cantidad=i.cantidad,
            costo_unitario=i.costo_unitario,
        )
        for i in payload.items
    ]
    return CompraService(db).crear(
        proveedor_id=payload.proveedor_id,
        items=items,
        numero_factura=payload.numero_factura,
        fecha_compra=payload.fecha_compra,
    )


@router.get("", response_model=list[CompraOut])
def listar(
    proveedor_id: int | None = None,
    estado: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CompraService(db).listar(
        proveedor_id=proveedor_id,
        estado=estado,
        offset=offset,
        limit=limit,
    )


@router.get("/{compra_id}", response_model=CompraOut)
def obtener(compra_id: int, db: Session = Depends(get_db)):
    return CompraService(db).obtener(compra_id)


@router.post("/{compra_id}/recibir", response_model=CompraOut)
def recibir(
    compra_id: int, payload: CompraRecepcionIn, db: Session = Depends(get_db)
):
    items = None
    if payload.items is not None:
        items = [
            RecepcionItemDatos(
                item_compra_id=i.item_compra_id, cantidad=i.cantidad
            )
            for i in payload.items
        ]
    return CompraService(db).recibir(
        compra_id,
        bodega_id=payload.bodega_id,
        items=items,
        notas=payload.notas,
    )


@router.post("/{compra_id}/cancelar", response_model=CompraOut)
def cancelar(compra_id: int, db: Session = Depends(get_db)):
    return CompraService(db).cancelar(compra_id)
