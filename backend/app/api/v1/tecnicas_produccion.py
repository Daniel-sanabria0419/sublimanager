"""CRUD `/api/v1/tecnicas-produccion`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.productos import (
    TecnicaProduccionCreate,
    TecnicaProduccionOut,
    TecnicaProduccionUpdate,
)
from app.services.productos import TecnicaProduccionService

router = APIRouter(prefix="/tecnicas-produccion", tags=["tecnicas-produccion"])


@router.post(
    "", response_model=TecnicaProduccionOut, status_code=status.HTTP_201_CREATED
)
def crear(payload: TecnicaProduccionCreate, db: Session = Depends(get_db)):
    return TecnicaProduccionService(db).crear(**payload.model_dump())


@router.get("", response_model=list[TecnicaProduccionOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return TecnicaProduccionService(db).listar(
        activo=activo, offset=offset, limit=limit
    )


@router.get("/{tecnica_id}", response_model=TecnicaProduccionOut)
def obtener(tecnica_id: int, db: Session = Depends(get_db)):
    return TecnicaProduccionService(db).obtener(tecnica_id)


@router.patch("/{tecnica_id}", response_model=TecnicaProduccionOut)
def actualizar(
    tecnica_id: int,
    payload: TecnicaProduccionUpdate,
    db: Session = Depends(get_db),
):
    return TecnicaProduccionService(db).actualizar(
        tecnica_id, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{tecnica_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(tecnica_id: int, db: Session = Depends(get_db)):
    TecnicaProduccionService(db).eliminar(tecnica_id)
