"""Consultas `/api/v1/existencias`."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.inventario import ExistenciaOut
from app.services.inventario import ExistenciaService

router = APIRouter(prefix="/existencias", tags=["existencias"])


@router.get("", response_model=list[ExistenciaOut])
def listar(
    bodega_id: int | None = None,
    material_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return ExistenciaService(db).listar(
        bodega_id=bodega_id,
        material_id=material_id,
        offset=offset,
        limit=limit,
    )


@router.get("/{existencia_id}", response_model=ExistenciaOut)
def obtener(existencia_id: int, db: Session = Depends(get_db)):
    return ExistenciaService(db).obtener(existencia_id)
