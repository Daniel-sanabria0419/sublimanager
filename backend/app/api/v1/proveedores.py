"""CRUD `/api/v1/proveedores`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.compras import ProveedorCreate, ProveedorOut, ProveedorUpdate
from app.services.compras import ProveedorService

router = APIRouter(prefix="/proveedores", tags=["proveedores"])


@router.post("", response_model=ProveedorOut, status_code=status.HTTP_201_CREATED)
def crear(payload: ProveedorCreate, db: Session = Depends(get_db)):
    return ProveedorService(db).crear(**payload.model_dump())


@router.get("", response_model=list[ProveedorOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return ProveedorService(db).listar(activo=activo, offset=offset, limit=limit)


@router.get("/{proveedor_id}", response_model=ProveedorOut)
def obtener(proveedor_id: int, db: Session = Depends(get_db)):
    return ProveedorService(db).obtener(proveedor_id)


@router.patch("/{proveedor_id}", response_model=ProveedorOut)
def actualizar(
    proveedor_id: int, payload: ProveedorUpdate, db: Session = Depends(get_db)
):
    return ProveedorService(db).actualizar(
        proveedor_id, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{proveedor_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(proveedor_id: int, db: Session = Depends(get_db)):
    ProveedorService(db).eliminar(proveedor_id)
