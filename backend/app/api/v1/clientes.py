"""CRUD `/api/v1/clientes`."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import MensajeOut
from app.schemas.pedidos import ClienteCreate, ClienteOut, ClienteUpdate
from app.services.clientes import ClienteService

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
def crear(payload: ClienteCreate, db: Session = Depends(get_db)):
    return ClienteService(db).crear(**payload.model_dump())


@router.get("", response_model=list[ClienteOut])
def listar(
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return ClienteService(db).listar(activo=activo, offset=offset, limit=limit)


@router.get("/{cliente_id}", response_model=ClienteOut)
def obtener(cliente_id: int, db: Session = Depends(get_db)):
    return ClienteService(db).obtener(cliente_id)


@router.patch("/{cliente_id}", response_model=ClienteOut)
def actualizar(
    cliente_id: int, payload: ClienteUpdate, db: Session = Depends(get_db)
):
    return ClienteService(db).actualizar(
        cliente_id, **payload.model_dump(exclude_unset=True)
    )


@router.delete("/{cliente_id}", response_model=MensajeOut)
def eliminar(cliente_id: int, db: Session = Depends(get_db)):
    ClienteService(db).eliminar(cliente_id)
    return MensajeOut(detalle="Cliente desactivado")
