"""CRUD `/api/v1/variantes-producto`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.productos import (
    VarianteProductoCreate,
    VarianteProductoOut,
    VarianteProductoUpdate,
)
from app.services.productos import VarianteProductoService

router = APIRouter(prefix="/variantes-producto", tags=["variantes-producto"])


@router.post(
    "", response_model=VarianteProductoOut, status_code=status.HTTP_201_CREATED
)
def crear(payload: VarianteProductoCreate, db: Session = Depends(get_db)):
    return VarianteProductoService(db).crear(**payload.model_dump())


@router.get("", response_model=list[VarianteProductoOut])
def listar(
    producto_id: int | None = None,
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return VarianteProductoService(db).listar(
        producto_id=producto_id, activo=activo, offset=offset, limit=limit
    )


@router.get("/{variante_id}", response_model=VarianteProductoOut)
def obtener(variante_id: int, db: Session = Depends(get_db)):
    return VarianteProductoService(db).obtener(variante_id)


@router.patch("/{variante_id}", response_model=VarianteProductoOut)
def actualizar(
    variante_id: int,
    payload: VarianteProductoUpdate,
    db: Session = Depends(get_db),
):
    return VarianteProductoService(db).actualizar(
        variante_id, **payload.model_dump(exclude_unset=True)
    )
