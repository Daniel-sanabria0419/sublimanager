"""Excepciones de dominio y manejadores HTTP centralizados."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class SubliManagerError(Exception):
    """Error base de dominio SubliManager."""

    def __init__(self, mensaje: str, codigo: str = "error_dominio") -> None:
        self.mensaje = mensaje
        self.codigo = codigo
        super().__init__(mensaje)


class RecursoNoEncontradoError(SubliManagerError):
    """El recurso solicitado no existe."""

    def __init__(self, mensaje: str = "Recurso no encontrado") -> None:
        super().__init__(mensaje, codigo="no_encontrado")


class ConflictoNegocioError(SubliManagerError):
    """Violación de regla de negocio o estado inválido."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="conflicto_negocio")


class ValidacionError(SubliManagerError):
    """Datos de entrada inválidos a nivel de dominio."""

    def __init__(self, mensaje: str) -> None:
        super().__init__(mensaje, codigo="validacion")


def registrar_manejadores(app: FastAPI) -> None:
    """Registra manejadores de excepción globales en la app FastAPI."""

    @app.exception_handler(RecursoNoEncontradoError)
    async def manejar_no_encontrado(
        _request: Request, exc: RecursoNoEncontradoError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_404_NOT_FOUND,
            content={"detalle": exc.mensaje, "codigo": exc.codigo},
        )

    @app.exception_handler(ConflictoNegocioError)
    async def manejar_conflicto(
        _request: Request, exc: ConflictoNegocioError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_409_CONFLICT,
            content={"detalle": exc.mensaje, "codigo": exc.codigo},
        )

    @app.exception_handler(ValidacionError)
    async def manejar_validacion(
        _request: Request, exc: ValidacionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"detalle": exc.mensaje, "codigo": exc.codigo},
        )

    @app.exception_handler(SubliManagerError)
    async def manejar_dominio(
        _request: Request, exc: SubliManagerError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={"detalle": exc.mensaje, "codigo": exc.codigo},
        )

    @app.exception_handler(Exception)
    async def manejar_inesperado(
        _request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception("Error no controlado: %s", exc)
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detalle": "Error interno del servidor",
                "codigo": "error_interno",
            },
        )
