"""API `/api/v1/gastos` — gastos operativos y estado_pago."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import GastoCreate, GastoOut, GastoUpdate
from app.services.gastos import GastoService

router = APIRouter(prefix="/gastos", tags=["gastos"])


def _gasto_out(svc: GastoService, gasto) -> GastoOut:
    pagado, saldo = svc.detalle_saldos(gasto)
    data = GastoOut.model_validate(gasto)
    return data.model_copy(
        update={"total_pagado": pagado, "saldo_pendiente": saldo}
    )


@router.post("", response_model=GastoOut, status_code=status.HTTP_201_CREATED)
def crear(payload: GastoCreate, db: Session = Depends(get_db)):
    svc = GastoService(db)
    gasto = svc.crear(**payload.model_dump())
    return _gasto_out(svc, gasto)


@router.get("", response_model=list[GastoOut])
def listar(
    categoria_id: int | None = None,
    estado_pago: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    svc = GastoService(db)
    return [
        _gasto_out(svc, g)
        for g in svc.listar(
            categoria_id=categoria_id,
            estado_pago=estado_pago,
            offset=offset,
            limit=limit,
        )
    ]


@router.get("/{gasto_id}", response_model=GastoOut)
def obtener(gasto_id: int, db: Session = Depends(get_db)):
    svc = GastoService(db)
    return _gasto_out(svc, svc.obtener(gasto_id))


@router.patch("/{gasto_id}", response_model=GastoOut)
def actualizar(
    gasto_id: int, payload: GastoUpdate, db: Session = Depends(get_db)
):
    svc = GastoService(db)
    gasto = svc.actualizar(gasto_id, **payload.model_dump(exclude_unset=True))
    return _gasto_out(svc, gasto)


@router.post("/{gasto_id}/anular", response_model=GastoOut)
def anular(gasto_id: int, db: Session = Depends(get_db)):
    svc = GastoService(db)
    return _gasto_out(svc, svc.anular(gasto_id))
