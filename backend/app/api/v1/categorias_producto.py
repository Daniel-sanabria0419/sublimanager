"""CRUD `/api/v1/categorias-producto`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.productos import (
    CategoriaProductoCreate,
    CategoriaProductoOut,
    CategoriaProductoUpdate,
)
from app.services.productos import CategoriaProductoService

router = APIRouter(prefix="/categorias-producto", tags=["categorias-producto"])


@router.post("", response_model=CategoriaProductoOut, status_code=status.HTTP_201_CREATED)
def crear(payload: CategoriaProductoCreate, db: Session = Depends(get_db)):
    return CategoriaProductoService(db).crear(**payload.model_dump())


@router.get("", response_model=list[CategoriaProductoOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CategoriaProductoService(db).listar(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{categoria_id}", response_model=CategoriaProductoOut)
def obtener(categoria_id: int, db: Session = Depends(get_db)):
    return CategoriaProductoService(db).obtener(categoria_id)


@router.patch("/{categoria_id}", response_model=CategoriaProductoOut)
def actualizar(
    categoria_id: int,
    payload: CategoriaProductoUpdate,
    db: Session = Depends(get_db),
):
    return CategoriaProductoService(db).actualizar(
        categoria_id, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(categoria_id: int, db: Session = Depends(get_db)):
    CategoriaProductoService(db).eliminar(categoria_id)
