"""Motor SQLAlchemy 2.0 y fábrica de sesiones para PostgreSQL."""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base declarativa para modelos SQLAlchemy.

    Las 36 tablas en español se registran al importar `app.models`.
    """


def _crear_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.sqlalchemy_database_url,
        pool_pre_ping=True,
        future=True,
    )


engine: Engine = _crear_engine()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """Dependencia FastAPI: entrega una sesión y la cierra al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def verificar_conexion(db: Session | None = None) -> bool:
    """Ejecuta `SELECT 1` para comprobar conectividad con PostgreSQL."""
    if db is not None:
        db.execute(text("SELECT 1"))
        return True
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
