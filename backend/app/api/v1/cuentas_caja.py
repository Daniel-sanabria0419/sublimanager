"""CRUD mínimo `/api/v1/cuentas-caja` (soporte anticipos Stage 5)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import CuentaCajaCreate, CuentaCajaOut
from app.services.pagos import CuentaCajaService

router = APIRouter(prefix="/cuentas-caja", tags=["cuentas-caja"])


@router.post("", response_model=CuentaCajaOut, status_code=status.HTTP_201_CREATED)
def crear(payload: CuentaCajaCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["tipo_cuenta"] = payload.tipo_cuenta.value
    return CuentaCajaService(db).crear(**data)


@router.get("", response_model=list[CuentaCajaOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CuentaCajaService(db).listar(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{cuenta_id}", response_model=CuentaCajaOut)
def obtener(cuenta_id: int, db: Session = Depends(get_db)):
    return CuentaCajaService(db).obtener(cuenta_id)
