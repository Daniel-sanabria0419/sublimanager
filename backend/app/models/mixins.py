"""Helpers de columna reutilizables (SQLAlchemy 2.0 / PostgreSQL)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Identity, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

# Tipos Numeric de negocio (Stage 0)
DINERO = Numeric(14, 2)
CANTIDAD = Numeric(14, 4)
PORCENTAJE = Numeric(5, 2)


def col_id() -> Mapped[int]:
    """PK BIGINT Identity."""
    return mapped_column(BigInteger, Identity(), primary_key=True)


def col_activo(*, default: bool = True) -> Mapped[bool]:
    return mapped_column(
        Boolean,
        nullable=False,
        default=default,
        server_default="true",
    )


def col_creado_en() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


def col_actualizado_en() -> Mapped[datetime]:
    return mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
