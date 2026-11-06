"""Dependencias FastAPI compartidas."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import get_db

# Re-export para routers
obtener_db = get_db


def sesion_db() -> Generator[Session, None, None]:
    yield from get_db()
