"""Endpoints de salud de la aplicación y de la base de datos."""

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db, verificar_conexion
from app.core.logging_config import get_logger

router = APIRouter(tags=["salud"])
logger = get_logger(__name__)


@router.get("/health", summary="Salud de la aplicación")
def salud() -> dict[str, str]:
    """Indica que el proceso API está vivo (sin consultar la BD)."""
    settings = get_settings()
    return {
        "estado": "ok",
        "aplicacion": settings.app_name,
        "entorno": settings.app_env,
    }


@router.get("/health/db", summary="Salud de la conexión a PostgreSQL")
def salud_db(db: Session = Depends(get_db)) -> JSONResponse:
    """Verifica conectividad con PostgreSQL mediante `SELECT 1`."""
    try:
        verificar_conexion(db)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"estado": "ok", "base_datos": "conectada"},
        )
    except Exception as exc:  # noqa: BLE001 — reportamos fallo de conectividad
        logger.warning("Fallo en health/db: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "estado": "error",
                "base_datos": "no_disponible",
                "detalle": str(exc),
            },
        )
