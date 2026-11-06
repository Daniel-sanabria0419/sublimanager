"""Repositorios de persistencia."""

from app.repositories.compras import CompraRepo, ItemCompraRepo, ProveedorRepo
from app.repositories.inventario import (
    BodegaRepo,
    CategoriaMaterialRepo,
    ExistenciaRepo,
    ItemMovimientoRepo,
    MaterialRepo,
    MovimientoInventarioRepo,
    UnidadMedidaRepo,
)

__all__ = [
    "BodegaRepo",
    "CategoriaMaterialRepo",
    "CompraRepo",
    "ExistenciaRepo",
    "ItemCompraRepo",
    "ItemMovimientoRepo",
    "MaterialRepo",
    "MovimientoInventarioRepo",
    "ProveedorRepo",
    "UnidadMedidaRepo",
]
