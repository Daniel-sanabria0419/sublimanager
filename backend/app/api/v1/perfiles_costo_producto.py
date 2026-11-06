"""API `/api/v1/perfiles-costo-producto` — perfiles históricos (no sobrescribe)."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recetas import PerfilCostoProductoCreate, PerfilCostoProductoOut
from app.services.recetas import PerfilCostoProductoService

router = APIRouter(
    prefix="/perfiles-costo-producto", tags=["perfiles-costo-producto"]
)


@router.post(
    "",
    response_model=PerfilCostoProductoOut,
    status_code=status.HTTP_201_CREATED,
)
def crear(payload: PerfilCostoProductoCreate, db: Session = Depends(get_db)):
    return PerfilCostoProductoService(db).crear(**payload.model_dump())


@router.get("", response_model=list[PerfilCostoProductoOut])
def listar(
    producto_id: int = Query(...),
    variante_id: int | None = None,
    solo_variante_exacta: bool = False,
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return PerfilCostoProductoService(db).listar(
        producto_id=producto_id,
        variante_id=variante_id,
        solo_variante_exacta=solo_variante_exacta,
        activo=activo,
        offset=offset,
        limit=limit,
    )


@router.get("/{perfil_id}", response_model=PerfilCostoProductoOut)
def obtener(perfil_id: int, db: Session = Depends(get_db)):
    return PerfilCostoProductoService(db).obtener(perfil_id)


@router.post("/{perfil_id}/activar", response_model=PerfilCostoProductoOut)
def activar(perfil_id: int, db: Session = Depends(get_db)):
    return PerfilCostoProductoService(db).activar(perfil_id)
