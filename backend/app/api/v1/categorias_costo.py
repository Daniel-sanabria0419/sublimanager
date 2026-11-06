"""CRUD `/api/v1/categorias-costo`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recetas import (
    CategoriaCostoCreate,
    CategoriaCostoOut,
    CategoriaCostoUpdate,
)
from app.services.recetas import CategoriaCostoService

router = APIRouter(prefix="/categorias-costo", tags=["categorias-costo"])


@router.post("", response_model=CategoriaCostoOut, status_code=status.HTTP_201_CREATED)
def crear(payload: CategoriaCostoCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["tipo_costo"] = payload.tipo_costo.value
    return CategoriaCostoService(db).crear(**data)


@router.get("", response_model=list[CategoriaCostoOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return CategoriaCostoService(db).listar(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{categoria_id}", response_model=CategoriaCostoOut)
def obtener(categoria_id: int, db: Session = Depends(get_db)):
    return CategoriaCostoService(db).obtener(categoria_id)


@router.patch("/{categoria_id}", response_model=CategoriaCostoOut)
def actualizar(
    categoria_id: int,
    payload: CategoriaCostoUpdate,
    db: Session = Depends(get_db),
):
    data = payload.model_dump(exclude_unset=True)
    if "tipo_costo" in data and data["tipo_costo"] is not None:
        data["tipo_costo"] = payload.tipo_costo.value  # type: ignore[union-attr]
    return CategoriaCostoService(db).actualizar(categoria_id, **data)


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(categoria_id: int, db: Session = Depends(get_db)):
    CategoriaCostoService(db).eliminar(categoria_id)
