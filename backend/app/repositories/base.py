"""Repositorio base genérico (CRUD mínimo)."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import RecursoNoEncontradoError

ModelT = TypeVar("ModelT", bound=Base)


class RepositorioBase(Generic[ModelT]):
    """CRUD genérico sobre un modelo SQLAlchemy."""

    def __init__(self, db: Session, modelo: type[ModelT]) -> None:
        self.db = db
        self.modelo = modelo

    def obtener(self, id_: int) -> ModelT | None:
        return self.db.get(self.modelo, id_)

    def obtener_o_404(self, id_: int, nombre: str | None = None) -> ModelT:
        obj = self.obtener(id_)
        if obj is None:
            etiqueta = nombre or self.modelo.__tablename__
            raise RecursoNoEncontradoError(f"{etiqueta} id={id_} no encontrado")
        return obj

    def listar(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
        filtros: dict[str, Any] | None = None,
    ) -> list[ModelT]:
        stmt = select(self.modelo)
        if filtros:
            for campo, valor in filtros.items():
                if valor is None:
                    continue
                columna = getattr(self.modelo, campo, None)
                if columna is not None:
                    stmt = stmt.where(columna == valor)
        stmt = stmt.offset(offset).limit(limit).order_by(self.modelo.id)  # type: ignore[attr-defined]
        return list(self.db.scalars(stmt).all())

    def agregar(self, entidad: ModelT) -> ModelT:
        self.db.add(entidad)
        self.db.flush()
        self.db.refresh(entidad)
        return entidad

    def eliminar(self, entidad: ModelT) -> None:
        self.db.delete(entidad)
        self.db.flush()
