"""Vínculos `/api/v1/tecnicas-producto` (producto × técnica, unique)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.productos import TecnicaProductoCreate, TecnicaProductoOut
from app.services.productos import TecnicaProductoService

router = APIRouter(prefix="/tecnicas-producto", tags=["tecnicas-producto"])


@router.post(
    "", response_model=TecnicaProductoOut, status_code=status.HTTP_201_CREATED
)
def vincular(payload: TecnicaProductoCreate, db: Session = Depends(get_db)):
    return TecnicaProductoService(db).vincular(**payload.model_dump())


@router.get("", response_model=list[TecnicaProductoOut])
def listar(
    producto_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return TecnicaProductoService(db).listar_por_producto(producto_id)


@router.delete("/{vinculo_id}", status_code=status.HTTP_204_NO_CONTENT)
def desvincular(vinculo_id: int, db: Session = Depends(get_db)):
    TecnicaProductoService(db).desvincular(vinculo_id)
