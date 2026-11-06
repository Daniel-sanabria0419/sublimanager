"""Módulo B — Productos."""

from app.models.productos.categorias_producto import CategoriaProducto
from app.models.productos.productos import Producto
from app.models.productos.tecnicas_produccion import TecnicaProduccion
from app.models.productos.tecnicas_producto import TecnicaProducto
from app.models.productos.variantes_producto import VarianteProducto

__all__ = [
    "CategoriaProducto",
    "Producto",
    "TecnicaProduccion",
    "TecnicaProducto",
    "VarianteProducto",
]
