"""Migración inicial vacía (Stage 1).

Revision ID: 20261106_0001
Revises:
Create Date: 2026-11-06

Las 36 tablas de negocio (nombres en español: materiales, pedidos,
ordenes_produccion, bodegas, existencias, …) se añaden en Stage 2
en 10 lotes Alembic. Esta revisión solo inicializa el historial
sobre una BD vacía. Ver docs/nomenclatura.md.
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "20261106_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Stage 1: sin tablas de negocio."""
    pass


def downgrade() -> None:
    """Stage 1: nada que revertir."""
    pass
