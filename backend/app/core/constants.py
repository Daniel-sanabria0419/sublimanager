"""Constantes compartidas del backend (Stage 1 — mínimas).

Nomenclatura de negocio (tablas, columnas, enums, paths) en español según
docs/nomenclatura.md. Los enums UPPER_SNAKE y los modelos de las 36 tablas
se materializan en Stage 2 — aquí solo se documentan prefijos y precisiones.
"""

API_V1_PREFIX = "/api/v1"
HEALTH_PATH = "/health"
HEALTH_DB_PATH = "/health/db"

# Prefijos de recursos previstos (Stage 2+). Paths en kebab-case español.
# No hay routers de negocio en Stage 1.
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

# Recordatorio V1 (Stage 2): ordenes_produccion.pedido_id es NOT NULL.
PEDIDO_ID_REQUERIDO_EN_OP = True
