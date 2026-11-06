# Arquitectura — resumen (Stage 3)

Documento espejo condensado de la arquitectura V1. Nomenclatura de schema/API:
[`nomenclatura.md`](nomenclatura.md). Schema: [`database.md`](database.md).

## Capas

| Capa | Tecnología | Rol |
|------|------------|-----|
| Desktop | CustomTkinter + HTTPX | UI (Stage 8); stub en Stage 1 |
| API | FastAPI / Uvicorn | Único canal REST (`/api/v1/…` en español) |
| Dominio | Services Python | Reglas de negocio (Stage 3: inventario/compras) |
| Persistencia | SQLAlchemy 2.0 + Alembic + PostgreSQL (Psycopg 3) | Datos y migraciones |

## Invariantes

1. El desktop **nunca** abre conexiones a PostgreSQL ni importa SQLAlchemy.
2. Secretos solo por variables de entorno (`.env`); el repo solo incluye `.env.example`.
3. Sin SQLite como BD principal.
4. Identificadores de negocio (tablas, columnas, estados, UI, paths) en **español**.
5. `ordenes_produccion.pedido_id` es **NOT NULL** en V1.
6. Inventario solo cambia vía `movimientos_inventario` (+ `existencias`); Decimal ROUND_HALF_UP.

## Layout del backend (`backend/app/`)

- `core/` — config, database, exceptions, constants, logging
- `models/` — 36 tablas SQLAlchemy 2.0 (paquetes A–G) + enums español
- `schemas/` — DTOs Pydantic (inventario, compras)
- `repositories/` — persistencia sin orquestar multi-agregado
- `services/` — autoridad de reglas §5.1–5.2
- `api/v1/` — routers REST en español
- `utils/decimal_policy.py` — `money_round` / `qty_round` / promedio ponderado

## Endpoints

### Salud (Stage 1)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Proceso vivo |
| GET | `/health/db` | Ping PostgreSQL |

### Inventario y compras (Stage 3)

| Método | Ruta | Descripción |
|--------|------|-------------|
| CRUD | `/api/v1/categorias-material` | Categorías de material |
| CRUD | `/api/v1/unidades-medida` | Unidades de medida |
| CRUD | `/api/v1/bodegas` | Bodegas |
| CRUD | `/api/v1/materiales` | Materiales (+ stock apertura vía AJUSTE) |
| GET | `/api/v1/materiales/alertas-stock-bajo` | Stock &lt; mínimo |
| GET | `/api/v1/existencias` | Consulta de existencias |
| POST/GET | `/api/v1/movimientos-inventario` | Movimientos (entrada/salida/ajuste) |
| POST | `/api/v1/movimientos-inventario/transferencias` | Par SALIDA/ENTRADA |
| POST | `/api/v1/movimientos-inventario/{id}/confirmar` | Confirma BORRADOR |
| CRUD | `/api/v1/proveedores` | Proveedores |
| POST/GET | `/api/v1/compras` | Compras en BORRADOR |
| POST | `/api/v1/compras/{id}/recibir` | Recepción → stock + promedio |
| POST | `/api/v1/compras/{id}/cancelar` | Solo BORRADOR |
