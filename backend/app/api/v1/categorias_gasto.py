"""CRUD `/api/v1/categorias-gasto`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finanzas import (
    CategoriaGastoCreate,
    CategoriaGastoOut,
    CategoriaGastoUpdate,
)
from app.services.gastos import CategoriaGastoService

router = APIRouter(prefix="/categorias-gasto", tags=["categorias-gasto"])


@router.post("", response_model=CategoriaGastoOut, status_code=status.HTTP_201_CREATED)
def crear(payload: CategoriaGastoCreate, db: Session = Depends(get_db)):
    return CategoriaGastoService(db).crear(**payload.model_dump())


@router.get("", response_model=list[CategoriaGastoOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CategoriaGastoService(db).listar(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{categoria_id}", response_model=CategoriaGastoOut)
def obtener(categoria_id: int, db: Session = Depends(get_db)):
    return CategoriaGastoService(db).obtener(categoria_id)


@router.patch("/{categoria_id}", response_model=CategoriaGastoOut)
def actualizar(
    categoria_id: int,
    payload: CategoriaGastoUpdate,
    db: Session = Depends(get_db),
):
    return CategoriaGastoService(db).actualizar(
        categoria_id, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(categoria_id: int, db: Session = Depends(get_db)):
    CategoriaGastoService(db).eliminar(categoria_id)
