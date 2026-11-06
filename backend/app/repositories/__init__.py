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
from app.repositories.productos import (
    CategoriaProductoRepo,
    ProductoRepo,
    TecnicaProduccionRepo,
    TecnicaProductoRepo,
    VarianteProductoRepo,
)
from app.repositories.recetas import (
    CategoriaCostoRepo,
    ItemRecetaRepo,
    PerfilCostoProductoRepo,
    RecetaProductoRepo,
)

__all__ = [
    "BodegaRepo",
    "CategoriaCostoRepo",
    "CategoriaMaterialRepo",
    "CategoriaProductoRepo",
    "CompraRepo",
    "ExistenciaRepo",
    "ItemCompraRepo",
    "ItemMovimientoRepo",
    "ItemRecetaRepo",
    "MaterialRepo",
    "MovimientoInventarioRepo",
    "PerfilCostoProductoRepo",
    "ProductoRepo",
    "ProveedorRepo",
    "RecetaProductoRepo",
    "TecnicaProduccionRepo",
    "TecnicaProductoRepo",
    "UnidadMedidaRepo",
    "VarianteProductoRepo",
]
