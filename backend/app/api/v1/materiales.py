"""CRUD `/api/v1/materiales` + alertas de stock bajo."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.inventario import (
    AlertaStockBajoOut,
    MaterialCreate,
    MaterialOut,
    MaterialUpdate,
)
from app.services.inventario import MaterialService

router = APIRouter(prefix="/materiales", tags=["materiales"])


@router.post("", response_model=MaterialOut, status_code=status.HTTP_201_CREATED)
def crear(payload: MaterialCreate, db: Session = Depends(get_db)):
    return MaterialService(db).crear(**payload.model_dump())


@router.get("", response_model=list[MaterialOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return MaterialService(db).listar(activo=activo, offset=offset, limit=limit)


@router.get("/alertas-stock-bajo", response_model=list[AlertaStockBajoOut])
def alertas_stock_bajo(db: Session = Depends(get_db)):
    return MaterialService(db).alertas_stock_bajo()


@router.get("/{material_id}", response_model=MaterialOut)
def obtener(material_id: int, db: Session = Depends(get_db)):
    return MaterialService(db).obtener(material_id)


@router.patch("/{material_id}", response_model=MaterialOut)
def actualizar(
    material_id: int, payload: MaterialUpdate, db: Session = Depends(get_db)
):
    return MaterialService(db).actualizar(
        material_id, **payload.model_dump(exclude_unset=True)
    )
