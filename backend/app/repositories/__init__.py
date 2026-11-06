"""Repositorios de persistencia."""

from app.repositories.compras import CompraRepo, ItemCompraRepo, ProveedorRepo
from app.repositories.finanzas import (
    CategoriaGastoRepo,
    ConsultasFinancierasRepo,
    CuentaCajaRepo,
    GastoRepo,
    MetodoPagoRepo,
    MovimientoCajaRepo,
    PagoGastoRepo,
    PagoProveedorRepo,
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
    "CategoriaGastoRepo",
    "CategoriaMaterialRepo",
    "CategoriaProductoRepo",
    "ClienteRepo",
    "CompraRepo",
    "ConsultasFinancierasRepo",
    "ConsumoProduccionRepo",
    "CuentaCajaRepo",
    "DisenoPedidoRepo",
    "ExistenciaRepo",
    "GastoRepo",
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
    "PagoGastoRepo",
    "PagoProveedorRepo",
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
