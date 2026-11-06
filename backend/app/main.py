"""Punto de entrada FastAPI de SubliManager."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.exceptions import registrar_manejadores
from app.core.logging_config import configurar_logging, get_logger


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configurar_logging()
    logger = get_logger(__name__)
    settings = get_settings()
    logger.info(
        "Iniciando %s v%s (entorno=%s)",
        settings.app_name,
        __version__,
        settings.app_env,
    )
    yield
    logger.info("Deteniendo %s", settings.app_name)


def create_app() -> FastAPI:
    """Fábrica de la aplicación (útil para tests)."""
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "API REST de SubliManager V1 — ERP de sublimación "
            "(backend desacoplado del cliente desktop)."
        ),
        lifespan=lifespan,
    )
    registrar_manejadores(app)
    app.include_router(api_router)
    return app


app = create_app()
