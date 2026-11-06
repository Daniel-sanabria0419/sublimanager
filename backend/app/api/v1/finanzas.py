"""API `/api/v1/finanzas` — CxC, CxP y resumen financiero (§5.10)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import (
    CuentaPorCobrarOut,
    CuentaPorPagarOut,
    ResumenFinancieroOut,
)
from app.services.caja import CajaService

router = APIRouter(prefix="/finanzas", tags=["finanzas"])


@router.get("/cuentas-por-cobrar", response_model=list[CuentaPorCobrarOut])
def cuentas_por_cobrar(db: Session = Depends(get_db)):
    return CajaService(db).cuentas_por_cobrar()


@router.get("/cuentas-por-pagar", response_model=list[CuentaPorPagarOut])
def cuentas_por_pagar(db: Session = Depends(get_db)):
    return CajaService(db).cuentas_por_pagar()


@router.get("/resumen", response_model=ResumenFinancieroOut)
def resumen(db: Session = Depends(get_db)):
    return CajaService(db).resumen_financiero()
