"""CRUD `/api/v1/bodegas`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.inventario import BodegaCreate, BodegaOut, BodegaUpdate
from app.services.inventario import CatalogoInventarioService

router = APIRouter(prefix="/bodegas", tags=["bodegas"])


@router.post("", response_model=BodegaOut, status_code=status.HTTP_201_CREATED)
def crear(payload: BodegaCreate, db: Session = Depends(get_db)):
    return CatalogoInventarioService(db).crear_bodega(**payload.model_dump())


@router.get("", response_model=list[BodegaOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CatalogoInventarioService(db).listar_bodegas(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{bodega_id}", response_model=BodegaOut)
def obtener(bodega_id: int, db: Session = Depends(get_db)):
    return CatalogoInventarioService(db).obtener_bodega(bodega_id)


@router.patch("/{bodega_id}", response_model=BodegaOut)
def actualizar(
    bodega_id: int, payload: BodegaUpdate, db: Session = Depends(get_db)
):
    return CatalogoInventarioService(db).actualizar_bodega(
        bodega_id, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{bodega_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(bodega_id: int, db: Session = Depends(get_db)):
    CatalogoInventarioService(db).eliminar_bodega(bodega_id)
