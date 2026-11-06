"""Configuración centralizada de logging."""

import logging
import sys

from app.core.config import get_settings


def configurar_logging() -> None:
    """Inicializa el logging raíz según LOG_LEVEL de settings."""
    settings = get_settings()
    nivel = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=nivel,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


def get_logger(nombre: str) -> logging.Logger:
    """Obtiene un logger nombrado (tras configurar_logging)."""
    return logging.getLogger(nombre)
