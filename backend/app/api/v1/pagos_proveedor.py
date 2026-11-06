"""API `/api/v1/pagos-proveedor` — pagos parciales ligados a compras."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import PagoProveedorCreate, PagoProveedorOut, SaldoCompraOut
from app.services.pagos_proveedor import PagoProveedorService
from app.utils.decimal_policy import money_round

router = APIRouter(prefix="/pagos-proveedor", tags=["pagos-proveedor"])


@router.post("", response_model=PagoProveedorOut, status_code=status.HTTP_201_CREATED)
def registrar(payload: PagoProveedorCreate, db: Session = Depends(get_db)):
    return PagoProveedorService(db).registrar(
        compra_id=payload.compra_id,
        metodo_pago_id=payload.metodo_pago_id,
        cuenta_caja_id=payload.cuenta_caja_id,
        monto=payload.monto,
        referencia=payload.referencia,
        confirmar=payload.confirmar,
        fecha_pago=payload.fecha_pago,
    )


@router.get("", response_model=list[PagoProveedorOut])
def listar(
    compra_id: int = Query(..., description="Filtrar por compra"),
    estado: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return PagoProveedorService(db).listar_por_compra(
        compra_id, estado=estado, offset=offset, limit=limit
    )


@router.get("/saldo/{compra_id}", response_model=SaldoCompraOut)
def saldo_compra(compra_id: int, db: Session = Depends(get_db)):
    svc = PagoProveedorService(db)
    compra = svc.compras.obtener_o_404(compra_id, "compra")
    pagado = money_round(svc.pagos.suma_confirmados_compra(compra_id))
    total = money_round(compra.total)
    return SaldoCompraOut(
        compra_id=compra_id,
        total=total,
        total_pagado=pagado,
        saldo_pendiente=money_round(total - pagado),
    )


@router.get("/{pago_id}", response_model=PagoProveedorOut)
def obtener(pago_id: int, db: Session = Depends(get_db)):
    return PagoProveedorService(db).obtener(pago_id)


@router.post("/{pago_id}/confirmar", response_model=PagoProveedorOut)
def confirmar(pago_id: int, db: Session = Depends(get_db)):
    return PagoProveedorService(db).confirmar(pago_id)


@router.post("/{pago_id}/anular", response_model=PagoProveedorOut)
def anular(pago_id: int, db: Session = Depends(get_db)):
    return PagoProveedorService(db).anular(pago_id)
