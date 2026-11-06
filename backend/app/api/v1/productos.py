"""CRUD `/api/v1/productos` + costo estimado."""

from decimal import Decimal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.productos import ProductoCreate, ProductoOut, ProductoUpdate
from app.schemas.recetas import CostoEstimadoOut
from app.services.costos import ProductoCostoService
from app.services.productos import ProductoService
from app.utils.decimal_policy import a_decimal, money_round

router = APIRouter(prefix="/productos", tags=["productos"])


@router.post("", response_model=ProductoOut, status_code=status.HTTP_201_CREATED)
def crear(payload: ProductoCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    data["tipo_producto"] = payload.tipo_producto.value
    return ProductoService(db).crear(**data)


@router.get("", response_model=list[ProductoOut])
def listar(
    activo: bool | None = None,
    tipo_producto: str | None = None,
    categoria_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return ProductoService(db).listar(
        activo=activo,
        tipo_producto=tipo_producto,
        categoria_id=categoria_id,
        offset=offset,
        limit=limit,
    )


@router.get("/{producto_id}", response_model=ProductoOut)
def obtener(producto_id: int, db: Session = Depends(get_db)):
    return ProductoService(db).obtener(producto_id)


@router.patch("/{producto_id}", response_model=ProductoOut)
def actualizar(
    producto_id: int, payload: ProductoUpdate, db: Session = Depends(get_db)
):
    data = payload.model_dump(exclude_unset=True)
    if "tipo_producto" in data and data["tipo_producto"] is not None:
        data["tipo_producto"] = payload.tipo_producto.value  # type: ignore[union-attr]
    return ProductoService(db).actualizar(producto_id, **data)


@router.get("/{producto_id}/costo-estimado", response_model=CostoEstimadoOut)
def costo_estimado(
    producto_id: int,
    variante_id: int | None = None,
    costo_adquisicion: Decimal | None = None,
    db: Session = Depends(get_db),
):
    adquisicion = (
        money_round(a_decimal(costo_adquisicion))
        if costo_adquisicion is not None
        else None
    )
    return ProductoCostoService(db).estimar(
        producto_id=producto_id,
        variante_id=variante_id,
        costo_adquisicion=adquisicion,
    )
