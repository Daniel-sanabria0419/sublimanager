"""CRUD `/api/v1/categorias-material`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.inventario import (
    CategoriaMaterialCreate,
    CategoriaMaterialOut,
    CategoriaMaterialUpdate,
)
from app.services.inventario import CatalogoInventarioService

router = APIRouter(prefix="/categorias-material", tags=["categorias-material"])


@router.post("", response_model=CategoriaMaterialOut, status_code=status.HTTP_201_CREATED)
def crear(payload: CategoriaMaterialCreate, db: Session = Depends(get_db)):
    return CatalogoInventarioService(db).crear_categoria(**payload.model_dump())


@router.get("", response_model=list[CategoriaMaterialOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CatalogoInventarioService(db).listar_categorias(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{categoria_id}", response_model=CategoriaMaterialOut)
def obtener(categoria_id: int, db: Session = Depends(get_db)):
    return CatalogoInventarioService(db).obtener_categoria(categoria_id)


@router.patch("/{categoria_id}", response_model=CategoriaMaterialOut)
def actualizar(
    categoria_id: int,
    payload: CategoriaMaterialUpdate,
    db: Session = Depends(get_db),
):
    return CatalogoInventarioService(db).actualizar_categoria(
        categoria_id, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(categoria_id: int, db: Session = Depends(get_db)):
    CatalogoInventarioService(db).eliminar_categoria(categoria_id)
