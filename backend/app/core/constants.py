"""Constantes compartidas del backend.

Nomenclatura de negocio (tablas, columnas, enums, paths) en español según
docs/nomenclatura.md. Enums de dominio: `app.models.enums`.
"""

API_V1_PREFIX = "/api/v1"
HEALTH_PATH = "/health"
HEALTH_DB_PATH = "/health/db"

# Prefijos de recursos previstos (routers de negocio en Stages 3–7).
RUTAS_RECURSOS_V1 = {
    "materiales": f"{API_V1_PREFIX}/materiales",
    "bodegas": f"{API_V1_PREFIX}/bodegas",
    "existencias": f"{API_V1_PREFIX}/existencias",
    "movimientos_inventario": f"{API_V1_PREFIX}/movimientos-inventario",
    "productos": f"{API_V1_PREFIX}/productos",
    "clientes": f"{API_V1_PREFIX}/clientes",
    "pedidos": f"{API_V1_PREFIX}/pedidos",
    "ordenes_produccion": f"{API_V1_PREFIX}/ordenes-produccion",
    "proveedores": f"{API_V1_PREFIX}/proveedores",
    "compras": f"{API_V1_PREFIX}/compras",
    "cuentas_caja": f"{API_V1_PREFIX}/cuentas-caja",
    "pagos": f"{API_V1_PREFIX}/pagos",
}

# Precisión Decimal de negocio (Stage 0; helpers money_round/qty_round en Stage 3+)
DINERO_DECIMALES = 2
CANTIDAD_DECIMALES = 4
PORCENTAJE_DECIMALES = 2

# V1: ordenes_produccion.pedido_id es NOT NULL.
PEDIDO_ID_REQUERIDO_EN_OP = True

# Revisiones Alembic Stage 2
ALEMBIC_REVISION_SCHEMA_V1 = "20261106_0002"
CANTIDAD_TABLAS_NEGOCIO = 36
