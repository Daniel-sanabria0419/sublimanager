"""API mínima `/api/v1/pagos` — anticipos y saldo de pedidos (Stage 5)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import PagoCreate, PagoOut
from app.services.pagos import PagoService

router = APIRouter(prefix="/pagos", tags=["pagos"])


@router.post("", response_model=PagoOut, status_code=status.HTTP_201_CREATED)
def registrar(payload: PagoCreate, db: Session = Depends(get_db)):
    return PagoService(db).registrar(
        pedido_id=payload.pedido_id,
        metodo_pago_id=payload.metodo_pago_id,
        cuenta_caja_id=payload.cuenta_caja_id,
        monto=payload.monto,
        referencia=payload.referencia,
        notas=payload.notas,
        confirmar=payload.confirmar,
        fecha_pago=payload.fecha_pago,
    )


@router.get("", response_model=list[PagoOut])
def listar(
    pedido_id: int = Query(..., description="Filtrar por pedido"),
    estado: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return PagoService(db).listar_por_pedido(
        pedido_id, estado=estado, offset=offset, limit=limit
    )


@router.get("/{pago_id}", response_model=PagoOut)
def obtener(pago_id: int, db: Session = Depends(get_db)):
    return PagoService(db).obtener(pago_id)


@router.post("/{pago_id}/confirmar", response_model=PagoOut)
def confirmar(pago_id: int, db: Session = Depends(get_db)):
    return PagoService(db).confirmar(pago_id)


@router.post("/{pago_id}/anular", response_model=PagoOut)
def anular(pago_id: int, db: Session = Depends(get_db)):
    return PagoService(db).anular(pago_id)
