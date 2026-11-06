"""API `/api/v1/recetas-producto` — versiones históricas de receta."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.recetas import RecetaProductoCreate, RecetaProductoOut
from app.services.recetas import ItemRecetaDatos, RecetaProductoService

router = APIRouter(prefix="/recetas-producto", tags=["recetas-producto"])


@router.post(
    "", response_model=RecetaProductoOut, status_code=status.HTTP_201_CREATED
)
def crear(payload: RecetaProductoCreate, db: Session = Depends(get_db)):
    items = [
        ItemRecetaDatos(
            material_id=i.material_id,
            cantidad=i.cantidad,
            porcentaje_desperdicio=i.porcentaje_desperdicio,
            notas=i.notas,
        )
        for i in payload.items
    ]
    return RecetaProductoService(db).crear(
        producto_id=payload.producto_id,
        variante_id=payload.variante_id,
        nombre=payload.nombre,
        activo=payload.activo,
        items=items,
    )


@router.get("", response_model=list[RecetaProductoOut])
def listar(
    producto_id: int = Query(...),
    variante_id: int | None = None,
    solo_variante_exacta: bool = False,
    activo: bool | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return RecetaProductoService(db).listar(
        producto_id=producto_id,
        variante_id=variante_id,
        solo_variante_exacta=solo_variante_exacta,
        activo=activo,
        offset=offset,
        limit=limit,
    )


@router.get("/{receta_id}", response_model=RecetaProductoOut)
def obtener(receta_id: int, db: Session = Depends(get_db)):
    return RecetaProductoService(db).obtener(receta_id)


@router.post("/{receta_id}/activar", response_model=RecetaProductoOut)
def activar(receta_id: int, db: Session = Depends(get_db)):
    return RecetaProductoService(db).activar(receta_id)
