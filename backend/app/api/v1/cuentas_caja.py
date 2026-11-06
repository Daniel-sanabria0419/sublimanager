"""CRUD `/api/v1/cuentas-caja` + saldo."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import (
    CuentaCajaCreate,
    CuentaCajaOut,
    CuentaCajaSaldoOut,
    CuentaCajaUpdate,
)
from app.services.caja import CajaService
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


@router.get("/saldos", response_model=list[CuentaCajaSaldoOut])
def saldos(db: Session = Depends(get_db)):
    return CajaService(db).saldos_todas_las_cuentas()


@router.get("/{cuenta_id}", response_model=CuentaCajaOut)
def obtener(cuenta_id: int, db: Session = Depends(get_db)):
    return CuentaCajaService(db).obtener(cuenta_id)


@router.get("/{cuenta_id}/saldo", response_model=CuentaCajaSaldoOut)
def saldo(cuenta_id: int, db: Session = Depends(get_db)):
    return CajaService(db).saldo_cuenta(cuenta_id)


@router.patch("/{cuenta_id}", response_model=CuentaCajaOut)
def actualizar(
    cuenta_id: int, payload: CuentaCajaUpdate, db: Session = Depends(get_db)
):
    data = payload.model_dump(exclude_unset=True)
    if "tipo_cuenta" in data and data["tipo_cuenta"] is not None:
        data["tipo_cuenta"] = payload.tipo_cuenta.value  # type: ignore[union-attr]
    return CuentaCajaService(db).actualizar(cuenta_id, **data)


@router.delete("/{cuenta_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(cuenta_id: int, db: Session = Depends(get_db)):
    CuentaCajaService(db).eliminar(cuenta_id)
