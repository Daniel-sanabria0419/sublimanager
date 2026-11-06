"""CRUD `/api/v1/unidades-medida`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.inventario import (
    UnidadMedidaCreate,
    UnidadMedidaOut,
    UnidadMedidaUpdate,
)
from app.services.inventario import CatalogoInventarioService

router = APIRouter(prefix="/unidades-medida", tags=["unidades-medida"])


@router.post("", response_model=UnidadMedidaOut, status_code=status.HTTP_201_CREATED)
def crear(payload: UnidadMedidaCreate, db: Session = Depends(get_db)):
    return CatalogoInventarioService(db).crear_unidad(**payload.model_dump())


@router.get("", response_model=list[UnidadMedidaOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CatalogoInventarioService(db).listar_unidades(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{unidad_id}", response_model=UnidadMedidaOut)
def obtener(unidad_id: int, db: Session = Depends(get_db)):
    return CatalogoInventarioService(db).obtener_unidad(unidad_id)


@router.patch("/{unidad_id}", response_model=UnidadMedidaOut)
def actualizar(
    unidad_id: int, payload: UnidadMedidaUpdate, db: Session = Depends(get_db)
):
    return CatalogoInventarioService(db).actualizar_unidad(
        unidad_id, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(unidad_id: int, db: Session = Depends(get_db)):
    CatalogoInventarioService(db).eliminar_unidad(unidad_id)
