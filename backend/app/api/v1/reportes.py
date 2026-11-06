"""API `/api/v1/reportes` — reportes, dashboard y exportación (Stage 9)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ValidacionError
from app.schemas.reportes import (
    CompraReporteOut,
    ConsumoMaterialOut,
    CostoCategoriaOut,
    CostoProduccionOut,
    CuentasPendientesOut,
    DashboardOut,
    DesperdicioOut,
    GastoReporteOut,
    InventarioValorizadoOut,
    ProductoMasVendidoOut,
    RentabilidadPedidoOut,
    UtilidadProductoOut,
    VentaDiariaOut,
    VentaMensualOut,
)
from app.services.reportes import ReportesService

router = APIRouter(prefix="/reportes", tags=["reportes"])

TipoExport = Literal[
    "ventas",
    "inventario-valorizado",
    "rentabilidad-pedidos",
    "resumen-financiero",
]
FormatoExport = Literal["csv", "pdf"]


def _svc(db: Session) -> ReportesService:
    return ReportesService(db)


@router.get("/ventas/diarias", response_model=list[VentaDiariaOut])
def ventas_diarias(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    return _svc(db).ventas_diarias(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)


@router.get("/ventas/mensuales", response_model=list[VentaMensualOut])
def ventas_mensuales(
    anio: int | None = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
):
    return _svc(db).ventas_mensuales(anio=anio)


@router.get("/productos-mas-vendidos", response_model=list[ProductoMasVendidoOut])
def productos_mas_vendidos(
    limite: int = Query(default=20, ge=1, le=100),
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    return _svc(db).productos_mas_vendidos(
        limite=limite, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )


@router.get("/utilidad-por-producto", response_model=list[UtilidadProductoOut])
def utilidad_por_producto(
    limite: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return _svc(db).utilidad_por_producto(limite=limite)


@router.get("/rentabilidad-pedidos", response_model=list[RentabilidadPedidoOut])
def rentabilidad_pedidos(
    limite: int = Query(default=100, ge=1, le=500),
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    return _svc(db).rentabilidad_pedidos(
        limite=limite, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta
    )


@router.get("/costos-produccion", response_model=list[CostoProduccionOut])
def costos_produccion(
    etapa: str | None = Query(default=None, pattern="^(ESTIMADO|REAL)$"),
    db: Session = Depends(get_db),
):
    return _svc(db).costos_produccion(etapa=etapa)


@router.get("/costos-por-categoria", response_model=list[CostoCategoriaOut])
def costos_por_categoria(
    etapa: str = Query(default="REAL", pattern="^(ESTIMADO|REAL)$"),
    db: Session = Depends(get_db),
):
    return _svc(db).costos_por_categoria(etapa=etapa)


@router.get("/compras", response_model=list[CompraReporteOut])
def reporte_compras(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    return _svc(db).compras(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)


@router.get("/gastos", response_model=list[GastoReporteOut])
def reporte_gastos(
    fecha_desde: date | None = None,
    fecha_hasta: date | None = None,
    db: Session = Depends(get_db),
):
    return _svc(db).gastos(fecha_desde=fecha_desde, fecha_hasta=fecha_hasta)


@router.get("/inventario-valorizado", response_model=list[InventarioValorizadoOut])
def inventario_valorizado(db: Session = Depends(get_db)):
    return _svc(db).inventario_valorizado()


@router.get("/consumo-materiales", response_model=list[ConsumoMaterialOut])
def consumo_materiales(db: Session = Depends(get_db)):
    return _svc(db).consumo_materiales()


@router.get("/desperdicios", response_model=list[DesperdicioOut])
def desperdicios(db: Session = Depends(get_db)):
    return _svc(db).desperdicios()


@router.get("/cuentas-pendientes", response_model=CuentasPendientesOut)
def cuentas_pendientes(db: Session = Depends(get_db)):
    """Wrapper de CxC/CxP Stage 7 para el módulo de reportes."""
    return _svc(db).cuentas_pendientes()


@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    return _svc(db).dashboard()


@router.get("/export/{tipo}")
def exportar_reporte(
    tipo: TipoExport,
    formato: FormatoExport = Query(default="csv"),
    db: Session = Depends(get_db),
):
    """Exporta reportes clave a CSV o PDF.

    Tipos: `ventas`, `inventario-valorizado`, `rentabilidad-pedidos`,
    `resumen-financiero`.
    """
    try:
        content, media, filename = _svc(db).exportar(tipo, formato=formato)
    except ValueError as exc:
        raise ValidacionError(str(exc)) from exc
    return Response(
        content=content,
        media_type=media,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
