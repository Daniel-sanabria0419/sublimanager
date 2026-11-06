"""CRUD mínimo `/api/v1/metodos-pago` (soporte anticipos Stage 5)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import MetodoPagoCreate, MetodoPagoOut
from app.services.pagos import MetodoPagoService

router = APIRouter(prefix="/metodos-pago", tags=["metodos-pago"])


@router.post("", response_model=MetodoPagoOut, status_code=status.HTTP_201_CREATED)
def crear(payload: MetodoPagoCreate, db: Session = Depends(get_db)):
    return MetodoPagoService(db).crear(**payload.model_dump())


@router.get("", response_model=list[MetodoPagoOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return MetodoPagoService(db).listar(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{metodo_id}", response_model=MetodoPagoOut)
def obtener(metodo_id: int, db: Session = Depends(get_db)):
    return MetodoPagoService(db).obtener(metodo_id)
