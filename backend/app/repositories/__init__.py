"""Repositorios de persistencia."""

from app.repositories.compras import CompraRepo, ItemCompraRepo, ProveedorRepo
from app.repositories.finanzas import (
    CuentaCajaRepo,
    MetodoPagoRepo,
    MovimientoCajaRepo,
    PagoRepo,
)
from app.repositories.inventario import (
    BodegaRepo,
    CategoriaMaterialRepo,
    ExistenciaRepo,
    ItemMovimientoRepo,
    MaterialRepo,
    MovimientoInventarioRepo,
    UnidadMedidaRepo,
)
from app.repositories.pedidos import (
    ClienteRepo,
    DisenoPedidoRepo,
    HistorialEstadoPedidoRepo,
    ItemPedidoRepo,
    PedidoRepo,
)
from app.repositories.produccion import (
    AsientoCostoProduccionRepo,
    ConsumoProduccionRepo,
    ItemOrdenProduccionRepo,
    OrdenProduccionRepo,
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
    "AsientoCostoProduccionRepo",
    "BodegaRepo",
    "CategoriaCostoRepo",
    "CategoriaMaterialRepo",
    "CategoriaProductoRepo",
    "ClienteRepo",
    "CompraRepo",
    "ConsumoProduccionRepo",
    "CuentaCajaRepo",
    "DisenoPedidoRepo",
    "ExistenciaRepo",
    "HistorialEstadoPedidoRepo",
    "ItemCompraRepo",
    "ItemMovimientoRepo",
    "ItemOrdenProduccionRepo",
    "ItemPedidoRepo",
    "ItemRecetaRepo",
    "MaterialRepo",
    "MetodoPagoRepo",
    "MovimientoCajaRepo",
    "MovimientoInventarioRepo",
    "OrdenProduccionRepo",
    "PagoRepo",
    "PedidoRepo",
    "PerfilCostoProductoRepo",
    "ProductoRepo",
    "ProveedorRepo",
    "RecetaProductoRepo",
    "TecnicaProduccionRepo",
    "TecnicaProductoRepo",
    "UnidadMedidaRepo",
    "VarianteProductoRepo",
]
