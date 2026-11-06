"""API `/api/v1/pagos-gasto` — pagos parciales de gastos operativos."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import PagoGastoCreate, PagoGastoOut
from app.services.gastos import PagoGastoService

router = APIRouter(prefix="/pagos-gasto", tags=["pagos-gasto"])


@router.post("", response_model=PagoGastoOut, status_code=status.HTTP_201_CREATED)
def registrar(payload: PagoGastoCreate, db: Session = Depends(get_db)):
    return PagoGastoService(db).registrar(
        gasto_id=payload.gasto_id,
        metodo_pago_id=payload.metodo_pago_id,
        cuenta_caja_id=payload.cuenta_caja_id,
        monto=payload.monto,
        referencia=payload.referencia,
        confirmar=payload.confirmar,
        fecha_pago=payload.fecha_pago,
    )


@router.get("", response_model=list[PagoGastoOut])
def listar(
    gasto_id: int = Query(..., description="Filtrar por gasto"),
    estado: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return PagoGastoService(db).listar_por_gasto(
        gasto_id, estado=estado, offset=offset, limit=limit
    )


@router.get("/{pago_id}", response_model=PagoGastoOut)
def obtener(pago_id: int, db: Session = Depends(get_db)):
    return PagoGastoService(db).obtener(pago_id)


@router.post("/{pago_id}/confirmar", response_model=PagoGastoOut)
def confirmar(pago_id: int, db: Session = Depends(get_db)):
    return PagoGastoService(db).confirmar(pago_id)


@router.post("/{pago_id}/anular", response_model=PagoGastoOut)
def anular(pago_id: int, db: Session = Depends(get_db)):
    return PagoGastoService(db).anular(pago_id)
