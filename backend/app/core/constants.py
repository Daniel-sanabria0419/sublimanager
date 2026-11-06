"""Constantes compartidas del backend (Stage 1 — mínimas).

Los enums de estado de negocio (español UPPER_SNAKE) se definen en Stage 2
junto con los modelos. Ver docs/nomenclatura-es.md en el Project store.
"""

API_V1_PREFIX = "/api/v1"
HEALTH_PATH = "/health"
HEALTH_DB_PATH = "/health/db"

# Precisión Decimal de negocio (referencia Stage 0; helpers en Stage 3+)
DINERO_DECIMALES = 2
CANTIDAD_DECIMALES = 4
