"""API `/api/v1/movimientos-caja` — consulta de movimientos generados por pagos."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import MovimientoCajaOut
from app.services.caja import CajaService

router = APIRouter(prefix="/movimientos-caja", tags=["movimientos-caja"])


@router.get("", response_model=list[MovimientoCajaOut])
def listar(
    cuenta_caja_id: int | None = None,
    tipo_movimiento: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CajaService(db).listar_movimientos(
        cuenta_caja_id=cuenta_caja_id,
        tipo_movimiento=tipo_movimiento,
        offset=offset,
        limit=limit,
    )


@router.get("/{movimiento_id}", response_model=MovimientoCajaOut)
def obtener(movimiento_id: int, db: Session = Depends(get_db)):
    return CajaService(db).obtener_movimiento(movimiento_id)
