"""Modelos SQLAlchemy — stubs en Stage 1.

Stage 2 mapeará las 36 tablas en español (`materiales`, `pedidos`,
`ordenes_produccion`, `bodegas`, `existencias`, …). Ver docs/nomenclatura.md.
"""

from app.core.database import Base

__all__ = ["Base"]
