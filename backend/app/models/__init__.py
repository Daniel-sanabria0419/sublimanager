"""Modelos SQLAlchemy 2.0 — 36 tablas en español (Stage 2).

Paquetes por módulo de negocio (A–G). Importar este paquete registra
todas las tablas en `Base.metadata` (Alembic / tests).
"""

from app.core.database import Base

# Enums de dominio
from app.models import enums as enums  # noqa: F401

# Módulo A — Inventario
from app.models.inventario import (
    Bodega,
    CategoriaMaterial,
    Existencia,
    ItemMovimientoInventario,
    Material,
    MovimientoInventario,
    UnidadMedida,
)

# Módulo B — Productos
from app.models.productos import (
    CategoriaProducto,
    Producto,
    TecnicaProduccion,
    TecnicaProducto,
    VarianteProducto,
)

# Módulo C — Recetas / costos
from app.models.recetas import (
    CategoriaCosto,
    ItemRecetaProducto,
    PerfilCostoProducto,
    RecetaProducto,
)

# Módulo D — Clientes / pedidos
from app.models.pedidos import (
    Cliente,
    DisenoPedido,
    HistorialEstadoPedido,
    ItemPedido,
    Pedido,
)

# Módulo E — Producción
from app.models.produccion import (
    AsientoCostoProduccion,
    ConsumoProduccion,
    ItemOrdenProduccion,
    OrdenProduccion,
)

# Módulo F — Compras
from app.models.compras import (
    Compra,
    ItemCompra,
    Proveedor,
)

# Módulo G — Finanzas
from app.models.finanzas import (
    CategoriaGasto,
    CuentaCaja,
    Gasto,
    MetodoPago,
    MovimientoCaja,
    Pago,
    PagoGasto,
    PagoProveedor,
)

__all__ = [
    "Base",
    # A
    "CategoriaMaterial",
    "UnidadMedida",
    "Material",
    "Bodega",
    "Existencia",
    "MovimientoInventario",
    "ItemMovimientoInventario",
    # B
    "CategoriaProducto",
    "Producto",
    "VarianteProducto",
    "TecnicaProduccion",
    "TecnicaProducto",
    # C
    "RecetaProducto",
    "ItemRecetaProducto",
    "PerfilCostoProducto",
    "CategoriaCosto",
    # D
    "Cliente",
    "Pedido",
    "ItemPedido",
    "DisenoPedido",
    "HistorialEstadoPedido",
    # E
    "OrdenProduccion",
    "ItemOrdenProduccion",
    "ConsumoProduccion",
    "AsientoCostoProduccion",
    # F
    "Proveedor",
    "Compra",
    "ItemCompra",
    # G
    "MetodoPago",
    "CuentaCaja",
    "Pago",
    "CategoriaGasto",
    "Gasto",
    "PagoGasto",
    "PagoProveedor",
    "MovimientoCaja",
]

# Verificación de conteo (36 tablas de negocio)
TABLAS_NEGOCIO = [
    name
    for name in Base.metadata.tables
    if not name.startswith("alembic_")
]
assert len(TABLAS_NEGOCIO) == 36, (
    f"Se esperaban 36 tablas de negocio, hay {len(TABLAS_NEGOCIO)}: "
    f"{sorted(TABLAS_NEGOCIO)}"
)
