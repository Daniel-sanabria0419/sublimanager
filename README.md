# SubliManager

ERP de sublimación (V1): backend FastAPI + PostgreSQL y cliente desktop CustomTkinter desacoplados por REST.

**Etapa actual:** Stage 1 — Configuración del proyecto (bootstrap). Sin tablas de negocio ni lógica de inventario/productos/pedidos.

## Stack

- Python 3.12+
- FastAPI · Uvicorn · Pydantic 2 · SQLAlchemy 2.0 · Alembic · Psycopg 3
- PostgreSQL 16+
- Pytest · HTTPX
- Desktop (stub): CustomTkinter en Stage 8

## Estructura

```
sublimanager/          ← raíz del repositorio
├── backend/           # API FastAPI
├── desktop/           # Stub del cliente (Stage 8)
├── docs/              # Guías en español
├── scripts/           # Helpers de arranque / migraciones / tests
├── docker-compose.yml # PostgreSQL local
├── .env.example
└── README.md
```

## Arranque rápido

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env
docker compose up -d          # PostgreSQL
./scripts/run_migrations.sh   # Alembic (migración vacía Stage 1)
./scripts/run_api.sh          # http://localhost:8000
```

- Salud: [http://localhost:8000/health](http://localhost:8000/health)
- Salud BD: [http://localhost:8000/health/db](http://localhost:8000/health/db)
- OpenAPI: [http://localhost:8000/docs](http://localhost:8000/docs)

Guía detallada: [`docs/instalacion.md`](docs/instalacion.md).

## Tests

```bash
./scripts/run_tests.sh
# Con BD de prueba:
TEST_DATABASE_URL=postgresql+psycopg://sublimanager:sublimanager@localhost:5432/sublimanager \
  ./scripts/run_tests.sh
```

## Convenciones

- Identificadores de producto/schema/UI/API en **español** (`pedidos`, `bodegas`,
  `ordenes_produccion`, …). Ver [`docs/nomenclatura.md`](docs/nomenclatura.md).
- Nombres de stack tecnológico en inglés.
- Sin secretos en el código; solo `.env.example` en el repo.
- Stage 1 no crea las 36 tablas; eso es Stage 2.

## Licencia / autor

Proyecto privado — Sublisoft / Daniel Sanabria.
