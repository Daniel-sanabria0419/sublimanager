"""Constantes compartidas del backend.

Nomenclatura de negocio (tablas, columnas, enums, paths) en español según
docs/nomenclatura.md. Enums de dominio: `app.models.enums`.
"""

API_V1_PREFIX = "/api/v1"
HEALTH_PATH = "/health"
HEALTH_DB_PATH = "/health/db"

# Prefijos de recursos (Stage 3–5 implementados; 6–7 previstos).
RUTAS_RECURSOS_V1 = {
    "categorias_material": f"{API_V1_PREFIX}/categorias-material",
    "unidades_medida": f"{API_V1_PREFIX}/unidades-medida",
    "materiales": f"{API_V1_PREFIX}/materiales",
    "bodegas": f"{API_V1_PREFIX}/bodegas",
    "existencias": f"{API_V1_PREFIX}/existencias",
    "movimientos_inventario": f"{API_V1_PREFIX}/movimientos-inventario",
    "proveedores": f"{API_V1_PREFIX}/proveedores",
    "compras": f"{API_V1_PREFIX}/compras",
    "productos": f"{API_V1_PREFIX}/productos",
    "clientes": f"{API_V1_PREFIX}/clientes",
    "pedidos": f"{API_V1_PREFIX}/pedidos",
    "metodos_pago": f"{API_V1_PREFIX}/metodos-pago",
    "ordenes_produccion": f"{API_V1_PREFIX}/ordenes-produccion",
    "cuentas_caja": f"{API_V1_PREFIX}/cuentas-caja",
    "pagos": f"{API_V1_PREFIX}/pagos",
}

# Precisión Decimal de negocio (ROUND_HALF_UP; ver utils/decimal_policy.py)
DINERO_DECIMALES = 2
CANTIDAD_DECIMALES = 4
PORCENTAJE_DECIMALES = 2

# V1: ordenes_produccion.pedido_id es NOT NULL.
PEDIDO_ID_REQUERIDO_EN_OP = True

# Revisiones Alembic Stage 2
ALEMBIC_REVISION_SCHEMA_V1 = "20261106_0002"
CANTIDAD_TABLAS_NEGOCIO = 36
