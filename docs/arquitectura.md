# Arquitectura — resumen Stage 1

Documento espejo condensado de la arquitectura V1. La fuente completa vive en el
Project store (`docs/architecture.md`). Nomenclatura de schema/API: ver
[`nomenclatura.md`](nomenclatura.md).

## Capas

| Capa | Tecnología | Rol |
|------|------------|-----|
| Desktop | CustomTkinter + HTTPX | UI (Stage 8); stub en Stage 1 |
| API | FastAPI / Uvicorn | Único canal REST (`/api/v1/…` en español) |
| Dominio | Services Python | Reglas de negocio (Stage 3+) |
| Persistencia | SQLAlchemy 2.0 + Alembic + PostgreSQL (Psycopg 3) | Datos y migraciones |

## Invariantes

1. El desktop **nunca** abre conexiones a PostgreSQL ni importa SQLAlchemy.
2. Secretos solo por variables de entorno (`.env`); el repo solo incluye `.env.example`.
3. Sin SQLite como BD principal.
4. Identificadores de negocio (tablas, columnas, estados, UI, paths) en **español**
   (`pedidos`, `ordenes_produccion`, `bodegas`, `existencias`, …). Stack en inglés.
5. `ordenes_produccion.pedido_id` será **NOT NULL** en V1 (cuando exista en Stage 2).

## Layout del backend (`backend/app/`)

- `core/` — config, database, exceptions, constants, logging
- `models/` — stubs Stage 1; modelos SQLAlchemy de las 36 tablas en Stage 2
- `schemas/` / `repositories/` / `services/` — stubs Stage 1
- `api/v1/` — routers (hoy: salud; luego `/pedidos`, `/ordenes-produccion`, …)
- `utils/` — helpers puros

## Endpoints Stage 1

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Proceso vivo |
| GET | `/health/db` | Ping `SELECT 1` a PostgreSQL |

Los recursos de negocio (`/api/v1/materiales`, `/api/v1/pedidos`, etc.) llegan con
los services de las etapas 3–7; Stage 1 solo deja el cableado listo.
